import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.preprocessing import preprocessor
from src.utilities import get_data_path

class KnowledgeBaseEngine:
    """
    Structured Knowledge Base Lookup & Management API.
    Loads FAQs and college metadata from json, supports vector similarity search over questions.
    """
    def __init__(self):
        self.faqs = []
        self.base_faqs = []
        self.college_meta = {}
        self.vectorizer = None
        self.faq_vectors = None
        self.faq_pattern_lookup = {}
        self.load_kb()

    def load_kb(self, filepath=None):
        """Load Knowledge Base dataset."""
        self.faqs = []
        self.college_meta = {}
        if not filepath:
            filepath = get_data_path("knowledge_base.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.base_faqs = data.get("faqs", [])
                self.college_meta = data.get("college_meta", {})
        self.faqs = list(self.base_faqs)

        intent_path = get_data_path("intents.json")
        if os.path.exists(intent_path):
            with open(intent_path, 'r', encoding='utf-8') as f:
                intent_data = json.load(f)
            next_id = len(self.faqs) + 1
            for intent in intent_data.get("intents", []):
                for qa_pair in intent.get("qa_pairs", []):
                    self.faqs.append({
                        "id": next_id,
                        "category": intent["tag"],
                        "question": qa_pair["question"],
                        "answer": qa_pair["answer"],
                        "patterns": qa_pair.get("patterns", [])
                    })
                    next_id += 1

                self._rebuild_search_index()

    def _rebuild_search_index(self):
        """Build the local FAQ search index once after data changes."""
        self.faq_pattern_lookup = {}
        if not self.faqs:
            self.vectorizer = None
            self.faq_vectors = None
            return

        processed_questions = []
        for index, faq in enumerate(self.faqs):
            candidates = [faq["question"], *faq.get("patterns", [])]
            processed_candidates = [
                preprocessor.preprocess_for_vectorizer(candidate)
                for candidate in candidates
            ]
            processed_candidates = [candidate for candidate in processed_candidates if candidate]
            for candidate in processed_candidates:
                self.faq_pattern_lookup[candidate] = index
            processed_questions.append(" ".join(processed_candidates))

        self.vectorizer = TfidfVectorizer().fit(processed_questions)
        self.faq_vectors = self.vectorizer.transform(processed_questions)

    def search_faq(self, query: str, score_threshold: float = 0.3) -> dict:
        """Find an exact local Q&A match or the nearest FAQ by TF-IDF similarity."""
        if not self.faqs or not self.vectorizer or not query.strip():
            return None

        processed_query = preprocessor.preprocess_for_vectorizer(query)
        if not processed_query:
            return None

        exact_index = self.faq_pattern_lookup.get(processed_query)
        if exact_index is not None:
            match = self.faqs[exact_index].copy()
            match["similarity_score"] = 1.0
            match["exact_match"] = True
            return match

        query_vec = self.vectorizer.transform([processed_query])
        similarities = cosine_similarity(query_vec, self.faq_vectors)[0]
        best_idx = similarities.argmax()
        best_score = float(similarities[best_idx])

        if best_score >= score_threshold:
            match = self.faqs[best_idx].copy()
            match["similarity_score"] = round(best_score, 4)
            match["exact_match"] = False
            return match

        return None

    def add_faq(self, category: str, question: str, answer: str) -> bool:
        """Add new FAQ item dynamically and save to json."""
        new_id = len(self.base_faqs) + 1
        new_item = {
            "id": new_id,
            "category": category,
            "question": question,
            "answer": answer
        }
        self.base_faqs.append(new_item)
        self.save_kb()
        self.load_kb()
        return True

    def save_kb(self, filepath=None):
        """Save Knowledge Base to disk."""
        if not filepath:
            filepath = get_data_path("knowledge_base.json")
        data = {
            "faqs": self.base_faqs,
            "college_meta": self.college_meta
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

knowledge_base = KnowledgeBaseEngine()
