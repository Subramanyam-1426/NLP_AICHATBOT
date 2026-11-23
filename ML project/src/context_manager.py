import re

class ContextManager:
    """
    Short-term Conversational Memory & Coreference Resolution Manager.
    Tracks active subject context, intent history, target subjects (e.g. Python, Admission, College),
    and resolves coreferences like "it", "this", "its features", "who made it?".
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_context = ""
        self.last_intent = ""
        self.last_query = ""
        self.last_response = ""
        self.target_subject = ""
        self.history = []

    def update_context(self, user_query: str, predicted_intent: str, response: str, context_set: str = ""):
        """
        Record interaction and update target subject heuristics.
        """
        self.last_query = user_query
        self.last_intent = predicted_intent
        self.last_response = response

        if context_set:
            self.current_context = context_set
            self.target_subject = context_set

        # Subject extraction heuristics
        query_lower = user_query.lower()
        if "python" in query_lower:
            self.target_subject = "Python"
        elif "java" in query_lower:
            self.target_subject = "Java"
        elif "machine learning" in query_lower or "ml" in query_lower:
            self.target_subject = "Machine Learning"
        elif "nlp" in query_lower or "natural language processing" in query_lower:
            self.target_subject = "NLP"
        elif "college" in query_lower or "institute" in query_lower:
            self.target_subject = "College"
        elif "admission" in query_lower:
            self.target_subject = "Admission"
        elif "hostel" in query_lower:
            self.target_subject = "Hostel"

        self.history.append({
            "query": user_query,
            "intent": predicted_intent,
            "subject": self.target_subject,
            "context": self.current_context
        })

    def resolve_coreference(self, user_query: str) -> tuple:
        """
        Check if user query contains pronouns like "it", "its", "this", "that", "who created it".
        If present, rewrite or append the target subject context.
        Returns (resolved_query, is_resolved, resolved_subject).
        """
        query_lower = user_query.lower()
        pronouns = [r'\bit\b', r'\bits\b', r'\bthis\b', r'\bthat\b', r'\bthey\b', r'\bthem\b']
        
        has_pronoun = any(re.search(p, query_lower) for p in pronouns)

        if has_pronoun and self.target_subject:
            # Construct enhanced query combining target subject
            resolved_query = f"{user_query} regarding {self.target_subject}"
            return resolved_query, True, self.target_subject

        return user_query, False, self.target_subject

    def get_summary(self) -> dict:
        """Returns current context state summary."""
        return {
            "current_context": self.current_context,
            "last_intent": self.last_intent,
            "target_subject": self.target_subject,
            "total_turns": len(self.history)
        }

context_manager = ContextManager()
