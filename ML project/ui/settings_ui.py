import streamlit as st
from src.context_manager import context_manager

def render_settings():
    st.markdown("### ⚙️ Settings")

    st.markdown("**Intent Confidence Threshold**")
    threshold = st.slider(
        "Fallback threshold — queries below this confidence get logged to Admin:",
        min_value=0.10, max_value=0.80, value=0.35, step=0.05,
        format="%.0f%%"
    )
    st.caption(f"Currently: **{int(threshold * 100)}%**")

    st.markdown("---")
    st.markdown("**Context Memory**")
    st.write(f"Active subject: `{context_manager.target_subject or 'None'}`")
    st.write(f"Turns in memory: `{len(context_manager.history)}`")

    if st.button("Reset Context Memory"):
        context_manager.reset()
        st.success("Context cleared.")

    st.markdown("---")
    st.markdown("**Storage Paths**")
    st.caption("Database: `database/chatbot.db`  ·  Models: `models/`")
