import streamlit as st
import pandas as pd
from src.preprocessing import preprocessor
from src.intent_classifier import intent_classifier
from src.sentiment_analyzer import sentiment_analyzer
from src.context_manager import context_manager
from src.document_qa import document_qa
from ui.theme import render_page_header

def render_review_demo():
    render_page_header(
        "Demo mode",
        "slideshow",
        "Run short examples across language processing, intent detection, sentiment, context, and documents.",
    )

    t1, t2, t3, t4, t5 = st.tabs([
        "NLP pipeline",
        "Intent",
        "Sentiment",
        "Context",
        "Document Q&A",
    ])

    with t1:
        st.subheader("Text processing", icon=":material/psychology:")
        text = st.text_input(
            "Input text",
            "The students are studying AI and Machine Learning in Python!",
            key="d_nlp"
        )
        if st.button("Run example", key="btn_nlp", icon=":material/play_arrow:", type="primary"):
            with st.status("Processing text", expanded=False):
                st.session_state.demo_nlp_result = preprocessor.get_full_nlp_pipeline_details(text)
        if result := st.session_state.get("demo_nlp_result"):
            st.markdown("**Word tokens**")
            _render_chips(result["raw_tokens"])
            st.markdown("**Filtered tokens**")
            _render_chips(result["filtered_tokens"])
            st.markdown("**Part-of-speech tags**")
            with st.container(horizontal=True, gap="small"):
                for token, tag in result["pos_tags"][:8]:
                    st.badge(f"{token} · {tag}", color=_pos_color(tag))
            st.dataframe(
                pd.DataFrame({"Lemma": result["lemmas"]}),
                hide_index=True,
                width="stretch",
            )

    with t2:
        st.subheader("Intent classification", icon=":material/category:")
        query = st.text_input("Example question", "What is the fee structure for B.Tech CSE?", key="d_int")
        if st.button("Run example", key="btn_int", icon=":material/play_arrow:", type="primary"):
            st.session_state.demo_intent_result = intent_classifier.predict_intent(query)
        if result := st.session_state.get("demo_intent_result"):
            st.success(f"Intent: **{result['tag']}**")
            st.metric("Confidence", f"{result['confidence']:.1%}")
            st.dataframe(result["top_predictions"], hide_index=True, width="stretch")

    with t3:
        st.subheader("Sentiment analysis", icon=":material/mood:")
        sent = st.text_input("Input text", "I am extremely happy with the result!", key="d_sent")
        if st.button("Run example", key="btn_sent", icon=":material/play_arrow:", type="primary"):
            st.session_state.demo_sentiment_result = sentiment_analyzer.analyze(sent)
        if result := st.session_state.get("demo_sentiment_result"):
            st.success(f"{result['emoji']} **{result['sentiment']}**")
            polarity, positive, neutral, negative = st.columns(4)
            polarity.metric("Compound", f"{result['compound']:.2f}")
            positive.metric("Positive", f"{result['pos']:.0%}")
            neutral.metric("Neutral", f"{result['neu']:.0%}")
            negative.metric("Negative", f"{result['neg']:.0%}")
            st.progress(min(max((result["compound"] + 1) / 2, 0.0), 1.0), text="Sentiment polarity")

    with t4:
        st.subheader("Context resolution", icon=":material/link:")
        st.caption("Example: “Tell me about Python” followed by “Who created it?”")
        if st.button("Run example", key="btn_coref", icon=":material/play_arrow:", type="primary"):
            context_manager.reset()
            context_manager.update_context(
                "Tell me about Python", "python_info",
                "Python is a programming language", context_set="Python"
            )
            resolved, is_res, subj = context_manager.resolve_coreference("Who created it?")
            st.session_state.demo_context_result = {
                "resolved": resolved,
                "resolved_coreference": is_res,
                "subject": subj,
            }
        if result := st.session_state.get("demo_context_result"):
            st.success(f"Resolved query: **{result['resolved']}**")
            st.badge(
                f"Subject: {result['subject'] or 'not detected'}",
                icon=":material/link:",
                color="violet",
            )

    with t5:
        st.subheader("Document retrieval", icon=":material/find_in_page:")
        if st.button("Run example", key="btn_doc", icon=":material/play_arrow:", type="primary"):
            if not document_qa.indexed_chunks:
                import os
                p = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "data", "sample_documents", "sample_college_guide.txt"
                )
                if os.path.exists(p):
                    document_qa.process_document(p, source_name="sample_college_guide.txt")
            st.session_state.demo_document_result = document_qa.search_document(
                "placement statistics highest package",
                top_k=1,
            )
        results = st.session_state.get("demo_document_result")
        if results:
            match = results[0]
            st.metric("Top match", f"{match['score']:.1%}")
            st.write(match["raw_text"])
            st.caption(f"Source: {match['source']} · Page/paragraph {match['page']}")
        elif results is not None:
            st.warning("No matching document found.")


def _render_chips(values: list[str]) -> None:
    from html import escape

    if values:
        chips = " ".join(
            f'<span class="token-chip">{escape(str(value))}</span>'
            for value in values
        )
        st.markdown(chips, unsafe_allow_html=True)
    else:
        st.caption("No values to display.")


def _pos_color(tag: str) -> str:
    if tag.startswith("NN"):
        return "blue"
    if tag.startswith("VB"):
        return "green"
    if tag.startswith("JJ"):
        return "orange"
    if tag.startswith("RB"):
        return "violet"
    return "gray"
