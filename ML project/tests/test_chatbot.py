import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.context_manager import context_manager
from src.sentiment_analyzer import sentiment_analyzer
from src.knowledge_base import knowledge_base
from src.chatbot_engine import chatbot_engine

class TestChatbotEngine(unittest.TestCase):
    def test_context_manager(self):
        context_manager.reset()
        context_manager.update_context("Tell me about Python", "python_info", "Python is a language", context_set="Python")
        resolved, is_resolved, subj = context_manager.resolve_coreference("Who created it?")
        self.assertTrue(is_resolved)
        self.assertIn("Python", resolved)

    def test_sentiment_analyzer(self):
        res = sentiment_analyzer.analyze("I love learning NLP, it is amazing!")
        self.assertEqual(res["sentiment"], "Positive")
        self.assertGreater(res["compound"], 0.0)

    def test_knowledge_base(self):
        faq = knowledge_base.search_faq("What is TF-IDF?")
        self.assertIsNotNone(faq)
        self.assertTrue("TF-IDF" in faq["question"] or "TF-IDF" in faq["answer"])

    def test_chatbot_engine_pipeline(self):
        payload = chatbot_engine.process_query("What courses are offered?", session_id="test_session")
        self.assertIn("response", payload)
        self.assertNotEqual(payload["intent"], "")
        self.assertIn(payload["sentiment"], ["Positive", "Neutral", "Negative"])
        self.assertIn("nlp_details", payload)

    def test_faq_response_is_available_offline(self):
        payload = chatbot_engine.process_query("What is TF-IDF?", session_id="offline_test")
        self.assertIn("Inverse Document Frequency", payload["response"])

    def test_unknown_query_uses_safe_fallback(self):
        payload = chatbot_engine.process_query("Who is Rohit Sharma?", session_id="offline_test")
        self.assertIn("don't have enough information", payload["response"])

    def test_general_conversation_and_formal_writing_prompts(self):
        examples = [
            ("How are you?", "how_are_you", "I'm doing well"),
            ("What is your name?", "bot_identity", "AI chatbot"),
            ("Are you a robot?", "bot_physical_form", "not a physical robot"),
            ("What is the time?", "time_date_limit", "can't check the live time"),
            ("Tell me a joke", "joke_request", "computer"),
            ("I am happy", "happiness_response", "That's wonderful"),
            ("Write a formal email", "formal_email_request", "Subject:"),
            ("Write a formal leave letter", "formal_leave_letter", "Leave Request"),
            ("What is C++?", "cpp_info", "C++ is"),
            ("What is tokenization?", "tokenization", "Tokenization splits text"),
            ("What is text preprocessing?", "text_preprocessing", "Text preprocessing prepares raw language")
        ]
        for query, expected_intent, expected_response in examples:
            with self.subTest(query=query):
                payload = chatbot_engine.process_query(query, session_id="general_samples")
                self.assertEqual(payload["intent"], expected_intent)
                self.assertIn(expected_response, payload["response"])

if __name__ == '__main__':
    unittest.main()
