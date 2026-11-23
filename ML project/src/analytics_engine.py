"""Conversation metrics scoped to one owner, with an aggregate admin view."""

import pandas as pd
from sqlalchemy import func

from src.database import (
    Conversation,
    FeedbackLog,
    IntentPredictionLog,
    Message,
    UnknownQueryLog,
    User,
    db,
)


class AnalyticsEngine:
    def _scope(self, query, user_id: int | None, include_all: bool):
        query = query.join(Conversation, Conversation.id == Message.conversation_id)
        if include_all:
            return query.join(User, User.id == Conversation.user_id).filter(
                Conversation.is_deleted.is_(False), User.is_legacy.is_(False)
            )
        if user_id is None:
            return None
        return query.filter(Conversation.user_id == user_id, Conversation.is_deleted.is_(False))

    def get_summary_metrics(self, user_id: int | None = None, include_all: bool = False) -> dict:
        empty = {
            "total_conversations": 0, "total_messages": 0, "user_messages": 0,
            "average_confidence": 0.0, "positive_sentiment": 0, "neutral_sentiment": 0,
            "negative_sentiment": 0, "thumbs_up": 0, "thumbs_down": 0, "unknown_queries": 0,
        }
        if user_id is None and not include_all:
            return empty
        session = db.get_session()
        try:
            conv_query = session.query(Conversation).filter(Conversation.is_deleted.is_(False))
            if include_all:
                conv_query = conv_query.join(User, User.id == Conversation.user_id).filter(User.is_legacy.is_(False))
            else:
                conv_query = conv_query.filter(Conversation.user_id == user_id)
            conversation_ids = conv_query.with_entities(Conversation.id).subquery()
            message_scope = Message.conversation_id.in_(conversation_ids)
            total_convs = conv_query.count()
            total_msgs = session.query(func.count(Message.id)).filter(message_scope).scalar() or 0
            user_msgs = session.query(func.count(Message.id)).filter(
                message_scope, Message.sender == "user"
            ).scalar() or 0
            avg_conf = session.query(func.avg(IntentPredictionLog.confidence)).join(
                Message, Message.id == IntentPredictionLog.message_id
            ).filter(message_scope).scalar() or 0.0
            sentiments = {
                label: session.query(func.count(Message.id)).filter(
                    message_scope, Message.sender == "user", Message.sentiment == label
                ).scalar() or 0
                for label in ("Positive", "Neutral", "Negative")
            }
            feedback_query = session.query(FeedbackLog).join(
                Message, Message.id == FeedbackLog.message_id
            ).filter(message_scope)
            thumbs_up = feedback_query.filter(FeedbackLog.rating == 1).count()
            thumbs_down = feedback_query.filter(FeedbackLog.rating == -1).count()
            unknown_query = session.query(UnknownQueryLog).join(
                Conversation, Conversation.id == UnknownQueryLog.conversation_id
            ).filter(Conversation.is_deleted.is_(False))
            if include_all:
                unknown_query = unknown_query.join(User, User.id == UnknownQueryLog.user_id).filter(User.is_legacy.is_(False))
            else:
                unknown_query = unknown_query.filter(UnknownQueryLog.user_id == user_id)
            return {
                "total_conversations": total_convs,
                "total_messages": total_msgs,
                "user_messages": user_msgs,
                "average_confidence": round(float(avg_conf), 4),
                "positive_sentiment": sentiments["Positive"],
                "neutral_sentiment": sentiments["Neutral"],
                "negative_sentiment": sentiments["Negative"],
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "unknown_queries": unknown_query.count(),
            }
        finally:
            session.close()

    def get_intent_distribution(self, user_id: int | None = None,
                                include_all: bool = False) -> pd.DataFrame:
        if user_id is None and not include_all:
            return pd.DataFrame(columns=["intent", "count"])
        session = db.get_session()
        try:
            query = session.query(
                IntentPredictionLog.predicted_intent,
                func.count(IntentPredictionLog.id).label("count"),
            ).join(Message, Message.id == IntentPredictionLog.message_id)
            query = self._scope(query, user_id, include_all)
            results = query.group_by(IntentPredictionLog.predicted_intent).all()
            return pd.DataFrame([{"intent": item[0], "count": item[1]} for item in results],
                                columns=["intent", "count"])
        finally:
            session.close()

    def get_sentiment_distribution(self, user_id: int | None = None,
                                   include_all: bool = False) -> pd.DataFrame:
        if user_id is None and not include_all:
            return pd.DataFrame(columns=["sentiment", "count"])
        session = db.get_session()
        try:
            query = session.query(
                Message.sentiment, func.count(Message.id).label("count")
            ).filter(Message.sender == "user")
            query = self._scope(query, user_id, include_all)
            results = query.group_by(Message.sentiment).all()
            return pd.DataFrame([{"sentiment": item[0], "count": item[1]} for item in results],
                                columns=["sentiment", "count"])
        finally:
            session.close()


analytics_engine = AnalyticsEngine()
