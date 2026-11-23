import streamlit as st

from src.analytics_engine import analytics_engine
from src.intent_classifier import intent_classifier
from ui.theme import render_page_header


_PAGES = [
    ("Chat", "chat", "Ask general questions, explore ideas, and draft polished messages."),
    ("NLTK Lab", "psychology", "Inspect tokenization, tags, sentiment, stems, and lemmas."),
    ("Document Q&A", "description", "Search local PDF, DOCX, and text files with source snippets."),
    ("Analytics", "monitoring", "Review conversation volume, intent mix, sentiment, and feedback."),
    ("Model Training", "model_training", "Train and benchmark the local intent classifier."),
    ("Demo Mode", "slideshow", "Run short demonstrations of the NLP and retrieval modules."),
]


def _open_page(page: str) -> None:
    st.session_state["_nav_page"] = page
    st.rerun()


def render_home():
    render_page_header(
        "Your AI workspace",
        "auto_awesome",
        "Conversations, language tools, and local document knowledge in one place.",
    )
    st.markdown("### Your local space to ask, explore, and create.")
    st.button(
        "Start chatting",
        key="home_start_chatting",
        icon=":material/chat:",
        type="primary",
        on_click=_open_page,
        args=("Chat",),
    )

    user = st.session_state.get("user")
    metrics = analytics_engine.get_summary_metrics(user_id=user["id"] if user else None)
    model_accuracy = intent_classifier.metrics.get("accuracy", 0.0) if intent_classifier.metrics else 0.0
    intent_count = len(intent_classifier.intents_data)

    stat_columns = st.columns(3)
    stats = [
        ("Messages", metrics.get("total_messages", 0), "forum", "Conversations stored locally"),
        ("Model accuracy", f"{model_accuracy:.0%}", "insights", "Held-out evaluation score"),
        ("Intent classes", intent_count, "category", "Topics available to the model"),
    ]
    for column, (label, value, icon, detail) in zip(stat_columns, stats):
        with column:
            with st.container(border=True, key=f"home_stat_{label.lower().replace(' ', '_')}"):
                st.markdown(f":material/{icon}: **{label}**")
                st.metric(label, value, label_visibility="collapsed")
                st.caption(detail)

    st.subheader("Explore")
    for start in range(0, len(_PAGES), 3):
        columns = st.columns(3)
        for column, (title, icon, description) in zip(columns, _PAGES[start:start + 3]):
            with column:
                with st.container(border=True, key=f"home_card_{title.lower().replace(' ', '_')}"):
                    st.subheader(title, icon=f":material/{icon}:")
                    st.caption(description)
                    st.button(
                        "Open",
                        key=f"home_open_{title.lower().replace(' ', '_')}",
                        icon=":material/arrow_forward:",
                        type="primary",
                        on_click=_open_page,
                        args=(title,),
                    )

    st.caption("Local-first assistant · responses from trained examples, FAQs, and files you upload.")
