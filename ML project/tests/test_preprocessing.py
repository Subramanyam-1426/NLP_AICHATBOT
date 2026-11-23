import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.preprocessing import preprocessor

class TestPreprocessing(unittest.TestCase):
    def test_clean_text(self):
        raw = "Hello World! Visit https://example.com for 123 details."
        cleaned = preprocessor.clean_text(raw)
        self.assertNotIn("https", cleaned)
        self.assertIn("hello world", cleaned)

    def test_tokenization(self):
        text = "NLTK is an amazing toolkit for Python. It simplifies text processing."
        sentences = preprocessor.tokenize_sentences(text)
        words = preprocessor.tokenize_words(text)
        self.assertEqual(len(sentences), 2)
        self.assertGreater(len(words), 5)

    def test_stopwords_removal(self):
        tokens = ["this", "is", "a", "test", "sentence"]
        filtered = preprocessor.remove_stopwords(tokens)
        self.assertNotIn("this", filtered)
        self.assertNotIn("is", filtered)
        self.assertIn("test", filtered)
        self.assertIn("sentence", filtered)

    def test_lemmatization_and_stemming(self):
        tokens = ["studying", "studies", "better"]
        lemmas = preprocessor.lemmatize_tokens(tokens)
        stems = preprocessor.stem_tokens(tokens)
        self.assertTrue("study" in lemmas or "studying" in lemmas)
        self.assertIn("studi", stems)

    def test_full_pipeline_details(self):
        text = "Artificial Intelligence is transforming higher education in India."
        details = preprocessor.get_full_nlp_pipeline_details(text)
        self.assertIn("raw_tokens", details)
        self.assertIn("filtered_tokens", details)
        self.assertIn("pos_tags", details)
        self.assertIn("lemmas", details)
        self.assertIn("stems", details)

if __name__ == '__main__':
    unittest.main()
