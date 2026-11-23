import random

class ResponseGenerator:
    """
    Response Strategy & Text Generator Engine.
    Combines intent-based responses, sentiment adjustments, knowledge base entries,
    and document citations into natural, friendly conversational output.
    """
    def generate_response(self, intent_tag: str, responses_list: list,
                          sentiment_data: dict = None, kb_match: dict = None,
                          doc_matches: list = None) -> str:
        
        # 1. Document Q&A priority match if strong score present
        if doc_matches and len(doc_matches) > 0 and doc_matches[0].get("score", 0) > 0.25:
            top_match = doc_matches[0]
            citation = f"📄 **Source:** `{top_match['source']}` (Page/Paragraph: {top_match['page']})"
            return f"Based on the uploaded document, here is what I found:\n\n\"{top_match['raw_text']}\"\n\n{citation}"

        # 2. Knowledge Base match priority
        if kb_match and kb_match.get("similarity_score", 0) > 0.4:
            return f"💡 **{kb_match['question']}**\n\n{kb_match['answer']}"

        # 3. Intent responses
        if responses_list:
            base_response = random.choice(responses_list)
        else:
            base_response = "I understand your query, but I'm not sure how to respond right now."

        # 4. Sentiment-aware prefix/suffix adjustments
        if sentiment_data:
            sentiment = sentiment_data.get("sentiment", "Neutral")
            if sentiment == "Negative" and intent_tag != "greeting":
                base_response = f"I'm sorry to hear that you're facing an issue! " + base_response
            elif sentiment == "Positive" and intent_tag in ["thanks", "greeting"]:
                base_response = base_response + " 😊"

        return base_response

response_generator = ResponseGenerator()
