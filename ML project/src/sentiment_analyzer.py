import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from src.utilities import initialize_nltk

initialize_nltk()

class SentimentAnalyzer:
    """
    VADER Sentiment Analysis Engine.
    Analyzes compound, positive, neutral, and negative scores
    and classifies tone into Positive, Negative, or Neutral with confidence.
    """
    def __init__(self):
        try:
            self.sid = SentimentIntensityAnalyzer()
        except LookupError:
            self.sid = None

    def analyze(self, text: str) -> dict:
        """
        Analyze input text sentiment.
        Returns label, compound score, detail breakdown, and confidence score.
        """
        if not text or not text.strip():
            return {
                "sentiment": "Neutral",
                "compound": 0.0,
                "pos": 0.0,
                "neu": 1.0,
                "neg": 0.0,
                "confidence": 1.0,
                "emoji": "😐"
            }

        if self.sid:
            scores = self.sid.polarity_scores(text)
        else:
            positive_words = {"amazing", "awesome", "best", "excellent", "glad", "good", "great", "happy", "helpful", "love", "perfect", "thanks", "thank", "wonderful"}
            negative_words = {"angry", "bad", "broken", "disappointed", "hate", "issue", "poor", "sad", "terrible", "unhappy", "upset", "worst"}
            words = set(re.findall(r"[a-z]+", text.lower()))
            positive = len(words & positive_words)
            negative = len(words & negative_words)
            total = positive + negative
            compound = (positive - negative) / total if total else 0.0
            scores = {
                "compound": compound,
                "pos": positive / max(len(words), 1),
                "neu": max(0.0, 1.0 - total / max(len(words), 1)),
                "neg": negative / max(len(words), 1)
            }
        compound = scores["compound"]

        if compound >= 0.05:
            sentiment = "Positive"
            emoji = "😊"
            confidence = min(1.0, 0.5 + compound * 0.5)
        elif compound <= -0.05:
            sentiment = "Negative"
            emoji = "😟"
            confidence = min(1.0, 0.5 + abs(compound) * 0.5)
        else:
            sentiment = "Neutral"
            emoji = "😐"
            confidence = 1.0 - abs(compound)

        return {
            "sentiment": sentiment,
            "compound": round(compound, 4),
            "pos": round(scores["pos"], 4),
            "neu": round(scores["neu"], 4),
            "neg": round(scores["neg"], 4),
            "confidence": round(confidence, 4),
            "emoji": emoji
        }

sentiment_analyzer = SentimentAnalyzer()
