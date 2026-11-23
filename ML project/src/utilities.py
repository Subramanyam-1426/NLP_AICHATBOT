import os
import nltk

def initialize_nltk():
    """
    Check for local NLTK resources without attempting network downloads.
    """
    resources = {
        "punkt": "tokenizers/punkt",
        "stopwords": "corpora/stopwords",
        "wordnet": "corpora/wordnet",
        "averaged_perceptron_tagger": "taggers/averaged_perceptron_tagger",
        "vader_lexicon": "sentiment/vader_lexicon.zip",
        "maxent_ne_chunker": "chunkers/maxent_ne_chunker",
        "words": "corpora/words",
        "omw-1.4": "corpora/omw-1.4"
    }
    missing = []
    for package, resource in resources.items():
        try:
            nltk.data.find(resource)
        except LookupError:
            missing.append(package)
    return missing

def get_project_root():
    """
    Returns absolute path to project root.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_path(filename):
    """
    Returns absolute path to a file inside the data/ folder.
    """
    return os.path.join(get_project_root(), "data", filename)

def get_model_path(filename):
    """
    Returns absolute path to a file inside the models/ folder.
    """
    os.makedirs(os.path.join(get_project_root(), "models"), exist_ok=True)
    return os.path.join(get_project_root(), "models", filename)

def get_db_path():
    """
    Returns absolute path to SQLite database file.
    """
    override = os.environ.get("CHATBOT_DB_PATH")
    if override:
        return os.path.abspath(os.path.expanduser(override))
    db_dir = os.path.join(get_project_root(), "database")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "chatbot.db")
