# AI-Based Chatbot using Natural Language Processing (NLP)

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-red)](https://streamlit.io/)
[![NLTK](https://img.shields.io/badge/NLTK-3.8+-green)](https://www.nltk.org/)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.3+-orange)](https://scikit-learn.org/)

A comprehensive, modular AI chatbot platform combining real **NLTK text preprocessing**, **machine learning intent classification**, **VADER sentiment analysis**, **context management**, **document Q&A**, and **SQLite analytics**.

---

## 🔧 Prerequisites

- Python 3.10+
- Git (optional)

---

## 🚀 Installation & Setup

```powershell
# 1. Install all dependencies
pip install -r requirements.txt

# 2. Launch the app
streamlit run app.py
```

The chatbot uses local intent and FAQ data and does not require an API key or internet connection at runtime. NLTK uses installed local resources when available and offline fallbacks otherwise.

To compare word-only and combined word/character TF-IDF features, evaluate the classifiers
with a grouped stratified holdout and cross-validation, tune the fallback threshold, and save
the selected serving model, run:

```powershell
py train_pro_model.py
```

Responses are limited to the trained intent responses, bundled FAQ, and documents uploaded in the current session. The intent data includes dedicated examples for text preprocessing, tokenization, stemming, lemmatization, stop-word removal, POS tagging, and TF-IDF. Add verified examples and answers to the data files to expand the assistant's coverage.

---

## 📁 Project Structure

```
ML project/
├── app.py                         # Streamlit entry point
├── requirements.txt               # All dependencies
├── run_tests.py                   # Automated test runner
│
├── data/
│   ├── intents.json               # 30+ ML training intents
│   ├── knowledge_base.json        # Structured FAQ database
│   └── sample_documents/
│       └── sample_college_guide.txt
│
├── models/                        # Saved ML model artifacts (.pkl)
│
├── src/
│   ├── utilities.py               # Offline NLTK resource checks, path helpers
│   ├── preprocessing.py           # Full NLTK text pipeline
│   ├── nltk_explainer.py          # Educational stage explanations
│   ├── intent_classifier.py       # TF-IDF + ML classification
│   ├── sentiment_analyzer.py      # VADER sentiment engine
│   ├── context_manager.py         # Context memory & coreference
│   ├── knowledge_base.py          # FAQ lookup API
│   ├── document_qa.py             # PDF/DOCX/TXT cosine similarity Q&A
│   ├── response_generator.py      # Response strategy engine
│   ├── chatbot_engine.py          # Master orchestrator
│   ├── database.py                # SQLite ORM (SQLAlchemy)
│   └── analytics_engine.py        # Aggregations for Plotly charts
│
├── ui/
│   ├── home_ui.py                 # Landing page
│   ├── chat_ui.py                 # Core AI chat interface
│   ├── nltk_ui.py                 # Interactive NLTK Lab
│   ├── document_ui.py             # Document Q&A upload interface
│   ├── knowledge_ui.py            # KB browse & add
│   ├── analytics_ui.py            # Plotly analytics dashboard
│   ├── training_ui.py             # Multi-model comparison & training
│   ├── admin_ui.py                # Unknown query admin panel
│   ├── settings_ui.py             # Settings & config
│   ├── about_ui.py                # Project about page
│   ├── modules_ui.py              # 5-module academic mapping
│   └── review_demo_ui.py          # Faculty review demo mode
│
├── database/
│   └── chatbot.db                 # SQLite conversation store (auto-created)
│
└── tests/
    ├── test_preprocessing.py      # 5 NLP tests
    ├── test_intent.py             # 4 ML classifier tests
    └── test_chatbot.py            # 4 integration tests
```

---

## 🧠 NLP Pipeline (Module 1)

Each user query is processed through the following NLTK stages:

| Stage | NLTK Method | Purpose |
|-------|-------------|---------|
| Sentence Tokenization | `sent_tokenize()` | Split text into sentences |
| Word Tokenization | `word_tokenize()` | Split into individual tokens |
| Stopword Removal | `stopwords.words('english')` | Remove common non-informative words |
| POS Tagging | `pos_tag()` | Assign grammatical tags |
| Lemmatization | `WordNetLemmatizer()` | Reduce to dictionary base form |
| Stemming | `PorterStemmer()` | Aggressively reduce word suffix |
| NER | `ne_chunk()` | Extract named entities |

---

## 🤖 ML Intent Classification (Module 2)

| Algorithm | Library | Vectorizer |
|-----------|---------|------------|
| Multinomial Naive Bayes | `sklearn.naive_bayes` | TF-IDF (1-2 ngrams) |
| Logistic Regression | `sklearn.linear_model` | TF-IDF (1-2 ngrams) |
| Linear SVM | `sklearn.svm.SVC` | TF-IDF (1-2 ngrams) |

**Evaluation Metrics:** Accuracy, Precision, Recall, F1-Score, Confusion Matrix (Plotly heatmap)

---

## 📊 UI Pages Available

| Page | Description |
|------|-------------|
| 🏠 Home | Platform overview & feature cards |
| 💬 AI Chat | Natural language conversation with intent badge & feedback |
| 🧠 NLTK Lab | Step-by-step pipeline visualizer for each NLP stage |
| 📄 Document Q&A | Upload PDF/DOCX/TXT, query with cosine similarity |
| 📚 Knowledge Base | Browse FAQs, add new entries dynamically |
| 📊 Analytics | Plotly charts: intent distribution, sentiment trends |
| 🤖 Model Training | Multi-algorithm benchmark comparison + confusion matrix |
| 👨‍💻 Admin Panel | View unknown queries, map to intents, trigger retrain |
| ⚙️ Settings | Threshold sliders, context reset |
| ℹ️ About | Project overview & technology stack |
| 🏛️ 5 Core Modules | Official academic architecture mapping |
| 🎓 Review Demo | One-click demo suite for faculty evaluation |

---

## 🧪 Running Tests

```powershell
py run_tests.py
```

**Expected:** `Ran 13 tests — OK`

---

## 📚 Key Academic Differentiators

- ✅ **Real ML, NOT rule-based**: TF-IDF + probabilistic classifiers with confidence thresholds
- ✅ **Real NLTK pipeline**: Tokenization, POS tagging, lemmatization, NER — not mock methods
- ✅ **Context memory**: Tracks active subject (e.g. "Python") and resolves pronouns ("it", "this")
- ✅ **Document Intelligence**: TF-IDF cosine similarity Q&A from uploaded documents
- ✅ **Persistent storage**: SQLite via SQLAlchemy ORM
- ✅ **Continuous learning**: Unknown queries logged → admin maps to intent → model retrained

---

## Accounts, chat history, and privacy

Registered users have separate, persistent conversation history. The first non-legacy account
created is assigned the `admin` role automatically. To make additional accounts administrators,
create `.streamlit/secrets.toml` locally and add their usernames:

```toml
admin_usernames = ["another_admin"]
cookie_name = "nlp_chat_auth"
```

The `admin_usernames` setting is optional. Add `.streamlit/secrets.toml` to your deployment's
secret store as well as keeping it out of source control; `.gitignore` already excludes this file.
There is no hard-coded signing secret: remember-me cookies contain a random bearer token and the
database stores only its SHA-256 hash. Passwords are stored as bcrypt hashes. If the cookie
component is missing or blocked, sign-in still works for the current browser tab and the page
explains that refresh will require logging in again.

On startup, the SQLite migration checks the current schema and adds the account, ownership, and
message metadata columns without replacing existing tables. Before applying a required migration,
it creates a timestamped `database/chatbot.pre_auth_backup_*.db` snapshot. Existing conversations
and messages are assigned to an internal legacy guest owner and are hidden from newly registered
accounts. The database and migration backups are ignored by Git.

Guests can try the chat without an account, but their chats are not saved. Signed-in accounts can
search, reopen, rename, pin, and soft-delete their own conversations. Analytics is scoped to the
signed-in user; admins can opt into aggregate all-user metrics. Uploaded-document indexes and
coreference memory are isolated by user or guest browser session.
