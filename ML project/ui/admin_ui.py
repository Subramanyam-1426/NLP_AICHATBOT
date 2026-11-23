import streamlit as st
import pandas as pd
from src.database import db
from src.intent_classifier import intent_classifier

def render_admin():
    st.markdown("### 🛠️ Admin — Low Confidence Queries")
    st.caption("Queries where the model confidence was below threshold are logged here for review and retraining.")

    unknown_queries = db.get_unknown_queries()

    if not unknown_queries:
        st.info("No low-confidence queries logged yet.")
        return

    df = pd.DataFrame(unknown_queries)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.markdown("**Map Query to Intent & Retrain**")

    selected = st.selectbox("Select query:", [q["text"] for q in unknown_queries])
    intent   = st.selectbox("Assign intent:", intent_classifier.intent_tags)

    if st.button("Add & Retrain"):
        import json
        from src.utilities import get_data_path
        for item in intent_classifier.intents_data:
            if item["tag"] == intent:
                item["patterns"].append(selected)
                break
        with open(get_data_path("intents.json"), "w", encoding="utf-8") as f:
            json.dump({"intents": intent_classifier.intents_data}, f, indent=2)
        intent_classifier.train()
        st.success(f"Added '{selected}' → '{intent}' and retrained.")
        st.rerun()
