"""Account-aware conversation navigation in the existing gradient sidebar."""

from datetime import date, datetime, timedelta
from html import escape

import streamlit as st

from src.database import db


@st.dialog("Delete this conversation?")
def _confirm_delete(conversation_id: int, user_id: int):
    st.write("This conversation will be removed from your history.")
    left, right = st.columns(2)
    with left:
        if st.button("Delete conversation", type="primary", key="confirm_delete_conversation"):
            db.delete_conversation(conversation_id, user_id)
            if st.session_state.get("active_conversation_id") == conversation_id:
                st.session_state.active_conversation_id = None
                st.session_state.chat_history = []
                st.session_state.loaded_conversation_id = None
                st.query_params.pop("chat", None)
            st.session_state.pending_delete_conversation_id = None
            st.rerun()
    with right:
        if st.button("Cancel", key="cancel_delete_conversation"):
            st.session_state.pending_delete_conversation_id = None
            st.rerun()


def _date_group(updated_at: datetime) -> str:
    day = (updated_at.date() if isinstance(updated_at, datetime) else date.today())
    today = date.today()
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    if day >= today - timedelta(days=7):
        return "Previous 7 days"
    return "Older"


def render_history_sidebar(user: dict | None, guest_mode: bool = False, show_history: bool = True,
                          cookie_manager=None):
    st.markdown(
        """
<style>
div[class*="st-key-history_chat_"] button { background:rgba(255,255,255,.09)!important;
  border-color:rgba(255,255,255,.13)!important; color:#f7f8ff!important; }
div[class*="st-key-history_chat_"] button p { color:#f7f8ff!important; }
div[class*="st-key-history_chat_active_"] button { background:rgba(132,119,255,.28)!important;
  border-color:rgba(197,190,255,.48)!important; color:#fff!important; }
div[class*="st-key-history_chat_active_"] button p { color:#fff!important; }
div[class*="st-key-history_chat_"] button p { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
section[data-testid="stSidebar"] input { background:rgba(255,255,255,.09)!important;
  border-color:rgba(255,255,255,.18)!important; color:#fff!important; }
section[data-testid="stSidebar"] input::placeholder { color:rgba(255,255,255,.55)!important; }
div[class*="st-key-new_chat_button"] button { width:100%; color:white!important; border:0!important;
  background:linear-gradient(115deg,#4b45d6 0%,#7655e7 58%,#20a7b5 100%)!important; }
div[class*="st-key-profile_card"] [data-testid="stVerticalBlockBorderWrapper"] {
  background:rgba(255,255,255,.08)!important; border-color:rgba(255,255,255,.14)!important; }
.profile-line {display:flex; align-items:center; gap:10px;}
.profile-avatar {width:36px;height:36px;border-radius:50%;display:grid;place-items:center;
  background:linear-gradient(125deg,#4b45d6,#20a7b5);color:#fff;font-weight:700;flex:0 0 36px;}
.profile-meta {min-width:0;overflow-wrap:anywhere;color:#fff;}
.profile-meta small {color:rgba(255,255,255,.68)!important;}
</style>
""",
        unsafe_allow_html=True,
    )
    if show_history and st.button("＋  New chat", key="new_chat_button", type="primary", use_container_width=True):
        st.session_state.active_conversation_id = None
        st.session_state.loaded_conversation_id = None
        st.session_state.chat_history = []
        st.session_state.chat_feedback_votes = {}
        st.query_params.pop("chat", None)
        st.rerun()

    if show_history and user:
        previous_search = st.session_state.get("_last_chat_search", "")
        search = st.text_input("Search chats", placeholder="Search chats", key="chat_search")
        if search != previous_search:
            st.session_state.chat_list_offset = 0
            st.session_state._last_chat_search = search
        offset = int(st.session_state.get("chat_list_offset", 0))
        chats = db.list_conversations(user["id"], search=search, limit=offset + 20, offset=0)
        visible = chats
        active_id = st.session_state.get("active_conversation_id")
        if not visible:
            st.caption("No conversations yet." if not search else "No chats match that search.")
        else:
            groups = {"Pinned": [], "Today": [], "Yesterday": [], "Previous 7 days": [], "Older": []}
            for chat in visible:
                group = "Pinned" if chat["is_pinned"] else _date_group(chat["updated_at"])
                groups[group].append(chat)
            for group, items in groups.items():
                if not items:
                    continue
                st.caption(group)
                for chat in items:
                    chat_id = chat["id"]
                    row_key = f"history_chat_active_{chat_id}" if chat_id == active_id else f"history_chat_{chat_id}"
                    title = ("📌 " if chat["is_pinned"] else "") + (chat["title"] or "New chat")
                    with st.container(key=row_key):
                        title_col, menu_col = st.columns([5, 1], gap="small", vertical_alignment="center")
                        with title_col:
                            if st.button(title, key=f"open_chat_{chat_id}", use_container_width=True):
                                st.session_state.active_conversation_id = chat_id
                                st.session_state.loaded_conversation_id = None
                                st.query_params["chat"] = str(chat_id)
                                st.rerun()
                        with menu_col:
                            with st.popover("⋯", key=f"chat_menu_{chat_id}", use_container_width=True):
                                new_title = st.text_input(
                                    "Rename", value=chat["title"], key=f"rename_chat_text_{chat_id}"
                                )
                                if st.button("Save name", key=f"rename_chat_{chat_id}", use_container_width=True):
                                    if db.rename_conversation(chat_id, user["id"], new_title):
                                        st.rerun()
                                    st.error("Enter a title before saving.")
                                pinned_label = "Unpin" if chat["is_pinned"] else "Pin"
                                if st.button(pinned_label, key=f"pin_chat_{chat_id}", use_container_width=True):
                                    db.pin_conversation(chat_id, user["id"], not chat["is_pinned"])
                                    st.rerun()
                                if st.button("Delete…", key=f"delete_chat_{chat_id}", use_container_width=True):
                                    st.session_state.pending_delete_conversation_id = chat_id
                                    st.rerun()
        if len(chats) == offset + 20:
            if st.button("Show more", key="show_more_chats", use_container_width=True):
                st.session_state.chat_list_offset = offset + 20
                st.rerun()
        pending = st.session_state.get("pending_delete_conversation_id")
        if pending:
            _confirm_delete(pending, user["id"])
    elif show_history and guest_mode:
        st.info("Guest mode: sign in to save your history", icon=":material/info:")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.divider()
    if user:
        display_name = escape(str(user.get("display_name") or user.get("username") or "User"))
        username = escape(str(user.get("username") or ""))
        initials = escape("".join(part[0] for part in str(user.get("display_name") or user.get("username") or "U").split()[:2]).upper())
        st.markdown(
            f'<div class="profile-line"><div class="profile-avatar">{initials}</div>'
            f'<div class="profile-meta"><strong>{display_name}</strong><br><small>@{username}</small></div></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Signed in as {username}")
        if not st.session_state.get("auth_cookie_available", False):
            st.caption("Session-only login · cookies unavailable")
        if st.button("Log out", key="sidebar_logout", use_container_width=True):
            from ui.auth_ui import logout
            logout(cookie_manager)
    elif guest_mode:
        st.caption("Guest session · chats are not saved")
        if st.button("Log in or sign up", key="guest_to_auth", use_container_width=True):
            st.session_state.guest_mode = False
            st.session_state.pop("guest_session_id", None)
            st.session_state.chat_history = []
            st.rerun()

