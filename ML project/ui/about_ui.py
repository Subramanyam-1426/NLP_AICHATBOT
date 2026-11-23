import streamlit as st

def render_about():
    st.markdown("### ℹ️ About This Project")

    st.markdown("""
**AI-Based Chatbot using Natural Language Processing**

A production-ready college project demonstrating real Machine Learning and NLP techniques — not rule-based logic.

---

**Technology Stack**

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| NLP | NLTK (tokenization, POS, lemmatization, NER) |
| ML | Scikit-Learn (TF-IDF, Naive Bayes, LR, SVM) |
| Sentiment | VADER (Valence Aware Dictionary) |
| Database | SQLite3 |
| UI | Streamlit + Plotly |
| Document Parsing | PyPDF2, python-docx |

---

**Key Differentiators**

1. **Real ML Classification** — TF-IDF features + probability thresholds, not keyword matching.
2. **Full NLP Pipeline** — Tokenization → POS → Lemmatization → NER, all visible.
3. **Context Awareness** — Pronoun coreference resolution across turns.
4. **Document Q&A** — TF-IDF cosine similarity over uploaded documents.
5. **Evaluation Metrics** — Accuracy, Precision, Recall, F1-Score, Confusion Matrix.
""")
