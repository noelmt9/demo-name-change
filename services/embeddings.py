"""OpenAI embedding service for generating vector embeddings."""

from typing import List, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL


_client = None


def get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_text(text: str, model: Optional[str] = None) -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text to embed
        model: Optional model override (defaults to OPENAI_EMBEDDING_MODEL)
    
    Returns:
        List of floats representing the embedding vector
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    client = get_client()
    model = model or OPENAI_EMBEDDING_MODEL
    
    try:
        response = client.embeddings.create(
            model=model,
            input=text.strip()
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")


def embed_batch(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch.
    
    Args:
        texts: List of texts to embed
        model: Optional model override (defaults to OPENAI_EMBEDDING_MODEL)
    
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    # Filter out empty texts
    non_empty_texts = [t.strip() for t in texts if t and t.strip()]
    if not non_empty_texts:
        raise ValueError("No valid texts to embed")
    
    client = get_client()
    model = model or OPENAI_EMBEDDING_MODEL
    
    try:
        response = client.embeddings.create(
            model=model,
            input=non_empty_texts
        )
        # Return embeddings in same order as input (with None for empty texts)
        embeddings = {}
        for item in response.data:
            embeddings[item.index] = item.embedding
        
        result = []
        text_idx = 0
        for text in texts:
            if text and text.strip():
                result.append(embeddings[text_idx])
                text_idx += 1
            else:
                result.append(None)
        
        return result
    except Exception as e:
        raise Exception(f"Failed to generate batch embeddings: {str(e)}")

