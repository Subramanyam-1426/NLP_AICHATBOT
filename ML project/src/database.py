"""SQLite persistence, authentication, and ownership checks for the chatbot."""

from __future__ import annotations

import hashlib
import json
import secrets
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    URL,
    create_engine,
    func,
    or_,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from src.utilities import get_db_path

Base = declarative_base()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _password_material(password: str) -> bytes:
    """Pre-hash to a fixed-size value so bcrypt's 72-byte limit is not surprising."""
    return hashlib.sha256(password.encode("utf-8")).digest()


def _password_hash(password: str) -> str:
    return bcrypt.hashpw(_password_material(password), bcrypt.gensalt()).decode("ascii")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True, nullable=False, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    role = Column(String(10), nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=_now)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime)
    is_legacy = Column(Boolean, nullable=False, default=False)
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_now)
    user = relationship("User", back_populates="auth_tokens")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    # Kept for backwards compatibility with the original schema; new chats are user-owned.
    session_id = Column(String(100), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), default="New Chat", nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, nullable=False, index=True)
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    sender = Column(String(20))
    message_text = Column(Text)
    sentiment = Column(String(20), default="Neutral")
    compound_score = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=_now, index=True)
    intent = Column(String(100))
    confidence = Column(Float)
    top_predictions = Column(Text, nullable=False, default="[]")
    resolved_query = Column(Text)
    is_fallback = Column(Boolean, default=False, nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
    intent_logs = relationship("IntentPredictionLog", backref="message", cascade="all, delete-orphan")
    feedback_logs = relationship("FeedbackLog", backref="message", cascade="all, delete-orphan")


class IntentPredictionLog(Base):
    __tablename__ = "intent_predictions"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    predicted_intent = Column(String(100))
    confidence = Column(Float)
    is_fallback = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=_now)


class FeedbackLog(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    rating = Column(Integer)
    comment = Column(Text, default="")
    timestamp = Column(DateTime, default=_now)


class UnknownQueryLog(Base):
    __tablename__ = "unknown_queries"
    id = Column(Integer, primary_key=True)
    user_text = Column(Text)
    confidence = Column(Float)
    reviewed = Column(Boolean, default=False)
    mapped_intent = Column(String(100), default="")
    timestamp = Column(DateTime, default=_now)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)


class DatabaseManager:
    """SQLAlchemy storage with an idempotent, backup-first SQLite migration."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = str(db_path or get_db_path())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            URL.create("sqlite", database=self.db_path),
            connect_args={"check_same_thread": False, "timeout": 30},
        )
        self._migrate_existing_database()
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def _snapshot_before_migration(self) -> None:
        db_file = Path(self.db_path)
        if not db_file.exists() or db_file.stat().st_size == 0:
            return
        backup = db_file.with_name(f"{db_file.stem}.pre_auth_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
        suffix = 1
        while backup.exists():
            backup = db_file.with_name(
                f"{db_file.stem}.pre_auth_backup_{datetime.now():%Y%m%d_%H%M%S}_{suffix}.db"
            )
            suffix += 1
        source = sqlite3.connect(f"file:{db_file.as_posix()}?mode=ro", uri=True, timeout=30)
        destination = sqlite3.connect(str(backup), timeout=30)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

    def _migrate_existing_database(self) -> None:
        """Add auth/history metadata without rebuilding or dropping legacy tables."""
        with self.engine.begin() as conn:
            tables = set(conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).scalars())
            if not tables:
                return
            columns = {}
            for table in ("conversations", "messages", "unknown_queries"):
                if table in tables:
                    columns[table] = {
                        row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").all()
                    }
            required = {
                "conversations": {"user_id", "updated_at", "is_pinned", "is_deleted"},
                "messages": {"intent", "confidence", "top_predictions", "resolved_query", "is_fallback"},
                "unknown_queries": {"user_id", "conversation_id"},
            }
            needs_migration = (
                not {"users", "auth_tokens"}.issubset(tables)
                or any(not required[t].issubset(columns.get(t, set())) for t in required if t in tables)
            )
        if not needs_migration:
            return

        # SQLite's backup API includes committed data even while Streamlit has the DB open.
        self._snapshot_before_migration()
        with self.engine.begin() as conn:
            conn.exec_driver_sql(
                """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, username VARCHAR(30) NOT NULL UNIQUE,
                    email VARCHAR(254) NOT NULL UNIQUE, password_hash VARCHAR(100) NOT NULL,
                    display_name VARCHAR(100) NOT NULL, role VARCHAR(10) NOT NULL DEFAULT 'user',
                    created_at DATETIME NOT NULL, last_login DATETIME,
                    failed_login_attempts INTEGER NOT NULL DEFAULT 0, locked_until DATETIME,
                    is_legacy BOOLEAN NOT NULL DEFAULT 0
                )"""
            )
            conn.exec_driver_sql(
                """CREATE TABLE IF NOT EXISTS auth_tokens (
                    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                    token_hash VARCHAR(64) NOT NULL UNIQUE, expires_at DATETIME NOT NULL,
                    created_at DATETIME NOT NULL
                )"""
            )
            tables = set(conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).scalars())
            additions = {
                "conversations": {
                    "user_id": "INTEGER REFERENCES users(id)",
                    "updated_at": "DATETIME",
                    "is_pinned": "BOOLEAN NOT NULL DEFAULT 0",
                    "is_deleted": "BOOLEAN NOT NULL DEFAULT 0",
                },
                "messages": {
                    "intent": "VARCHAR(100)",
                    "confidence": "FLOAT",
                    "top_predictions": "TEXT NOT NULL DEFAULT '[]'",
                    "resolved_query": "TEXT",
                    "is_fallback": "BOOLEAN NOT NULL DEFAULT 0",
                },
                "unknown_queries": {
                    "user_id": "INTEGER REFERENCES users(id)",
                    "conversation_id": "INTEGER REFERENCES conversations(id)",
                },
            }
            for table, fields in additions.items():
                if table not in tables:
                    continue
                present = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").all()}
                for name, declaration in fields.items():
                    if name not in present:
                        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")

            users_table = set(conn.exec_driver_sql("PRAGMA table_info(users)").scalars())
            # A fixed internal owner keeps old rows separate from all real accounts.
            legacy = conn.exec_driver_sql("SELECT id FROM users WHERE is_legacy = 1 LIMIT 1").first()
            if not legacy:
                conn.exec_driver_sql(
                    """INSERT INTO users
                       (id, username, email, password_hash, display_name, role, created_at,
                        failed_login_attempts, is_legacy)
                       VALUES (1, '_legacy_guest', 'legacy-guest@local.invalid', '',
                               'Legacy guest', 'user', ?, 0, 1)""",
                    (_now().isoformat(sep=" ", timespec="microseconds"),),
                )
                legacy_id = 1
            else:
                legacy_id = legacy[0]
            if "conversations" in tables:
                conn.exec_driver_sql(
                    "UPDATE conversations SET user_id = ? WHERE user_id IS NULL", (legacy_id,)
                )
                if "created_at" in columns.get("conversations", set()):
                    conn.exec_driver_sql(
                        """UPDATE conversations SET updated_at = COALESCE(
                           (SELECT MAX(timestamp) FROM messages WHERE messages.conversation_id=conversations.id),
                           created_at, CURRENT_TIMESTAMP) WHERE updated_at IS NULL"""
                    )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations(user_id)"
                )
                conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_conversations_updated_at ON conversations(updated_at)"
                )
            if "messages" in tables and "intent_predictions" in tables:
                # The old application logged intent on the user row. Copy it onto the reply
                # row so saved chats retain their original badge and confidence.
                conn.exec_driver_sql(
                    """UPDATE messages AS bot SET
                         intent = (SELECT ip.predicted_intent FROM intent_predictions ip
                                   JOIN messages usr ON usr.id=ip.message_id
                                   WHERE usr.conversation_id=bot.conversation_id
                                     AND usr.sender='user' AND usr.id < bot.id
                                   ORDER BY usr.id DESC LIMIT 1),
                         confidence = (SELECT ip.confidence FROM intent_predictions ip
                                       JOIN messages usr ON usr.id=ip.message_id
                                       WHERE usr.conversation_id=bot.conversation_id
                                         AND usr.sender='user' AND usr.id < bot.id
                                       ORDER BY usr.id DESC LIMIT 1),
                         is_fallback = COALESCE((SELECT ip.is_fallback FROM intent_predictions ip
                                       JOIN messages usr ON usr.id=ip.message_id
                                       WHERE usr.conversation_id=bot.conversation_id
                                         AND usr.sender='user' AND usr.id < bot.id
                                       ORDER BY usr.id DESC LIMIT 1), 0),
                         resolved_query = (SELECT usr.message_text FROM messages usr
                                           WHERE usr.conversation_id=bot.conversation_id
                                             AND usr.sender='user' AND usr.id < bot.id
                                           ORDER BY usr.id DESC LIMIT 1),
                         sentiment = COALESCE((SELECT usr.sentiment FROM messages usr
                                           WHERE usr.conversation_id=bot.conversation_id
                                             AND usr.sender='user' AND usr.id < bot.id
                                           ORDER BY usr.id DESC LIMIT 1), bot.sentiment),
                         compound_score = COALESCE((SELECT usr.compound_score FROM messages usr
                                           WHERE usr.conversation_id=bot.conversation_id
                                             AND usr.sender='user' AND usr.id < bot.id
                                           ORDER BY usr.id DESC LIMIT 1), bot.compound_score),
                         top_predictions = '[]'
                       WHERE bot.sender='bot' AND bot.intent IS NULL"""
                )
            if "unknown_queries" in tables:
                conn.exec_driver_sql(
                    "UPDATE unknown_queries SET user_id = ? WHERE user_id IS NULL", (legacy_id,)
                )
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_auth_tokens_user_id ON auth_tokens(user_id)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_auth_tokens_token_hash ON auth_tokens(token_hash)")

    def get_session(self):
        return self.Session()

    @staticmethod
    def _user_dict(user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "created_at": user.created_at,
            "last_login": user.last_login,
        }

    def create_user(self, username: str, email: str, password: str,
                    display_name: str, role: str | None = None) -> dict:
        username = username.strip().lower()
        email = email.strip().lower()
        session = self.get_session()
        try:
            existing = session.query(User.id).filter(
                or_(func.lower(User.username) == username, func.lower(User.email) == email)
            ).first()
            if existing:
                raise ValueError("Username or email is already registered.")
            registered_users = session.query(User).filter(User.is_legacy.is_(False)).count()
            assigned_role = "admin" if (registered_users == 0 or role == "admin") else "user"
            registered_at = _now()
            user = User(
                username=username,
                email=email,
                password_hash=_password_hash(password),
                display_name=display_name.strip(),
                role=assigned_role,
                created_at=registered_at,
                last_login=registered_at,
                is_legacy=False,
            )
            session.add(user)
            session.commit()
            return self._user_dict(user)
        finally:
            session.close()

    def get_user_by_username_or_email(self, username_or_email: str) -> dict | None:
        session = self.get_session()
        try:
            value = username_or_email.strip().lower()
            user = session.query(User).filter(
                User.is_legacy.is_(False),
                or_(func.lower(User.username) == value, func.lower(User.email) == value),
            ).first()
            return self._user_dict(user) if user else None
        finally:
            session.close()

    def verify_user(self, username_or_email: str, password: str) -> dict | None:
        """Verify credentials and persist the five-failures/five-minute lockout."""
        session = self.get_session()
        try:
            value = username_or_email.strip().lower()
            user = session.query(User).filter(
                User.is_legacy.is_(False),
                or_(func.lower(User.username) == value, func.lower(User.email) == value),
            ).first()
            if user is None:
                # Burn a bcrypt check on unknown names to make account enumeration slower.
                bcrypt.checkpw(_password_material(password), _DUMMY_PASSWORD_HASH)
                return None
            now = _now()
            if user.locked_until and user.locked_until > now:
                return None
            if user.locked_until and user.locked_until <= now:
                user.failed_login_attempts = 0
                user.locked_until = None
            try:
                valid = bcrypt.checkpw(_password_material(password), user.password_hash.encode("ascii"))
            except (ValueError, TypeError):
                valid = False
            if not valid:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = now + timedelta(minutes=5)
                session.commit()
                return None
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = now
            session.commit()
            return self._user_dict(user)
        finally:
            session.close()

    def create_auth_token(self, user_id: int, expires_in_days: int = 30) -> str:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        session = self.get_session()
        try:
            session.add(AuthToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=_now() + timedelta(days=expires_in_days),
                created_at=_now(),
            ))
            session.commit()
            return raw_token
        finally:
            session.close()

    def get_user_by_token(self, token: str) -> dict | None:
        if not token:
            return None
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        session = self.get_session()
        try:
            record = session.query(AuthToken).filter(
                AuthToken.token_hash == token_hash,
                AuthToken.expires_at > _now(),
            ).first()
            if not record or not record.user or record.user.is_legacy:
                return None
            return self._user_dict(record.user)
        finally:
            session.close()

    def revoke_token(self, token: str) -> bool:
        if not token:
            return False
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        session = self.get_session()
        try:
            deleted = session.query(AuthToken).filter(AuthToken.token_hash == token_hash).delete()
            session.commit()
            return bool(deleted)
        finally:
            session.close()

    def create_conversation(self, user_id: int, title: str = "New Chat") -> int:
        session = self.get_session()
        try:
            user = session.query(User.id).filter(User.id == user_id, User.is_legacy.is_(False)).first()
            if not user:
                raise PermissionError("A conversation needs an authenticated owner.")
            now = _now()
            conv = Conversation(user_id=user_id, title=title, created_at=now, updated_at=now)
            session.add(conv)
            session.commit()
            return conv.id
        finally:
            session.close()

    def list_conversations(self, user_id: int, search: str | None = None,
                           limit: int = 20, offset: int = 0) -> list[dict]:
        session = self.get_session()
        try:
            query = session.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            )
            term = (search or "").strip()
            if term:
                pattern = f"%{term}%"
                query = query.filter(or_(
                    Conversation.title.ilike(pattern),
                    Conversation.messages.any(Message.message_text.ilike(pattern)),
                ))
            rows = query.order_by(Conversation.updated_at.desc(), Conversation.id.desc()).offset(
                max(0, offset)
            ).limit(max(0, limit)).all()
            return [{
                "id": row.id,
                "title": row.title,
                "created_at": row.created_at,
                "updated_at": row.updated_at or row.created_at,
                "is_pinned": bool(row.is_pinned),
            } for row in rows]
        finally:
            session.close()

    def get_conversation_messages(self, conversation_id: int, user_id: int) -> list[dict]:
        session = self.get_session()
        try:
            conv = session.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            ).first()
            if not conv:
                return []
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.id.asc()).all()
            restored = []
            pending_user = None
            for message in messages:
                if message.sender == "user":
                    pending_user = message
                elif message.sender == "bot":
                    if pending_user is None:
                        continue
                    latest_feedback = session.query(FeedbackLog.rating).filter(
                        FeedbackLog.message_id == message.id
                    ).order_by(FeedbackLog.timestamp.desc(), FeedbackLog.id.desc()).first()
                    try:
                        predictions = json.loads(message.top_predictions or "[]")
                    except (TypeError, json.JSONDecodeError):
                        predictions = []
                    restored.append({
                        "user_query": pending_user.message_text or "",
                        "response": message.message_text or "",
                        "intent": message.intent or "unknown",
                        "confidence": float(message.confidence or 0.0),
                        "top_predictions": predictions,
                        "resolved_query": message.resolved_query or pending_user.message_text or "",
                        "is_fallback": bool(message.is_fallback),
                        "sentiment": message.sentiment or pending_user.sentiment or "Neutral",
                        "message_id": message.id,
                        "feedback_vote": latest_feedback[0] if latest_feedback else None,
                    })
                    pending_user = None
            return restored
        finally:
            session.close()

    def get_conversation(self, conversation_id: int, user_id: int) -> dict | None:
        session = self.get_session()
        try:
            row = session.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            ).first()
            if not row:
                return None
            return {"id": row.id, "title": row.title, "is_pinned": bool(row.is_pinned)}
        finally:
            session.close()

    def rename_conversation(self, conversation_id: int, user_id: int, title: str) -> bool:
        clean_title = " ".join((title or "").split())[:255]
        if not clean_title:
            return False
        session = self.get_session()
        try:
            row = session.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            ).first()
            if not row:
                return False
            row.title = clean_title
            row.updated_at = _now()
            session.commit()
            return True
        finally:
            session.close()

    def pin_conversation(self, conversation_id: int, user_id: int, is_pinned: bool | None = None) -> bool:
        session = self.get_session()
        try:
            row = session.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            ).first()
            if not row:
                return False
            row.is_pinned = not row.is_pinned if is_pinned is None else bool(is_pinned)
            row.updated_at = _now()
            session.commit()
            return True
        finally:
            session.close()

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        session = self.get_session()
        try:
            row = session.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            ).first()
            if not row:
                return False
            row.is_deleted = True
            row.updated_at = _now()
            session.commit()
            return True
        finally:
            session.close()

    def log_interaction(self, conversation_id: int, user_id: int, user_text: str,
                        bot_response: str, intent_data: dict, sentiment_data: dict,
                        resolved_query: str | None = None) -> int:
        session = self.get_session()
        try:
            conv = session.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            ).first()
            if not conv:
                raise PermissionError("Conversation does not belong to this account.")
            now = _now()
            previous_count = session.query(Message.id).filter(
                Message.conversation_id == conversation_id
            ).count()
            if previous_count == 0:
                title = " ".join(user_text.strip().split())[:40]
                conv.title = title or "New Chat"
            conv.updated_at = now
            intent = intent_data.get("tag", "unknown")
            confidence = float(intent_data.get("confidence", 0.0) or 0.0)
            fallback = bool(intent_data.get("is_fallback", False))
            sentiment = sentiment_data.get("sentiment", "Neutral")
            compound = float(sentiment_data.get("compound", 0.0) or 0.0)
            user_msg = Message(
                conversation_id=conversation_id,
                sender="user",
                message_text=user_text,
                sentiment=sentiment,
                compound_score=compound,
                timestamp=now,
            )
            session.add(user_msg)
            session.flush()
            session.add(IntentPredictionLog(
                message_id=user_msg.id,
                predicted_intent=intent,
                confidence=confidence,
                is_fallback=fallback,
                timestamp=now,
            ))
            if fallback:
                session.add(UnknownQueryLog(
                    user_text=user_text,
                    confidence=confidence,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    timestamp=now,
                ))
            bot_msg = Message(
                conversation_id=conversation_id,
                sender="bot",
                message_text=bot_response,
                sentiment=sentiment,
                compound_score=compound,
                timestamp=now,
                intent=intent,
                confidence=confidence,
                top_predictions=json.dumps(intent_data.get("top_predictions", [])),
                resolved_query=resolved_query or user_text,
                is_fallback=fallback,
            )
            session.add(bot_msg)
            session.commit()
            return bot_msg.id
        finally:
            session.close()

    def add_feedback(self, message_id: int, user_id: int, rating: int, comment: str = "") -> bool:
        session = self.get_session()
        try:
            message = session.query(Message).join(Conversation).filter(
                Message.id == message_id,
                Message.sender == "bot",
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            ).first()
            if not message:
                return False
            session.add(FeedbackLog(message_id=message_id, rating=rating, comment=comment))
            session.commit()
            return True
        finally:
            session.close()

    def get_unknown_queries(self, user_id: int | None = None, include_all: bool = False) -> list:
        session = self.get_session()
        try:
            query = session.query(UnknownQueryLog)
            if not include_all:
                if user_id is None:
                    return []
                query = query.filter(UnknownQueryLog.user_id == user_id)
            rows = query.order_by(UnknownQueryLog.timestamp.desc()).all()
            return [{
                "id": row.id,
                "text": row.user_text,
                "confidence": round(float(row.confidence or 0.0), 4),
                "reviewed": row.reviewed,
                "mapped_intent": row.mapped_intent,
                "timestamp": row.timestamp.strftime("%Y-%m-%d %H:%M") if row.timestamp else "",
            } for row in rows]
        finally:
            session.close()


_DUMMY_PASSWORD_HASH = bcrypt.hashpw(_password_material("not-a-real-password"), bcrypt.gensalt())
db = DatabaseManager()
