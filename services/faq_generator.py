"""Main orchestration service for FAQ generation using Routing + RAG + Structured Outputs."""

from typing import List, Dict, Optional
from services.router import classify_scenario
from services.rag import retrieve_examples
from services.openai_service import generate_faqs_with_rag
from services.vector_db import initialize_db
from utils.scenario_prompts import load_scenario_prompt


def generate_faqs(
    faqs: List[Dict[str, str]],
    existing_prompt: Optional[str] = None
) -> str:
    """
    Generate FAQ prompts using Routing + RAG + Structured Outputs architecture.
    
    This is the main entry point that orchestrates:
    1. Router: Classify scenario
    2. RAG: Retrieve relevant examples
    3. Generation: Generate with structured outputs
    
    Args:
        faqs: List of FAQ dictionaries with 'trigger' and 'instruction' keys
        existing_prompt: Optional existing system prompt to extract flows and FAQ context from
    
    Returns:
        Generated FAQ prompt text
    """
    if not faqs:
        raise ValueError("At least one FAQ is required")
    
    # Ensure vector DB is initialized
    try:
        initialize_db()
    except Exception as e:
        print(f"Warning: Vector DB initialization failed: {e}")
    
    # Step 1: Route to determine scenario
    try:
        scenario = classify_scenario(faqs)
    except Exception as e:
        print(f"Warning: Router failed: {e}, using generic scenario")
        scenario = {"stage": "generic", "domain": "generic"}
    
    # Step 2: Load scenario-specific system prompt
    scenario_prompt = load_scenario_prompt(
        stage=scenario.get("stage", "generic"),
        domain=scenario.get("domain", "generic")
    )
    
    # If no scenario prompt found, use a basic one
    if not scenario_prompt:
        scenario_prompt = """You are a prompt engineer specializing in debt collection voicebot systems. 
Your task is to convert FAQ information into system prompt sections that match a specific writing style.
Use numbered format (1., 2., etc.) for main triggers and nested conditions when needed."""
    
    # Step 3: Retrieve relevant examples via RAG
    # Combine all FAQ questions for retrieval
    query_text = " ".join([faq.get("trigger", "") + " " + faq.get("instruction", "") for faq in faqs])
    
    try:
        retrieved_examples = retrieve_examples(
            query=query_text,
            scenario=scenario,
            k=5
        )
    except Exception as e:
        print(f"Warning: RAG retrieval failed: {e}, continuing without examples")
        retrieved_examples = []
    
    # Step 4: Generate with structured outputs
    try:
        generated_prompt = generate_faqs_with_rag(
            faqs=faqs,
            scenario_prompt=scenario_prompt,
            retrieved_examples=retrieved_examples,
            existing_prompt=existing_prompt
        )
        return generated_prompt
    except Exception as e:
        raise Exception(f"Failed to generate FAQs: {str(e)}")

