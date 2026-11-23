"""Account creation, login, remember-me cookies, and guest access."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
import re
import uuid

import streamlit as st

from src.database import db

try:
    from extra_streamlit_components.CookieManager import CookieManager
except ImportError:  # Session-only login remains available if the optional browser component is missing.
    CookieManager = None


COOKIE_NAME = "nlp_chat_auth"


def _secret(name: str, fallback=None):
    try:
        return st.secrets.get(name, fallback)
    except Exception:
        return fallback


def _cookie_name() -> str:
    return str(_secret("cookie_name", COOKIE_NAME) or COOKIE_NAME)


def cookie_manager():
    if CookieManager is None:
        return None
    try:
        return CookieManager(key="nlp_auth_cookie_manager")
    except Exception:
        logging.getLogger(__name__).warning("Cookie manager component could not initialize.", exc_info=True)
        return None


def restore_login(manager=None) -> None:
    """Restore a user from the browser's opaque, database-backed token."""
    if st.session_state.get("user") or st.session_state.get("guest_mode"):
        return
    manager = manager if manager is not None else cookie_manager()
    st.session_state.auth_cookie_available = manager is not None
    if manager is None:
        return
    try:
        token = manager.get(cookie=_cookie_name())
    except Exception:
        st.session_state.auth_cookie_available = False
        return
    if not token:
        return
    user = db.get_user_by_token(token)
    if user:
        st.session_state.user = user
        st.session_state.auth_token = token
    else:
        try:
            manager.delete(_cookie_name(), key="clear_expired_auth_cookie")
        except Exception:
            pass


def _start_session(user: dict, manager=None):
    st.session_state.user = user
    st.session_state.guest_mode = False
    st.session_state.pop("guest_session_id", None)
    st.session_state.active_conversation_id = None
    st.session_state.chat_history = []
    st.session_state.chat_feedback_votes = {}
    st.session_state._radio_nav = "Chat"
    st.session_state._nav_page = "Chat"
    try:
        st.query_params.clear()
    except Exception:
        pass
    manager = manager if manager is not None else cookie_manager()
    st.session_state.auth_cookie_available = manager is not None
    if manager is None:
        st.session_state.pop("auth_token", None)
        return False
    try:
        token = db.create_auth_token(user["id"], expires_in_days=30)
        manager.set(
            cookie=_cookie_name(),
            val=token,
            key="set_remember_me_cookie",
            path="/",
            expires_at=datetime.now() + timedelta(days=30),
            same_site="lax",
        )
        st.session_state.auth_token = token
        return True
    except Exception:
        logging.getLogger(__name__).warning("Remember-me cookie could not be stored; using session-only login.", exc_info=True)
        # The authenticated session continues until its browser tab closes.
        st.session_state.auth_cookie_available = False
        st.session_state.pop("auth_token", None)
        return False


def logout(manager=None):
    token = st.session_state.get("auth_token")
    if token:
        db.revoke_token(token)
    manager = manager if manager is not None else cookie_manager()
    cookie_delete_pending = False
    if manager is not None:
        try:
            manager.delete(_cookie_name(), key="logout_auth_cookie")
            cookie_delete_pending = True
        except Exception:
            pass
    dark_mode = st.session_state.get("dark_mode", False)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.dark_mode = dark_mode
    st.query_params.clear()
    if not cookie_delete_pending:
        st.rerun()


def _validate_signup(name: str, username: str, email: str, password: str,
                     confirmation: str) -> dict[str, str]:
    errors = {}
    if not name.strip():
        errors["name"] = "Enter your name."
    if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username.strip()):
        errors["username"] = "Use 3–30 letters, numbers, or underscores."
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
        errors["email"] = "Enter a valid email address."
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        errors["password"] = "Use at least 8 characters with a letter and a number."
    if password != confirmation:
        errors["confirmation"] = "Passwords do not match."
    return errors


def render_auth_page(manager=None):
    manager = manager if manager is not None else cookie_manager()
    st.markdown(
        """
<style>
.stApp { background: radial-gradient(ellipse at 18% 5%, rgba(32,167,181,.18), transparent 42%),
  radial-gradient(ellipse at 88% 94%, rgba(117,88,232,.22), transparent 46%), var(--app-bg) !important; }
[data-testid="stAppViewBlockContainer"] { max-width: 1050px !important; padding-top: clamp(2rem, 8vh, 5rem) !important; }
div[class*="st-key-auth_card"] [data-testid="stVerticalBlockBorderWrapper"] {
  padding: clamp(1.1rem, 4vw, 2.5rem) !important; border-radius: 22px !important;
  border: 1px solid color-mix(in srgb, var(--accent) 20%, var(--border)) !important;
  box-shadow: 0 24px 70px rgba(29,40,73,.15) !important; background: var(--surface) !important;
}
.auth-brand { text-align:center; margin: .2rem 0 1.2rem; }
.auth-brand h1 { font-size: clamp(1.75rem, 4vw, 2.25rem); margin: .3rem 0; }
.auth-brand p { color: var(--muted); margin: 0; }
div[class*="st-key-auth_card"] [data-testid="stFormSubmitButton"] button,
div[class*="st-key-auth_card"] [data-testid="stButton"] button[kind="primary"] {
  background: var(--accent-gradient) !important; color: white !important; border: 0 !important;
}
@media(max-width:700px) { [data-testid="stAppViewBlockContainer"] { padding: 1rem .7rem 2rem !important; } }
</style>
""",
        unsafe_allow_html=True,
    )
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.container(border=True, key="auth_card"):
            st.markdown(
                '<div class="auth-brand"><div>✨</div><h1>Welcome to your AI workspace</h1>'
                '<p>Sign in to continue your conversations across devices.</p></div>',
                unsafe_allow_html=True,
            )
            login_tab, signup_tab = st.tabs(["Log in", "Sign up"])
            with login_tab:
                show_password = st.toggle("Show password", key="login_show_password")
                with st.form("login_form", clear_on_submit=False):
                    login = st.text_input("Username or email", key="login_identifier", autocomplete="username")
                    password = st.text_input(
                        "Password", type="default" if show_password else "password",
                        key="login_password", autocomplete="current-password",
                    )
                    remember = st.checkbox("Remember me for 30 days", value=True, key="remember_me")
                    submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
                if submitted:
                    user = db.verify_user(login, password)
                    if not user:
                        st.error("Invalid username or password")
                    else:
                        cookie_update_pending = _start_session(user, manager if remember else None)
                        if not remember and manager is not None:
                            st.session_state.auth_cookie_available = True
                        if not cookie_update_pending:
                            st.rerun()
            with signup_tab:
                show_password = st.toggle("Show password", key="signup_show_password")
                with st.form("signup_form", clear_on_submit=False):
                    name = st.text_input("Name", key="signup_name", autocomplete="name")
                    username = st.text_input("Username", key="signup_username", autocomplete="username")
                    email = st.text_input("Email", key="signup_email", autocomplete="email")
                    password = st.text_input(
                        "Password", type="default" if show_password else "password",
                        key="signup_password", autocomplete="new-password",
                    )
                    confirmation = st.text_input(
                        "Confirm password", type="default" if show_password else "password",
                        key="signup_confirm", autocomplete="new-password",
                    )
                    remember = st.checkbox("Remember me for 30 days", value=True, key="signup_remember_me")
                    submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
                if submitted:
                    errors = _validate_signup(name, username, email, password, confirmation)
                    if errors:
                        for field in ("name", "username", "email", "password", "confirmation"):
                            if field in errors:
                                st.error(errors[field])
                    else:
                        admins = _secret("admin_usernames", []) or []
                        is_admin = username.strip().lower() in {str(item).lower() for item in admins}
                        try:
                            user = db.create_user(
                                username=username,
                                email=email,
                                password=password,
                                display_name=name,
                                role="admin" if is_admin else None,
                            )
                        except ValueError as error:
                            st.error(str(error))
                        else:
                            cookie_update_pending = _start_session(user, manager if remember else None)
                            if not remember and manager is not None:
                                st.session_state.auth_cookie_available = True
                            if not cookie_update_pending:
                                st.rerun()
            if not st.session_state.get("auth_cookie_available", manager is not None):
                st.info("Cookies are unavailable. You can use the app in this tab, but you’ll need to log in again after refresh.")
            st.divider()
            if st.button("Continue as guest", key="continue_as_guest", use_container_width=True):
                st.session_state.guest_mode = True
                st.session_state.user = None
                st.session_state.guest_session_id = str(uuid.uuid4())
                st.session_state.active_conversation_id = None
                st.session_state.chat_history = []
                st.session_state._radio_nav = "Chat"
                st.session_state._nav_page = "Chat"
                st.rerun()

