"""Qdrant vector database service for storing and retrieving FAQ examples."""

from typing import List, Dict, Optional
from pathlib import Path
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Query, Filter, FieldCondition, MatchAny
from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME, OPENAI_EMBEDDING_MODEL


_client = None
_collection_initialized = False


def get_client() -> QdrantClient:
    """Get or create Qdrant client."""
    global _client
    if _client is None:
        if QDRANT_API_KEY:
            # Cloud mode
            _client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY
            )
        else:
            # Local mode - use file-based storage
            db_path = Path(__file__).parent.parent / "data" / "vector_db"
            db_path.mkdir(parents=True, exist_ok=True)
            _client = QdrantClient(path=str(db_path))
    return _client


def initialize_db(vector_size: int = 1536) -> bool:
    """
    Initialize the vector database collection if it doesn't exist.
    
    Args:
        vector_size: Dimension of embedding vectors (1536 for text-embedding-3-small)
    
    Returns:
        True if collection was created, False if it already existed
    """
    global _collection_initialized
    
    if _collection_initialized:
        return False
    
    client = get_client()
    
    # Check if collection exists
    try:
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if QDRANT_COLLECTION_NAME in collection_names:
            _collection_initialized = True
            return False
    except Exception:
        pass
    
    # Create collection
    try:
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        _collection_initialized = True
        return True
    except Exception as e:
        # Collection might already exist
        _collection_initialized = True
        return False


def add_example(
    question: str,
    answer: str,
    generated_prompt: str,
    scenario_tags: List[str],
    source_file: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> str:
    """
    Add an FAQ example to the vector database.
    
    Args:
        question: User question/trigger
        answer: Bot response instruction
        generated_prompt: Full generated prompt text
        scenario_tags: List of scenario tags (e.g., ["pre_charge_off", "auto"])
        source_file: Optional source file name
        embedding: Optional pre-computed embedding (will compute if not provided)
    
    Returns:
        UUID of the added point
    """
    from services.embeddings import embed_text
    
    client = get_client()
    initialize_db()
    
    # Generate embedding if not provided
    if embedding is None:
        # Combine question and answer for embedding
        text_to_embed = f"{question}\n{answer}"
        embedding = embed_text(text_to_embed)
    
    # Create point
    point_id = str(uuid.uuid4())
    point = PointStruct(
        id=point_id,
        vector=embedding,
        payload={
            "question": question,
            "answer": answer,
            "generated_prompt": generated_prompt,
            "scenario_tags": scenario_tags,
            "source_file": source_file or "unknown"
        }
    )
    
    try:
        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[point]
        )
        return point_id
    except Exception as e:
        raise Exception(f"Failed to add example to vector DB: {str(e)}")


def search_examples(
    query_embedding: List[float],
    scenario_tags: Optional[List[str]] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search for similar FAQ examples.
    
    Args:
        query_embedding: Embedding vector of the query
        scenario_tags: Optional list of scenario tags to filter by
        limit: Maximum number of results to return
    
    Returns:
        List of example dictionaries with metadata
    """
    client = get_client()
    initialize_db()
    
    # Build filter if scenario tags provided
    query_filter = None
    if scenario_tags:
        # Filter by any of the provided tags
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="scenario_tags",
                    match=MatchAny(any=scenario_tags)
                )
            ]
        )
    
    try:
        # Use query_points - pass embedding vector directly as query
        # The query parameter accepts a list[float] for vector search
        results = client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_embedding,  # Direct vector embedding
            query_filter=query_filter,
            limit=limit
        )
        
        examples = []
        for point in results.points:
            examples.append({
                "id": point.id,
                "score": point.score if hasattr(point, 'score') else 0.0,
                "question": point.payload.get("question", ""),
                "answer": point.payload.get("answer", ""),
                "generated_prompt": point.payload.get("generated_prompt", ""),
                "scenario_tags": point.payload.get("scenario_tags", []),
                "source_file": point.payload.get("source_file", "unknown")
            })
        
        return examples
    except Exception as e:
        raise Exception(f"Failed to search vector DB: {str(e)}")


def add_user_accepted_faq(
    input_faqs: list,
    generated_prompt: str,
    user_email: str = None
) -> str:
    """
    Add a user-accepted FAQ to the vector database for training feedback.

    This improves future FAQ generations by including examples that users
    found helpful.

    Args:
        input_faqs: List of FAQ dicts with 'trigger' and 'instruction' keys
        generated_prompt: The generated prompt that was accepted
        user_email: Optional email of the user who accepted it

    Returns:
        UUID of the added point
    """
    from services.embeddings import embed_text

    client = get_client()
    initialize_db()

    # Combine all FAQ triggers and instructions for embedding
    combined_text = ""
    for faq in input_faqs:
        combined_text += f"Q: {faq.get('trigger', '')}\nA: {faq.get('instruction', '')}\n"

    embedding = embed_text(combined_text)

    # Create point with metadata indicating this is user-accepted
    point_id = str(uuid.uuid4())
    point = PointStruct(
        id=point_id,
        vector=embedding,
        payload={
            "question": combined_text,
            "answer": "User-accepted FAQ set",
            "generated_prompt": generated_prompt,
            "scenario_tags": ["user_accepted"],
            "source_file": f"user_accepted_{user_email or 'anonymous'}",
            "source": "user_accepted",
            "input_faqs": input_faqs
        }
    )

    try:
        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[point]
        )
        return point_id
    except Exception as e:
        raise Exception(f"Failed to add user-accepted FAQ to vector DB: {str(e)}")


def bulk_load_training_examples() -> int:
    """
    Load all training examples from prompts/training_examples/ into vector DB.
    
    Returns:
        Number of examples loaded
    """
    from pathlib import Path
    from services.embeddings import embed_text
    
    training_examples_dir = Path(__file__).parent.parent / "prompts" / "training_examples"
    
    if not training_examples_dir.exists():
        return 0
    
    example_files = sorted(training_examples_dir.glob("*.txt"))
    loaded_count = 0
    
    for example_file in example_files:
        try:
            with open(example_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            if not content:
                continue
            
            # Parse example (format: User Input, Bot Response, Generated Prompt)
            lines = content.split("\n")
            question = ""
            answer = ""
            generated_prompt = ""
            
            current_section = None
            for line in lines:
                if "User Input:" in line or "User input:" in line:
                    current_section = "question"
                    question = line.split(":", 1)[1].strip().strip('"')
                elif "Bot Response:" in line or "Bot response:" in line:
                    current_section = "answer"
                    answer = line.split(":", 1)[1].strip().strip('"')
                elif "Your Generated Prompt:" in line or "Generated Prompt:" in line:
                    current_section = "prompt"
                elif current_section == "prompt":
                    generated_prompt += line + "\n"
                elif current_section == "question" and not question:
                    question = line.strip().strip('"')
                elif current_section == "answer" and not answer:
                    answer = line.strip().strip('"')
            
            generated_prompt = generated_prompt.strip()
            
            if not question or not answer:
                continue
            
            # Extract scenario tags from filename or content
            scenario_tags = []
            filename_lower = example_file.name.lower()
            if "pre" in filename_lower or "pre-charge" in filename_lower:
                scenario_tags.append("pre_charge_off")
            if "post" in filename_lower or "post-charge" in filename_lower:
                scenario_tags.append("post_charge_off")
            if "auto" in filename_lower:
                scenario_tags.append("auto")
            if "b2b" in filename_lower or "business" in filename_lower:
                scenario_tags.append("b2b")
            if not scenario_tags:
                scenario_tags.append("generic")
            
            # Add to vector DB
            add_example(
                question=question,
                answer=answer,
                generated_prompt=generated_prompt,
                scenario_tags=scenario_tags,
                source_file=example_file.name
            )
            loaded_count += 1
            
        except Exception as e:
            print(f"Warning: Could not load {example_file.name}: {e}")
            continue
    
    return loaded_count

