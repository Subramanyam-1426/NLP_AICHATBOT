import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import pytest

from src.database import AuthToken, Conversation, DatabaseManager, Message, User
from src.chatbot_engine import chatbot_engine
from src.document_qa import DocumentQAEngine
from ui.auth_ui import _validate_signup


def _manager(tmp_path):
    return DatabaseManager(tmp_path / "accounts.db")


def test_signup_login_password_hash_and_first_admin(tmp_path):
    manager = _manager(tmp_path)
    first = manager.create_user("first_user", "first@example.com", "strongpass1", "First User")
    second = manager.create_user("second_user", "second@example.com", "otherpass2", "Second User")

    assert first["role"] == "admin"
    assert second["role"] == "user"
    assert manager.get_user_by_username_or_email("FIRST_USER")["id"] == first["id"]
    assert manager.get_user_by_username_or_email("first@example.com")["id"] == first["id"]
    assert manager.verify_user("first_user", "strongpass1")["id"] == first["id"]
    assert manager.verify_user("first_user", "wrongpass9") is None
    with manager.get_session() as session:
        stored = session.query(User).filter_by(id=first["id"]).one().password_hash
    assert stored != "strongpass1"
    assert stored.startswith(("$2a$", "$2b$", "$2y$"))
    assert bcrypt.checkpw(b"not-the-password", stored.encode()) is False


def test_signup_validation_messages():
    errors = _validate_signup("", "no spaces", "not-an-email", "short", "different")
    assert set(errors) == {"name", "username", "email", "password", "confirmation"}
    assert _validate_signup("A Name", "good_name2", "a@example.org", "password9", "password9") == {}


def test_login_lockout_after_five_failures(tmp_path):
    manager = _manager(tmp_path)
    user = manager.create_user("lock_user", "lock@example.com", "strongpass1", "Lock User")
    for _ in range(5):
        assert manager.verify_user("lock_user", "incorrect9") is None
    # Even the right password is rejected during the five-minute lock.
    assert manager.verify_user("lock@example.com", "strongpass1") is None
    with manager.get_session() as session:
        record = session.query(User).filter_by(id=user["id"]).one()
        assert record.failed_login_attempts == 5
        assert record.locked_until is not None
        record.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        session.commit()
    assert manager.verify_user("lock_user", "strongpass1")["id"] == user["id"]


def test_remember_token_expiry_and_revocation(tmp_path):
    manager = _manager(tmp_path)
    user = manager.create_user("token_user", "token@example.com", "strongpass1", "Token User")
    token = manager.create_auth_token(user["id"])
    assert manager.get_user_by_token(token)["id"] == user["id"]
    with manager.get_session() as session:
        record = session.query(AuthToken).one()
        assert record.token_hash != token
        record.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        session.commit()
    assert manager.get_user_by_token(token) is None

    live_token = manager.create_auth_token(user["id"])
    assert manager.revoke_token(live_token) is True
    assert manager.get_user_by_token(live_token) is None


def test_conversation_access_isolation_and_history_metadata(tmp_path):
    manager = _manager(tmp_path)
    owner = manager.create_user("owner_a", "owner@example.com", "strongpass1", "Owner")
    other = manager.create_user("owner_b", "other@example.com", "otherpass2", "Other")
    conversation_id = manager.create_conversation(owner["id"])
    query = "Tell me about Python and its language features in detail"
    bot_id = manager.log_interaction(
        conversation_id=conversation_id,
        user_id=owner["id"],
        user_text=query,
        bot_response="Python is a programming language.",
        intent_data={
            "tag": "python_info", "confidence": 0.87, "is_fallback": False,
            "top_predictions": [{"tag": "python_info", "confidence": 0.87}],
        },
        sentiment_data={"sentiment": "Positive", "compound": 0.71},
        resolved_query="Tell me about Python and its language features in detail",
    )
    manager.add_feedback(bot_id, owner["id"], 1)

    assert [chat["id"] for chat in manager.list_conversations(owner["id"])] == [conversation_id]
    assert manager.list_conversations(other["id"]) == []
    assert manager.get_conversation_messages(conversation_id, other["id"]) == []
    assert manager.rename_conversation(conversation_id, other["id"], "stolen") is False
    assert manager.pin_conversation(conversation_id, other["id"], True) is False
    assert manager.delete_conversation(conversation_id, other["id"]) is False
    assert manager.get_conversation(conversation_id, owner["id"])["title"] == query[:40]

    restored = manager.get_conversation_messages(conversation_id, owner["id"])
    assert len(restored) == 1
    assert restored[0]["user_query"] == query
    assert restored[0]["intent"] == "python_info"
    assert restored[0]["confidence"] == pytest.approx(0.87)
    assert restored[0]["top_predictions"][0]["tag"] == "python_info"
    assert restored[0]["sentiment"] == "Positive"
    assert restored[0]["feedback_vote"] == 1

    assert manager.rename_conversation(conversation_id, owner["id"], "Renamed") is True
    assert manager.pin_conversation(conversation_id, owner["id"], True) is True
    assert manager.list_conversations(owner["id"])[0]["is_pinned"] is True
    assert manager.delete_conversation(conversation_id, owner["id"]) is True
    assert manager.get_conversation_messages(conversation_id, owner["id"]) == []


def test_migration_preserves_existing_database_copy(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    source_backup = project_root / "database" / "chatbot.pre_auth_backup.db"
    assert source_backup.exists(), "Create the pre-migration backup before applying the migration."
    legacy_copy = tmp_path / "chatbot_legacy_copy.db"
    shutil.copy2(source_backup, legacy_copy)
    with sqlite3.connect(legacy_copy) as connection:
        before_conversations = connection.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        before_messages = connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        assert "user_id" not in {
            row[1] for row in connection.execute("PRAGMA table_info(conversations)").fetchall()
        }

    manager = DatabaseManager(legacy_copy)
    with manager.get_session() as session:
        assert session.query(Conversation).count() == before_conversations
        assert session.query(Message).count() == before_messages
        legacy_user = session.query(User).filter_by(is_legacy=True).one()
        assert session.query(Conversation).filter_by(user_id=legacy_user.id).count() == before_conversations
        assert legacy_user.username == "_legacy_guest"


def test_context_memory_is_per_conversation():
    first = chatbot_engine._context_for(user_id=10, conversation_id=9001)
    second = chatbot_engine._context_for(user_id=20, conversation_id=9002)
    first.update_context("Tell me about Python", "python_info", "Python details", context_set="Python")

    assert first.resolve_coreference("Who created it?")[1] is True
    assert second.resolve_coreference("Who created it?")[1] is False


def test_document_indexes_are_per_user():
    engine = DocumentQAEngine()
    engine.process_raw_text(
        "The secret orchid archive contains blue flowers and green leaves for a botany study.",
        source_name="private_orchid.txt",
        user_id=1001,
    )

    assert engine.search_document("secret orchid archive blue flowers", user_id=1001)
    assert engine.search_document("secret orchid archive blue flowers", user_id=1002) == []
