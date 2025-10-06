"""
Generate concise titles for conversations using OpenAI.
"""
from openai import OpenAI
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


def generate_conversation_title(query: str) -> str:
    """
    Generate a concise 2-4 word title for a conversation based on the user's query.

    Args:
        query: The user's query/message

    Returns:
        A concise title (2-4 words)
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a concise 2-4 word title that summarizes the user's query. Return ONLY the title, nothing else."
                },
                {
                    "role": "user",
                    "content": f"Generate a title for this query: {query}"
                }
            ],
            max_tokens=20,
            temperature=0.7
        )

        title = response.choices[0].message.content.strip()

        # Remove quotes if present
        title = title.strip('"\'')

        # Limit to 50 characters max
        if len(title) > 50:
            title = title[:47] + "..."

        return title

    except Exception as e:
        logger.warning(f"Error generating conversation title: {e}")
        # Fallback: use first few words of query
        words = query.split()[:4]
        return " ".join(words).capitalize()
