"""Utility to load scenario-specific system prompts from system_prompts folder."""

from pathlib import Path
from typing import Optional, Dict, List
import re
import hashlib


_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "system_prompts"
_prompt_cache: Dict[str, str] = {}
_cache_hashes: Dict[str, str] = {}


def _get_file_hash(filepath: Path) -> str:
    """Get hash of file modification time and size."""
    try:
        stat = filepath.stat()
        return hashlib.md5(f"{filepath.name}:{stat.st_mtime}:{stat.st_size}".encode()).hexdigest()
    except:
        return ""


def _normalize_scenario(stage: str, domain: str) -> tuple[str, str]:
    """Normalize scenario strings for matching."""
    stage_lower = stage.lower().replace("-", "_").replace(" ", "_")
    domain_lower = domain.lower().replace("-", "_").replace(" ", "_")
    return stage_lower, domain_lower


def _match_filename(filename: str, stage: str, domain: str) -> bool:
    """
    Check if filename matches the scenario.
    
    Args:
        filename: Filename to check
        stage: Stage (pre_charge_off, post_charge_off)
        domain: Domain (auto, b2b, generic, etc.)
    
    Returns:
        True if filename matches scenario
    """
    filename_lower = filename.lower()
    
    # Stage matching
    stage_patterns = {
        "pre_charge_off": ["pre", "pre-charge", "precharge", "pre_charge"],
        "post_charge_off": ["post", "post-charge", "postcharge", "post_charge"]
    }
    
    stage_matches = False
    if stage in stage_patterns:
        stage_matches = any(pattern in filename_lower for pattern in stage_patterns[stage])
    elif stage == "generic":
        # Generic matches if no specific stage indicators
        stage_matches = not any(
            pattern in filename_lower 
            for patterns in stage_patterns.values() 
            for pattern in patterns
        )
    
    # Domain matching
    domain_patterns = {
        "auto": ["auto", "automotive", "vehicle", "car"],
        "b2b": ["b2b", "business", "commercial"],
        "medical": ["medical", "health"],
        "lending": ["lending", "loan"],
        "leasing": ["leasing", "lease"],
        "generic": []  # Generic matches if no specific domain
    }
    
    domain_matches = False
    if domain in domain_patterns:
        if domain_patterns[domain]:
            domain_matches = any(pattern in filename_lower for pattern in domain_patterns[domain])
        else:  # generic
            # Generic matches if no specific domain indicators
            domain_matches = not any(
                pattern in filename_lower 
                for d, patterns in domain_patterns.items() 
                if d != "generic"
                for pattern in patterns
            )
    
    return stage_matches and domain_matches


def load_scenario_prompt(stage: str, domain: str) -> str:
    """
    Load scenario-specific system prompt from system_prompts folder.
    
    Args:
        stage: Stage (pre_charge_off, post_charge_off, generic)
        domain: Domain (auto, b2b, medical, lending, leasing, generic)
    
    Returns:
        System prompt text, or empty string if not found
    """
    if not _PROMPTS_DIR.exists():
        return ""
    
    stage, domain = _normalize_scenario(stage, domain)
    cache_key = f"{stage}_{domain}"
    
    # Check cache
    if cache_key in _prompt_cache:
        # Verify cache is still valid
        # For simplicity, we'll reload on each call (can optimize later)
        pass
    
    # Find matching file
    matching_files = []
    for filepath in _PROMPTS_DIR.glob("*.txt"):
        if _match_filename(filepath.name, stage, domain):
            matching_files.append(filepath)
    
    # If multiple matches, prefer more specific ones (shorter filenames often more specific)
    if matching_files:
        # Sort by filename length (shorter = more specific)
        matching_files.sort(key=lambda f: len(f.name))
        selected_file = matching_files[0]
        
        # Check if file changed
        file_hash = _get_file_hash(selected_file)
        if cache_key in _cache_hashes and _cache_hashes[cache_key] == file_hash:
            return _prompt_cache[cache_key]
        
        # Load file
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Cache it
            _prompt_cache[cache_key] = content
            _cache_hashes[cache_key] = file_hash
            
            return content
        except Exception as e:
            print(f"Warning: Could not load prompt from {selected_file.name}: {e}")
    
    # Fallback to Generic.txt
    generic_file = _PROMPTS_DIR / "Generic.txt"
    if generic_file.exists():
        try:
            with open(generic_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    
    return ""


def get_available_scenarios() -> List[Dict[str, str]]:
    """
    Get list of available scenario prompts.
    
    Returns:
        List of dicts with stage, domain, and filename
    """
    if not _PROMPTS_DIR.exists():
        return []
    
    scenarios = []
    for filepath in _PROMPTS_DIR.glob("*.txt"):
        # Try to extract scenario from filename
        filename_lower = filepath.name.lower()
        
        stage = "generic"
        if "pre" in filename_lower and "charge" in filename_lower:
            stage = "pre_charge_off"
        elif "post" in filename_lower and "charge" in filename_lower:
            stage = "post_charge_off"
        
        domain = "generic"
        if "auto" in filename_lower:
            domain = "auto"
        elif "b2b" in filename_lower or "business" in filename_lower:
            domain = "b2b"
        elif "medical" in filename_lower or "health" in filename_lower:
            domain = "medical"
        elif "lending" in filename_lower or "loan" in filename_lower:
            domain = "lending"
        elif "leasing" in filename_lower or "lease" in filename_lower:
            domain = "leasing"
        
        scenarios.append({
            "stage": stage,
            "domain": domain,
            "filename": filepath.name
        })
    
    return scenarios

