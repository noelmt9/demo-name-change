"""Router service for classifying FAQ scenarios."""

from typing import Dict, Optional, List
from openai import OpenAI
from config import OPENAI_API_KEY, ROUTER_MODEL


_client = None


def get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def classify_scenario(faqs: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Classify the scenario based on FAQ questions and answers.
    
    Args:
        faqs: List of FAQ dictionaries with 'trigger' and 'instruction' keys
    
    Returns:
        Dictionary with 'stage' and 'domain' keys
    """
    if not faqs:
        return {"stage": "generic", "domain": "generic"}
    
    client = get_client()
    
    # Build classification prompt
    faq_text = "\n".join([
        f"Q: {faq.get('trigger', '')}\nA: {faq.get('instruction', '')}"
        for faq in faqs[:5]  # Use first 5 FAQs for classification
    ])
    
    classification_prompt = f"""Analyze the following FAQ questions and answers to determine the scenario.

FAQs:
{faq_text}

Classify into:
- stage: "pre_charge_off", "post_charge_off", or "generic"
- domain: "auto", "b2b", "medical", "lending", "leasing", or "generic"

Return JSON with "stage" and "domain" keys only."""

    try:
        response = client.chat.completions.create(
            model=ROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a classification system. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": classification_prompt
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        # Validate and normalize
        stage = result.get("stage", "generic").lower()
        domain = result.get("domain", "generic").lower()
        
        # Normalize values
        valid_stages = ["pre_charge_off", "post_charge_off", "generic"]
        valid_domains = ["auto", "b2b", "medical", "lending", "leasing", "generic"]
        
        if stage not in valid_stages:
            stage = "generic"
        if domain not in valid_domains:
            domain = "generic"
        
        return {"stage": stage, "domain": domain}
        
    except Exception as e:
        # Fallback to generic on error
        print(f"Warning: Classification failed: {e}, using generic scenario")
        return {"stage": "generic", "domain": "generic"}

