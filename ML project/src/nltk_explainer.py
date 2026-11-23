class NLTKExplainer:
    """
    Provides academic & educational descriptions for NLTK text preprocessing stages.
    """
    @staticmethod
    def get_stage_explanation(stage_name: str) -> dict:
        explanations = {
            "tokenization": {
                "title": "Sentence & Word Tokenization",
                "definition": "Tokenization is the process of breaking raw text strings into smaller meaningful units called tokens (words, punctuation marks, or sentences).",
                "nltk_method": "nltk.tokenize.sent_tokenize() & nltk.tokenize.word_tokenize()",
                "academic_relevance": "Tokenization forms the foundational building block for all downstream NLP tasks, enabling mathematical analysis of discrete language units."
            },
            "stopwords": {
                "title": "Stopword Filtering",
                "definition": "Stopwords are extremely common words (e.g., 'the', 'is', 'at', 'which') that carry little unique semantic meaning or domain specificity.",
                "nltk_method": "nltk.corpus.stopwords.words('english')",
                "academic_relevance": "Removing non-informative stopwords reduces dataset dimensionality and prevents frequent function words from distorting TF-IDF feature weights."
            },
            "pos_tagging": {
                "title": "Part-Of-Speech (POS) Tagging",
                "definition": "POS Tagging assigns grammatical categories (Noun, Verb, Adjective, Adverb, etc.) to each token based on both its definition and context.",
                "nltk_method": "nltk.pos_tag() using Penn Treebank tagset",
                "academic_relevance": "POS tags provide crucial syntactic context required for accurate POS-aware lemmatization and Named Entity Recognition."
            },
            "lemmatization": {
                "title": "WordNet Lemmatization",
                "definition": "Lemmatization uses vocabulary and morphological analysis to return the dictionary base form (lemma) of a word (e.g., 'running' -> 'run', 'better' -> 'good').",
                "nltk_method": "nltk.stem.WordNetLemmatizer()",
                "academic_relevance": "Unlike crude stemming, lemmatization preserves valid dictionary words and canonical semantic meanings."
            },
            "stemming": {
                "title": "Porter Stemming",
                "definition": "Stemming applies heuristic rules to slice off word suffixes to reduce words to their stem (e.g., 'studies' -> 'studi').",
                "nltk_method": "nltk.stem.PorterStemmer()",
                "academic_relevance": "Stemming is computationally fast and aggressive, though it occasionally produces non-words."
            },
            "ner": {
                "title": "Named Entity Recognition (NER)",
                "definition": "NER identifies and classifies real-world named entities (e.g., Persons, Organizations, Locations) present in unstructured text.",
                "nltk_method": "nltk.ne_chunk(nltk.pos_tag(tokens))",
                "academic_relevance": "Extracting key entities assists in intent detection, question answering, and knowledge extraction."
            }
        }
        return explanations.get(stage_name.lower(), {
            "title": stage_name,
            "definition": "Standard NLTK Natural Language Processing step.",
            "nltk_method": "nltk library function",
            "academic_relevance": "Transforms unstructured text into structured representations."
        })

explainer = NLTKExplainer()
