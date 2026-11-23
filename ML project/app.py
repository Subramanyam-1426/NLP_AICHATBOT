import streamlit as st

st.set_page_config(
    page_title="AI assistant",
    page_icon=":material/smart_toy:",
    layout="wide",
    initial_sidebar_state="auto",
)

from src.intent_classifier import intent_classifier
from src.database import db
from ui.theme import inject_theme
from ui.auth_ui import cookie_manager, restore_login, render_auth_page
from ui.history_sidebar import render_history_sidebar
from ui.history_page import render_history_page
from ui.home_ui import render_home
from ui.chat_ui import render_chat
from ui.nltk_ui import render_nltk_lab
from ui.document_ui import render_document_qa
from ui.analytics_ui import render_analytics
from ui.training_ui import render_model_training
from ui.review_demo_ui import render_review_demo


st.session_state.setdefault("dark_mode", False)
inject_theme(st.session_state.dark_mode)

# The cookie component may be absent in restricted/browserless environments. Auth
# remains usable for the current tab, and the login page reports the fallback.
manager = cookie_manager()
restore_login(manager)
user = st.session_state.get("user")
guest_mode = bool(st.session_state.get("guest_mode"))

if not user and not guest_mode:
    render_auth_page(manager)
    st.stop()

st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("chat_feedback_votes", {})
st.session_state.setdefault("active_conversation_id", None)

# The URL keeps the selected conversation stable across refreshes. Ownership is
# checked here before it can influence the active chat state.
if user:
    raw_chat_id = st.query_params.get("chat")
    if raw_chat_id:
        try:
            url_chat_id = int(raw_chat_id)
        except (TypeError, ValueError):
            url_chat_id = None
        if url_chat_id and db.get_conversation(url_chat_id, user["id"]):
            if st.session_state.get("active_conversation_id") != url_chat_id:
                st.session_state.active_conversation_id = url_chat_id
                st.session_state.loaded_conversation_id = None
        elif url_chat_id:
            st.query_params.pop("chat", None)
            st.session_state.active_conversation_id = None

nav_icons = {
    "Home": "home",
    "Chat": "chat",
    "Chat history": "history",
    "NLTK Lab": "psychology",
    "Document Q&A": "description",
    "Analytics": "monitoring",
    "Model Training": "model_training",
    "Demo Mode": "slideshow",
}
nav_options = list(nav_icons)

with st.sidebar:
    st.markdown("## :material/auto_awesome: AI assistant")
    st.caption("Questions · NLP · Writing")
    st.markdown("**:material/contrast: Appearance**")
    st.toggle(
        "Dark mode",
        key="dark_mode",
        help="Switch between the light and dark appearance.",
        label_visibility="visible",
    )
    st.divider()

    nav_target = st.session_state.pop("_nav_page", None)
    if nav_target in nav_options:
        st.session_state["_radio_nav"] = nav_target
    st.session_state.setdefault("_radio_nav", "Chat")
    page = st.radio(
        "Navigation",
        nav_options,
        key="_radio_nav",
        format_func=lambda label: f":material/{nav_icons[label]}:  {label}",
        label_visibility="collapsed",
    )
    model_name = intent_classifier.model_name or "Not trained"
    accuracy = intent_classifier.metrics.get("accuracy")
    accuracy_label = f"{accuracy:.0%}" if accuracy is not None else "Not available"
    st.markdown(
        f"""
<div class="sidebar-footer">
  <strong>AI assistant · v1.0.0</strong>
  <span>Model: {model_name}</span>
  <span>Held-out accuracy: {accuracy_label}</span>
</div>
""",
        unsafe_allow_html=True,
    )
    render_history_sidebar(user, guest_mode, show_history=(page == "Chat"), cookie_manager=manager)

if page == "Home":
    render_home()
elif page == "Chat":
    render_chat()
elif page == "Chat history":
    render_history_page(user, guest_mode)
elif page == "NLTK Lab":
    render_nltk_lab()
elif page == "Document Q&A":
    render_document_qa()
elif page == "Analytics":
    render_analytics()
elif page == "Model Training":
    render_model_training()
elif page == "Demo Mode":
    render_review_demo()
