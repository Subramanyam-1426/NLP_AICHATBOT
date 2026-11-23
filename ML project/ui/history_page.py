"""A dedicated, easy-to-find page for reopening saved conversations."""

from datetime import date, datetime, timedelta
from html import escape

import streamlit as st

from src.database import db


@st.dialog("Delete this conversation?")
def _confirm_history_delete(conversation_id: int, user_id: int):
    st.write("This conversation will be removed from your history.")
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Delete conversation", type="primary", key="confirm_history_delete"):
            db.delete_conversation(conversation_id, user_id)
            if st.session_state.get("active_conversation_id") == conversation_id:
                st.session_state.active_conversation_id = None
                st.session_state.loaded_conversation_id = None
                st.session_state.chat_history = []
                st.query_params.pop("chat", None)
            st.session_state.pending_history_delete_id = None
            st.rerun()
    with cancel_col:
        if st.button("Cancel", key="cancel_history_delete"):
            st.session_state.pending_history_delete_id = None
            st.rerun()


def _date_group(updated_at: datetime) -> str:
    day = updated_at.date() if isinstance(updated_at, datetime) else date.today()
    today = date.today()
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    if day >= today - timedelta(days=7):
        return "Previous 7 days"
    return "Older"


def _open_chat(conversation_id: int):
    st.session_state.active_conversation_id = conversation_id
    st.session_state.loaded_conversation_id = None
    st.session_state._nav_page = "Chat"
    st.query_params["chat"] = str(conversation_id)
    st.rerun()


def _start_new_chat():
    st.session_state.active_conversation_id = None
    st.session_state.loaded_conversation_id = None
    st.session_state.chat_history = []
    st.session_state.chat_feedback_votes = {}
    st.session_state._nav_page = "Chat"
    st.query_params.pop("chat", None)
    st.rerun()


def render_history_page(user: dict | None, guest_mode: bool = False):
    st.title("Chat history")
    st.caption("Find and reopen your saved conversations. Chats are saved after you send the first message.")

    if not user:
        if guest_mode:
            st.info("Guest chats are not saved. Sign in to see your account history.")
            if st.button("Log in or sign up", type="primary", key="history_page_login"):
                st.session_state.guest_mode = False
                st.session_state.pop("guest_session_id", None)
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.info("Log in to view your saved conversations.")
        return

    search = st.text_input(
        "Search chats", placeholder="Search by title or message", key="history_page_search"
    )
    previous_search = st.session_state.get("_history_page_last_search", "")
    if search != previous_search:
        st.session_state.history_page_count = 20
        st.session_state._history_page_last_search = search
    count = int(st.session_state.get("history_page_count", 20))
    chats = db.list_conversations(user["id"], search=search, limit=count, offset=0)

    header_col, action_col = st.columns([4, 1.3], vertical_alignment="center")
    with header_col:
        st.subheader(f"{len(chats)} conversation{'s' if len(chats) != 1 else ''}")
    with action_col:
        if st.button("＋ New chat", type="primary", use_container_width=True, key="history_page_new_chat"):
            _start_new_chat()

    if not chats:
        if search:
            st.info("No chats match that search.")
        else:
            st.info("No saved conversations yet. Start a chat and it will appear here after your first message.")
        pending = st.session_state.get("pending_history_delete_id")
        if pending:
            _confirm_history_delete(pending, user["id"])
        return

    groups = {"Pinned": [], "Today": [], "Yesterday": [], "Previous 7 days": [], "Older": []}
    for chat in chats:
        group = "Pinned" if chat["is_pinned"] else _date_group(chat["updated_at"])
        groups[group].append(chat)

    for group, items in groups.items():
        if not items:
            continue
        st.subheader(group)
        for chat in items:
            conversation_id = chat["id"]
            title = ("📌 " if chat["is_pinned"] else "") + (chat["title"] or "New chat")
            with st.container(border=True):
                title_col, open_col, menu_col = st.columns([5, 1.3, 0.8], vertical_alignment="center")
                with title_col:
                    st.markdown(f"**{escape(title)}**")
                    st.caption(f"Updated {chat['updated_at']:%b %d, %Y at %I:%M %p}")
                with open_col:
                    if st.button("Open", key=f"history_page_open_{conversation_id}", use_container_width=True):
                        _open_chat(conversation_id)
                with menu_col:
                    with st.popover("⋯", key=f"history_page_menu_{conversation_id}", use_container_width=True):
                        renamed = st.text_input(
                            "Conversation title", value=chat["title"],
                            key=f"history_page_rename_text_{conversation_id}",
                        )
                        if st.button("Save name", key=f"history_page_rename_{conversation_id}", use_container_width=True):
                            if db.rename_conversation(conversation_id, user["id"], renamed):
                                st.rerun()
                            st.error("Enter a title before saving.")
                        pin_label = "Unpin" if chat["is_pinned"] else "Pin"
                        if st.button(pin_label, key=f"history_page_pin_{conversation_id}", use_container_width=True):
                            db.pin_conversation(conversation_id, user["id"], not chat["is_pinned"])
                            st.rerun()
                        if st.button("Delete…", key=f"history_page_delete_{conversation_id}", use_container_width=True):
                            st.session_state.pending_history_delete_id = conversation_id
                            st.rerun()

    if len(chats) == count:
        if st.button("Show more", key="history_page_show_more", use_container_width=True):
            st.session_state.history_page_count = count + 20
            st.rerun()

    pending = st.session_state.get("pending_history_delete_id")
    if pending:
        _confirm_history_delete(pending, user["id"])
