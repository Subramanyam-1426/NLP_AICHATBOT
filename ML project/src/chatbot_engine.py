from src.preprocessing import preprocessor
from src.intent_classifier import intent_classifier
from src.sentiment_analyzer import sentiment_analyzer
from src.context_manager import ContextManager
from src.knowledge_base import knowledge_base
from src.document_qa import document_qa
from src.response_generator import response_generator
from src.database import db

class ChatbotEngine:
    """
    Core Master Orchestrator Engine for the AI NLP Chatbot.
    Coordinates preprocessing, intent classification, sentiment analysis,
    context tracking, knowledge base lookups, document Q&A, response generation,
    and SQLite database logging.

    Responses are generated locally from the trained intent data, bundled FAQ,
    or documents uploaded during the current session.
    """
    def __init__(self):
        # Ensure models and KB are loaded
        intent_classifier.load_saved_model()
        # Context memory is private to each conversation (or guest browser session).
        self.contexts = {}

    def _context_for(self, user_id=None, conversation_id=None, session_id=None):
        if conversation_id is not None:
            key = f"conversation:{conversation_id}"
        elif user_id is not None:
            key = f"user:{user_id}"
        else:
            key = f"guest:{session_id or 'default'}"
        if key not in self.contexts:
            self.contexts[key] = ContextManager()
        return self.contexts[key]

    def restore_context(self, conversation_id: int, user_id: int) -> None:
        """Rebuild short-term coreference memory after a page refresh or chat reopen."""
        context = ContextManager()
        for turn in db.get_conversation_messages(conversation_id, user_id):
            tag = turn.get("intent", "unknown")
            context_set = ""
            for item in intent_classifier.intents_data:
                if item.get("tag") == tag:
                    context_set = item.get("context_set", "")
                    break
            context.update_context(
                user_query=turn.get("user_query", ""),
                predicted_intent=tag,
                response=turn.get("response", ""),
                context_set=context_set,
            )
        self.contexts[f"conversation:{conversation_id}"] = context

    def process_query(self, user_query: str, user_id: int | None = None,
                      conversation_id: int | None = None, session_id: str | None = None,
                      search_docs: bool = True, conversation_history: list = None) -> dict:
        """
        Process user query through full multi-module NLP/ML pipeline.
        Returns response payload with message ID, response text, intent info,
        sentiment info, and citations.
        """
        if not user_query or not user_query.strip():
            return {
                "response": "Please enter a valid message.",
                "intent": "unknown",
                "confidence": 0.0,
                "sentiment": "Neutral",
                "message_id": None
            }

        # 1. Pronoun / Coreference resolution
        context_manager = self._context_for(user_id, conversation_id, session_id)
        resolved_query, is_resolved, target_subject = context_manager.resolve_coreference(user_query)

        # 2. Sentiment Analysis
        sentiment_data = sentiment_analyzer.analyze(user_query)

        # 3. Intent Classification
        intent_data = intent_classifier.predict_intent(resolved_query)
        tag = intent_data["tag"]
        responses_list = intent_classifier.tag_to_response.get(tag, [])

        # Find context_set for predicted intent if any
        context_set = ""
        for item in intent_classifier.intents_data:
            if item["tag"] == tag:
                context_set = item.get("context_set", "")
                break

        # 4. Knowledge Base check
        kb_match = knowledge_base.search_faq(resolved_query)

        # 5. Document Q&A check
        doc_matches = []
        document_scope = user_id if user_id is not None else session_id
        if search_docs and document_qa.has_documents(user_id=document_scope):
            doc_matches = document_qa.search_document(resolved_query, top_k=2, user_id=document_scope)

        # Prefer answers grounded in local documents and FAQ data.
        if doc_matches and len(doc_matches) > 0 and doc_matches[0].get("score", 0) > 0.25:
            bot_response = response_generator.generate_response(
                intent_tag=tag,
                responses_list=responses_list,
                sentiment_data=sentiment_data,
                kb_match=None,
                doc_matches=doc_matches
            )

        elif kb_match and (
            kb_match.get("exact_match")
            or intent_data["is_fallback"]
            or kb_match.get("similarity_score", 0) > 0.65
        ):
            bot_response = response_generator.generate_response(
                intent_tag=tag,
                responses_list=responses_list,
                sentiment_data=sentiment_data,
                kb_match=kb_match
            )
        elif not intent_data["is_fallback"] and tag != "unknown_fallback":
            bot_response = response_generator.generate_response(
                intent_tag=tag,
                responses_list=responses_list,
                sentiment_data=sentiment_data
            )
        else:
            bot_response = (
                "I don't have enough information to answer that reliably. "
                "I can help with the topics in my training data, the local FAQ, "
                "or documents you upload."
            )

        # 6. Update Context Memory
        context_manager.update_context(
            user_query=user_query,
            predicted_intent=tag,
            response=bot_response,
            context_set=context_set
        )

        # 7. Log interaction to SQLite database
        msg_id = None
        if user_id is not None and conversation_id is not None:
            msg_id = db.log_interaction(
                conversation_id=conversation_id,
                user_id=user_id,
                user_text=user_query,
                bot_response=bot_response,
                intent_data=intent_data,
                sentiment_data=sentiment_data,
                resolved_query=resolved_query,
            )

        # 8. Extract NLP pipeline details for visualization lab
        nlp_details = preprocessor.get_full_nlp_pipeline_details(user_query)

        return {
            "user_query": user_query,
            "resolved_query": resolved_query,
            "is_coreference_resolved": is_resolved,
            "target_subject": target_subject,
            "response": bot_response,
            "intent": tag,
            "confidence": intent_data["confidence"],
            "is_fallback": intent_data["is_fallback"],
            "top_predictions": intent_data["top_predictions"],
            "sentiment": sentiment_data["sentiment"],
            "sentiment_details": sentiment_data,
            "kb_match": kb_match,
            "doc_matches": doc_matches,
            "nlp_details": nlp_details,
            "message_id": msg_id
        }

chatbot_engine = ChatbotEngine()
