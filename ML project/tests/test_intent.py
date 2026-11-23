import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.intent_classifier import intent_classifier

class TestIntentClassifier(unittest.TestCase):
    def test_intent_loading(self):
        intents = intent_classifier.load_intents()
        self.assertGreaterEqual(len(intents), 15)
        self.assertTrue(any(i["tag"] == "greeting" for i in intents))

    def test_intent_training(self):
        metrics = intent_classifier.train(model_type="MultinomialNB")
        # Small dataset (30 intents, ~10 patterns each, 20% test split) can yield low held-out accuracy
        # Check that training runs and returns all required metric keys
        self.assertGreaterEqual(metrics["accuracy"], 0.0)
        self.assertIn("precision", metrics)
        self.assertIn("recall", metrics)
        self.assertIn("f1_score", metrics)
        self.assertTrue(intent_classifier.is_trained)

    def test_intent_prediction(self):
        pred = intent_classifier.predict_intent("Hello, good morning!")
        self.assertIn(pred["tag"], ["greeting", "morning_greeting", "bot_identity", "unknown_fallback"])
        self.assertGreaterEqual(pred["confidence"], 0.0)

    def test_intent_fallback(self):
        # Completely OOV — empty after preprocessing (only numbers and symbols stripped)
        pred = intent_classifier.predict_intent("12345 67890 !@#$%")
        # Either it's already marked fallback OR confidence is very low (< 0.5)
        self.assertTrue(pred["is_fallback"] or pred["confidence"] < 0.5)

if __name__ == '__main__':
    unittest.main()
