import streamlit as st
import pandas as pd
from src.knowledge_base import knowledge_base

def render_knowledge_base():
    st.markdown("### 📚 Knowledge Base")
    st.caption("Browse FAQs and institute data, or add new entries.")

    tab1, tab2 = st.tabs(["Browse FAQs", "Add New FAQ"])

    with tab1:
        if knowledge_base.college_meta:
            m = knowledge_base.college_meta
            c1, c2, c3 = st.columns(3)
            c1.metric("College", m.get("name", "N/A"))
            c2.metric("Accreditation", m.get("accreditation", "N/A"))
            c3.metric("Established", m.get("established", "N/A"))
            st.markdown("---")

        if knowledge_base.faqs:
            df = pd.DataFrame(knowledge_base.faqs)
            st.dataframe(df[["id", "category", "question", "answer"]], use_container_width=True)
        else:
            st.info("Knowledge Base is empty.")

    with tab2:
        category = st.selectbox("Category", ["Admissions", "Academics", "Placements", "NLP & AI", "Infrastructure", "General"])
        question = st.text_input("Question")
        answer = st.text_area("Answer")

        if st.button("Save FAQ"):
            if question and answer:
                knowledge_base.add_faq(category, question, answer)
                st.success("FAQ added!")
                st.rerun()
            else:
                st.error("Please fill in both Question and Answer.")
