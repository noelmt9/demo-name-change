"""RAG service for retrieving relevant FAQ examples."""

from typing import List, Dict, Optional
from services.embeddings import embed_text
from services.vector_db import search_examples, initialize_db


def retrieve_examples(
    query: str,
    scenario: Dict[str, str],
    k: int = 5
) -> List[Dict]:
    """
    Retrieve relevant FAQ examples based on query and scenario.
    
    Args:
        query: User question/instruction to find similar examples for
        scenario: Dictionary with 'stage' and 'domain' keys
        k: Number of examples to retrieve
    
    Returns:
        List of example dictionaries with question, answer, generated_prompt, etc.
    """
    # Ensure vector DB is initialized
    initialize_db()
    
    # Generate embedding for query
    try:
        query_embedding = embed_text(query)
    except Exception as e:
        print(f"Warning: Failed to generate embedding: {e}")
        return []
    
    # Build scenario tags for filtering
    scenario_tags = []
    stage = scenario.get("stage", "generic")
    domain = scenario.get("domain", "generic")
    
    if stage != "generic":
        scenario_tags.append(stage)
    if domain != "generic":
        scenario_tags.append(domain)
    
    # If no specific tags, use empty list to search all
    if not scenario_tags:
        scenario_tags = None
    
    # Search for similar examples
    try:
        examples = search_examples(
            query_embedding=query_embedding,
            scenario_tags=scenario_tags,
            limit=k
        )
        return examples
    except Exception as e:
        print(f"Warning: Failed to search examples: {e}")
        return []

