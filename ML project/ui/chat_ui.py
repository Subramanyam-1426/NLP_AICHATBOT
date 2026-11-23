"""Persistent chat screen shared by registered accounts and unsaved guests."""

import re

import streamlit as st

from src.chatbot_engine import chatbot_engine
from src.database import db


@st.dialog("Clear this guest chat?")
def _confirm_clear_guest_chat():
    st.write("This will clear the messages from this browser session.")
    left, right = st.columns(2)
    with left:
        if st.button("Clear chat", type="primary", key="confirm_guest_clear"):
            st.session_state.chat_history = []
            st.session_state.chat_feedback_votes = {}
            st.session_state.pending_guest_clear = False
            st.rerun()
    with right:
        if st.button("Cancel", key="cancel_guest_clear"):
            st.session_state.pending_guest_clear = False
            st.rerun()


def _go_to_nltk_lab(prompt_text: str):
    st.session_state.nltk_prefill = prompt_text
    st.session_state._nav_page = "NLTK Lab"


def _new_pending_item(prompt: str) -> dict:
    return {
        "user_query": prompt,
        "response": "",
        "intent": "pending",
        "confidence": 0.0,
        "sentiment": "Neutral",
        "message_id": None,
        "_pending": True,
    }


def _queue_query(prompt: str, user: dict | None):
    if user and not st.session_state.get("active_conversation_id"):
        conversation_id = db.create_conversation(user["id"])
        st.session_state.active_conversation_id = conversation_id
        st.session_state.loaded_conversation_id = conversation_id
        st.query_params["chat"] = str(conversation_id)
    st.session_state.chat_history.append(_new_pending_item(prompt))


def _load_active_chat(user: dict | None):
    active_id = st.session_state.get("active_conversation_id") if user else None
    loaded_id = st.session_state.get("loaded_conversation_id")
    if not user:
        return
    if active_id != loaded_id:
        st.session_state.chat_history = []
        st.session_state.chat_feedback_votes = {}
        if active_id:
            turns = db.get_conversation_messages(active_id, user["id"])
            st.session_state.chat_history = turns
            for turn in turns:
                if turn.get("feedback_vote") is not None:
                    st.session_state.chat_feedback_votes[turn["message_id"]] = turn["feedback_vote"]
            chatbot_engine.restore_context(active_id, user["id"])
        st.session_state.loaded_conversation_id = active_id


def _conversation_title(user: dict | None) -> str:
    conversation_id = st.session_state.get("active_conversation_id")
    if user and conversation_id:
        conversation = db.get_conversation(conversation_id, user["id"])
        if conversation:
            return conversation["title"]
    return "New chat"


def render_chat():
    user = st.session_state.get("user")
    guest_mode = bool(st.session_state.get("guest_mode"))
    _load_active_chat(user)

    conversation_id = st.session_state.get("active_conversation_id") if user else None
    title = _conversation_title(user)
    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        st.subheader(title, anchor=False)
        with st.container(horizontal=True, gap="small", vertical_alignment="center"):
            if user and conversation_id:
                with st.popover("✎", help="Rename conversation", key="chat_title_rename"):
                    renamed = st.text_input("Conversation title", value=title, key="chat_title_value")
                    if st.button("Save title", key="chat_title_save", use_container_width=True):
                        if db.rename_conversation(conversation_id, user["id"], renamed):
                            st.rerun()
                        st.error("Enter a title before saving.")
            if user and st.button("History", icon=":material/history:", key="open_chat_history"):
                st.session_state._nav_page = "Chat history"
                st.rerun()
            st.badge("Saved" if user else "Guest chat (not saved)",
                     icon=":material/cloud_done:" if user else ":material/person_outline:",
                     color="green" if user else "gray")

    st.caption("Ask a question, explore an idea, or draft a message.")
    if guest_mode and st.session_state.get("pending_guest_clear"):
        _confirm_clear_guest_chat()

    if st.session_state.chat_history:
        transcript = "\n\n".join(
            f"You: {item['user_query']}\nAssistant: {item['response']}"
            for item in st.session_state.chat_history
            if not item.get("_pending")
        )
        with st.container(horizontal=True, horizontal_alignment="right", gap="small"):
            st.download_button(
                "Export chat",
                transcript,
                file_name="chat-transcript.txt",
                mime="text/plain",
                icon=":material/download:",
                key="export_chat",
            )
            if st.button("Clear chat", key="clear_chat", icon=":material/delete:", type="secondary"):
                if user and conversation_id:
                    st.session_state.pending_delete_conversation_id = conversation_id
                elif guest_mode:
                    st.session_state.pending_guest_clear = True
                st.rerun()

    user_input = st.chat_input("Type your message…")
    if user_input:
        _queue_query(user_input, user)
        st.rerun()

    if not st.session_state.chat_history:
        st.markdown(
            '<div class="empty-state"><h3>What would you like to explore?</h3>'
            "<p>Ask a question or choose a suggestion to get started.</p></div>",
            unsafe_allow_html=True,
        )
        suggestion_columns = st.columns(3)
        for column, label, prompt in zip(
            suggestion_columns,
            ("What is NLP?", "Applications of NLP", "Draft a formal email"),
            ("What is NLP?", "What are applications of NLP?", "Write a formal email"),
        ):
            with column:
                if st.button(label, key=f"chat_suggestion_{label}"):
                    _queue_query(prompt, user)
                    st.rerun()

    pending_item = next((item for item in st.session_state.chat_history if item.get("_pending")), None)
    for idx, item in enumerate(st.session_state.chat_history):
        with st.container(key=f"msg_user_{idx}"):
            with st.chat_message("user", avatar=":material/person:"):
                st.write(item["user_query"])
        if item.get("is_coreference_resolved"):
            st.caption(f"Resolved context: **{item.get('target_subject', '')}**")

        with st.container(key=f"msg_bot_{idx}"):
            with st.chat_message("assistant", avatar=":material/smart_toy:"):
                if item.get("_pending"):
                    st.markdown(
                        '<div class="typing-indicator" role="status" aria-label="Assistant is replying">'
                        "<span></span><span></span><span></span><span class=\"typing-label\">Thinking</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(item["response"])

        if item.get("_pending"):
            continue

        sentiment = item.get("sentiment", "Neutral")
        mood_color = {"Positive": "green", "Neutral": "gray", "Negative": "red"}.get(sentiment, "gray")
        with st.container(key=f"meta_bot_{idx}"):
            with st.container(horizontal=True, gap="small", vertical_alignment="center"):
                st.badge(item.get("intent", "unknown"), icon=":material/route:", color="violet")
                st.badge(sentiment, icon=":material/mood:", color=mood_color)
                st.caption(f"{int(item.get('confidence', 0) * 100)}% confidence")
                if item.get("is_fallback"):
                    st.badge("Fallback", icon=":material/info:", color="orange")
            msg_id = item.get("message_id")
            selected_vote = st.session_state.chat_feedback_votes.get(msg_id, item.get("feedback_vote"))
            with st.container(horizontal=True, gap="small", vertical_alignment="center"):
                if st.button(
                    "Analyze in NLTK Lab",
                    key=f"nltk_{idx}",
                    icon=":material/psychology:",
                    type="secondary",
                    help="Run this prompt through the NLTK pipeline",
                ):
                    _go_to_nltk_lab(item["user_query"])
                    st.rerun()

                if st.button(
                    ":material/thumb_up:",
                    key=f"up_{idx}",
                    help="Mark this response as helpful",
                    type="primary" if selected_vote == 1 else "secondary",
                ):
                    if msg_id and user:
                        db.add_feedback(msg_id, user["id"], 1)
                    vote_key = msg_id if msg_id else f"guest-{idx}"
                    st.session_state.chat_feedback_votes[vote_key] = 1
                    st.toast("Thanks for the feedback!", icon=":material/thumb_up:")

                if st.button(
                    ":material/thumb_down:",
                    key=f"dn_{idx}",
                    help="Mark this response as not helpful",
                    type="primary" if selected_vote == -1 else "secondary",
                ):
                    if msg_id and user:
                        db.add_feedback(msg_id, user["id"], -1)
                    vote_key = msg_id if msg_id else f"guest-{idx}"
                    st.session_state.chat_feedback_votes[vote_key] = -1
                    st.toast("Thanks. We'll use this to improve.", icon=":material/feedback:")

    if pending_item is not None:
        conv_history = []
        for item in st.session_state.chat_history[-7:-1]:
            if not item.get("_pending"):
                conv_history.append({"role": "user", "content": item["user_query"]})
                conv_history.append({"role": "assistant", "content": item["response"]})
        with st.spinner("Thinking…"):
            result = chatbot_engine.process_query(
                user_query=pending_item["user_query"],
                user_id=user["id"] if user else None,
                conversation_id=conversation_id,
                session_id=st.session_state.get("guest_session_id"),
                conversation_history=conv_history,
            )
        pending_item.update(result)
        if item_resolved := (result.get("resolved_query") != result.get("user_query")):
            pending_item["is_coreference_resolved"] = item_resolved
            match = re.search(r"\bregarding\s+(.+)$", result.get("resolved_query", ""), re.I)
            pending_item["target_subject"] = match.group(1) if match else result.get("target_subject", "")
        pending_item.pop("_pending", None)
        st.rerun()

