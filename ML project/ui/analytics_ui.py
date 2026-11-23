import streamlit as st
import pandas as pd
import plotly.express as px
from src.analytics_engine import analytics_engine
from src.database import db, Message, IntentPredictionLog, Conversation, User
from ui.theme import apply_plotly_theme, render_page_header


def _load_chart_data(user_id: int | None, include_all: bool = False):
    session = db.get_session()
    try:
        messages_query = session.query(Message.timestamp, Message.sentiment).join(
            Conversation, Conversation.id == Message.conversation_id
        ).filter(Message.sender == "user", Conversation.is_deleted.is_(False))
        confidence_query = session.query(IntentPredictionLog.confidence).join(
            Message, Message.id == IntentPredictionLog.message_id
        ).join(Conversation, Conversation.id == Message.conversation_id).filter(
            Conversation.is_deleted.is_(False)
        )
        if include_all:
            messages_query = messages_query.join(User, User.id == Conversation.user_id).filter(User.is_legacy.is_(False))
            confidence_query = confidence_query.join(User, User.id == Conversation.user_id).filter(User.is_legacy.is_(False))
        elif user_id is not None:
            messages_query = messages_query.filter(Conversation.user_id == user_id)
            confidence_query = confidence_query.filter(Conversation.user_id == user_id)
        else:
            return pd.DataFrame(columns=["timestamp", "sentiment", "day", "size"]), pd.DataFrame(columns=["confidence"])
        messages = messages_query.order_by(Message.timestamp).all()
        confidences = confidence_query.all()
        mood = pd.DataFrame(messages, columns=["timestamp", "sentiment"])
        confidence = pd.DataFrame(confidences, columns=["confidence"])
        if not mood.empty:
            mood["timestamp"] = pd.to_datetime(mood["timestamp"])
            mood["day"] = mood["timestamp"].dt.date
            mood = mood.groupby(["day", "sentiment"], as_index=False).size()
        if not confidence.empty:
            confidence["confidence"] = confidence["confidence"].fillna(0).astype(float)
        return mood, confidence
    finally:
        session.close()

def render_analytics():
    render_page_header(
        "Analytics",
        "monitoring",
        "A live view of conversation activity and model behavior.",
    )

    user = st.session_state.get("user")
    include_all = False
    if user and user.get("role") == "admin":
        include_all = st.toggle("All users", key="analytics_all_users", help="Show aggregate metrics across registered accounts.")
    user_id = user["id"] if user else None
    metrics = analytics_engine.get_summary_metrics(user_id=user_id, include_all=include_all)

    with st.container(horizontal=True, gap="small"):
        st.metric("User messages", metrics["user_messages"], border=True)
        st.metric("Conversations", metrics["total_conversations"], border=True)
        st.metric("Mean confidence", f"{metrics['average_confidence']:.0%}", border=True)
        st.metric("Feedback", f"{metrics['thumbs_up']} / {metrics['thumbs_down']}", border=True)

    is_dark = st.session_state.get("dark_mode", False)
    chart_template = "plotly_dark" if is_dark else "plotly_white"
    mood_trend, confidence_data = _load_chart_data(user_id, include_all)
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True, key="analytics_chart_intents"):
            st.markdown("**:material/bar_chart: Top intents**")
            df_intents = analytics_engine.get_intent_distribution(user_id, include_all)
            if not df_intents.empty and df_intents["count"].sum() > 0:
                df_intents = df_intents.sort_values("count", ascending=False).reset_index(drop=True)
                if len(df_intents) > 10:
                    other_count = int(df_intents.iloc[10:]["count"].sum())
                    df_intents = df_intents.iloc[:10].copy()
                    df_intents.loc[len(df_intents)] = {"intent": "Other", "count": other_count}
                fig = px.bar(
                    df_intents.sort_values("count", ascending=True),
                    x="count",
                    y="intent",
                    orientation="h",
                    text="count",
                    color_discrete_sequence=["#a99cff" if is_dark else "#5147d9"],
                    template=chart_template,
                )
                fig.update_layout(
                    height=330,
                    margin=dict(t=8, b=8, l=8, r=30),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Messages",
                    yaxis_title=None,
                )
                fig.update_traces(textposition="outside", cliponaxis=False)
                apply_plotly_theme(fig, is_dark)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            else:
                st.info("Start a conversation to build the intent distribution.", icon=":material/chat:")

    with col2:
        with st.container(border=True, key="analytics_chart_sentiment"):
            st.markdown("**:material/mood: Sentiment mix**")
            df_sent = analytics_engine.get_sentiment_distribution(user_id, include_all)
            if metrics["user_messages"] > 0 and not df_sent.empty:
                fig2 = px.bar(
                    df_sent, x="sentiment", y="count", color="sentiment",
                    text="count",
                    color_discrete_map={"Positive": "#16845b", "Neutral": "#7c8799", "Negative": "#cf4557"},
                    template=chart_template,
                )
                fig2.update_layout(
                    height=330,
                    margin=dict(t=8, b=8, l=8, r=12),
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title=None,
                    yaxis_title="Messages",
                )
                fig2.update_traces(marker_line_width=0, marker_cornerradius=6, textposition="outside")
                apply_plotly_theme(fig2, is_dark)
                st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
            else:
                st.info("Sentiment results will appear after the first message.", icon=":material/forum:")

    lower_left, lower_right = st.columns(2)
    with lower_left:
        with st.container(border=True, key="analytics_chart_mood"):
            st.markdown("**:material/timeline: Mood over time**")
            if not mood_trend.empty:
                fig3 = px.line(
                    mood_trend,
                    x="day",
                    y="size",
                    color="sentiment",
                    markers=True,
                    color_discrete_map={"Positive": "#16845b", "Neutral": "#7c8799", "Negative": "#cf4557"},
                    template=chart_template,
                )
                fig3.update_layout(
                    height=330,
                    margin=dict(t=8, b=8, l=8, r=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title=None,
                    yaxis_title="Messages",
                )
                apply_plotly_theme(fig3, is_dark)
                st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False})
            else:
                st.info("Mood trends appear once messages are logged.", icon=":material/timeline:")

    with lower_right:
        with st.container(border=True, key="analytics_chart_confidence"):
            st.markdown("**:material/speed: Confidence distribution**")
            if not confidence_data.empty:
                fig4 = px.histogram(
                    confidence_data,
                    x="confidence",
                    nbins=12,
                    color_discrete_sequence=["#a99cff" if is_dark else "#5147d9"],
                    template=chart_template,
                )
                fig4.update_layout(
                    height=330,
                    margin=dict(t=8, b=8, l=8, r=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Confidence",
                    yaxis_title="Predictions",
                )
                fig4.update_xaxes(tickformat=".0%", range=[0, 1])
                fig4.update_traces(marker_line_width=0, marker_cornerradius=6)
                apply_plotly_theme(fig4, is_dark)
                st.plotly_chart(fig4, width="stretch", config={"displayModeBar": False})
            else:
                st.info("Confidence appears after the first intent prediction.", icon=":material/speed:")
