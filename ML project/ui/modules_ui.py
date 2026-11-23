import streamlit as st

def render_modules():
    st.markdown("### 🏛️ 5 Core Academic Modules")
    st.caption("Software engineering module breakdown for project review.")

    modules = [
        {
            "title": "Module 1 — Text Preprocessing Engine",
            "file": "src/preprocessing.py",
            "desc": "Lowercasing, regex cleaning, NLTK tokenization, stopword removal, POS tagging, WordNet lemmatization, Porter stemming, NER.",
            "key_classes": "`TextPreprocessor` · `clean_text()` · `tokenize_words()` · `lemmatize_tokens()` · `get_full_nlp_pipeline_details()`"
        },
        {
            "title": "Module 2 — ML Intent Classifier",
            "file": "src/intent_classifier.py",
            "desc": "TF-IDF feature extraction (n-grams 1–2), multi-model training (MultinomialNB, LogisticRegression, SVM), Accuracy/F1/Confusion Matrix.",
            "key_classes": "`IntentClassifier` · `train()` · `predict_intent()` · `compare_all_models()`"
        },
        {
            "title": "Module 3 — Response Generator",
            "file": "src/response_generator.py",
            "desc": "Intent-based response mapping, sentiment-aware prefix/suffix adjustments, document snippet citation formatting.",
            "key_classes": "`ResponseGenerator` · `generate_response()`"
        },
        {
            "title": "Module 4 — Context & Memory Manager",
            "file": "src/context_manager.py",
            "desc": "Conversational turn tracking, target subject extraction, pronoun coreference resolution ('tell me about it').",
            "key_classes": "`ContextManager` · `update_context()` · `resolve_coreference()`"
        },
        {
            "title": "Module 5 — Sentiment & Analytics Engine",
            "file": "src/sentiment_analyzer.py · src/analytics_engine.py · src/database.py",
            "desc": "VADER sentiment scoring, SQLite message/prediction/feedback storage, Plotly analytics aggregations.",
            "key_classes": "`SentimentAnalyzer` · `DatabaseManager` · `AnalyticsEngine`"
        },
    ]

    for mod in modules:
        with st.expander(mod["title"], expanded=False):
            st.caption(f"📁 `{mod['file']}`")
            st.write(mod["desc"])
            st.markdown(f"**Key classes/functions:** {mod['key_classes']}")
