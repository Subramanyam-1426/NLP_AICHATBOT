import re
import string
from collections import Counter
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import sent_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tag import pos_tag
from nltk import ne_chunk

from src.utilities import initialize_nltk

# Check local resources only; never download during app startup.
initialize_nltk()

_FALLBACK_STOP_WORDS = set("""a about above after again against all am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not of off on once only or other our ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they this those through to too under until up very was we were what when where which while who whom why will with would you your yours yourself yourselves""".split())

class TextPreprocessor:
    """
    Comprehensive Text Preprocessing Module using NLTK and standard NLP pipelines.
    Supports lowercasing, tokenization, stopword removal, POS tagging,
    WordNet lemmatization, Porter stemming, NER, and detailed pipeline extraction.
    """
    def __init__(self):
        try:
            self.stop_words = set(stopwords.words("english"))
        except LookupError:
            self.stop_words = _FALLBACK_STOP_WORDS
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()

    def clean_text(self, text: str) -> str:
        """Clean raw text by removing URLs, numbers, special characters, extra whitespace."""
        if not text:
            return ""
        text = text.lower()
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        # Keep letters, numbers, and basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def tokenize_sentences(self, text: str) -> list:
        """Sentence tokenization using NLTK."""
        if not text:
            return []
        try:
            return sent_tokenize(text)
        except LookupError:
            return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]

    def tokenize_words(self, text: str) -> list:
        """Word tokenization using NLTK."""
        if not text:
            return []
        cleaned = self.clean_text(text)
        return re.findall(r"[a-zA-Z0-9]+", cleaned)

    def remove_stopwords(self, tokens: list) -> list:
        """Filter out standard English stopwords."""
        return [token for token in tokens if token.lower() not in self.stop_words and len(token) > 1]

    def _get_wordnet_pos(self, treebank_tag: str):
        """Map Treebank POS tag to WordNet POS tag for accurate lemmatization."""
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN

    def pos_tagging(self, tokens: list) -> list:
        """Perform Part-Of-Speech Tagging on token list."""
        if not tokens:
            return []
        try:
            return pos_tag(tokens)
        except LookupError:
            return [(token, "NN") for token in tokens]

    def lemmatize_tokens(self, tokens: list) -> list:
        """Lemmatize tokens using WordNet and POS tags."""
        tagged = self.pos_tagging(tokens)
        lemmas = []
        for token, tag in tagged:
            wn_pos = self._get_wordnet_pos(tag)
            try:
                lemmas.append(self.lemmatizer.lemmatize(token, pos=wn_pos))
            except LookupError:
                lemmas.append(token)
        return lemmas

    def stem_tokens(self, tokens: list) -> list:
        """Stem tokens using PorterStemmer."""
        return [self.stemmer.stem(token) for token in tokens]

    def extract_entities(self, text: str) -> list:
        """Extract Named Entities using NLTK ne_chunk with fallback."""
        if not text:
            return []
        try:
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            chunks = ne_chunk(tagged)
            entities = []
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    entity_name = " ".join(c[0] for c in chunk)
                    entity_label = chunk.label()
                    entities.append((entity_name, entity_label))
            return entities
        except Exception:
            # Safe fallback for capitalized entities
            caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            return [(cap, "ORGANIZATION") for cap in set(caps)]

    def preprocess_for_vectorizer(self, text: str) -> str:
        """
        Complete processing sequence returning space-separated clean lemmas
        ready for TF-IDF Vectorization.
        """
        raw_words = self.tokenize_words(text)
        non_stop = self.remove_stopwords(raw_words)
        lemmas = self.lemmatize_tokens(non_stop)
        return " ".join(lemmas)

    def get_full_nlp_pipeline_details(self, text: str) -> dict:
        """
        Detailed stage-by-stage dictionary output used in NLTK Educational Lab UI.
        """
        raw_sentences = self.tokenize_sentences(text)
        cleaned_text = self.clean_text(text)
        raw_words = self.tokenize_words(cleaned_text)
        filtered_words = self.remove_stopwords(raw_words)
        pos_tags = self.pos_tagging(filtered_words)
        lemmas = self.lemmatize_tokens(filtered_words)
        stems = self.stem_tokens(filtered_words)
        entities = self.extract_entities(text)
        freq_dist = dict(Counter(filtered_words).most_common(10))

        return {
            "original_text": text,
            "raw_sentences": raw_sentences,
            "cleaned_text": cleaned_text,
            "raw_tokens": raw_words,
            "filtered_tokens": filtered_words,
            "pos_tags": pos_tags,
            "lemmas": lemmas,
            "stems": stems,
            "named_entities": entities,
            "frequency_distribution": freq_dist,
            "final_processed_string": " ".join(lemmas)
        }

# Global singleton instance for easy import
preprocessor = TextPreprocessor()
