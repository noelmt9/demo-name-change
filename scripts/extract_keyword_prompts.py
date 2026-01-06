"""Script to extract system prompts from VAPI assistants with specific keywords in their names."""

import sys
from pathlib import Path
import hashlib
import os

# Add parent directory to path to import services
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, skip

from services import vapi
from pathlib import Path
import re


def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        name: Original filename
    
    Returns:
        Sanitized filename safe for filesystem
    """
    # Replace invalid filename characters with underscores
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', name)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[_\s]+', '_', sanitized)
    
    return sanitized


def extract_system_prompt(assistant: dict) -> str:
    """
    Extract system prompt from assistant configuration.
    
    Args:
        assistant: Assistant dictionary from VAPI API
    
    Returns:
        System prompt string, or empty string if not found
    """
    try:
        # System prompt is typically in model.messages[0].content
        messages = assistant.get("model", {}).get("messages", [])
        if messages and len(messages) > 0:
            # Find the system message
            for message in messages:
                if message.get("role") == "system":
                    return message.get("content", "")
        
        # Fallback: check if there's a direct system prompt field
        return assistant.get("systemPrompt", "")
    except Exception as e:
        print(f"Error extracting prompt: {e}")
        return ""


def get_content_hash(content: str) -> str:
    """
    Generate a hash of the content to detect duplicates.
    
    Args:
        content: The prompt content
    
    Returns:
        MD5 hash string
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def check_duplicate_content(prompts_dir: Path, content: str) -> tuple[bool, str]:
    """
    Check if content already exists in any file in the directory.
    
    Args:
        prompts_dir: Directory to check
        content: Content to check
    
    Returns:
        Tuple of (is_duplicate, existing_filename)
    """
    content_hash = get_content_hash(content)
    
    # Check all existing files
    for filepath in prompts_dir.glob("*.txt"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_content = f.read()
                if get_content_hash(existing_content) == content_hash:
                    return True, filepath.name
        except Exception:
            continue
    
    return False, ""


def main():
    """Main function to extract and save prompts with specific keywords."""
    print("="*60)
    print("Extracting System Prompts with Keywords")
    print("="*60)
    print("\nKeywords: leasing, lending, journey, pre charge off, post charge off")
    print("\nFetching assistants from VAPI...")
    
    try:
        # Get all assistants (limit 500)
        assistants = vapi.list_assistants(limit=500)
        print(f"Found {len(assistants)} assistants total")
        
        # Define keywords (case-insensitive matching)
        keywords = [
            "leasing",
            "lending", 
            "journey",
            "pre charge off",
            "pre charge-off",
            "pre-charge off",
            "precharge off",
            "post charge off",
            "post charge-off",
            "post-charge off",
            "postcharge off"
        ]
        
        matching_assistants = []
        
        for assistant in assistants:
            name = assistant.get("name", "")
            name_lower = name.lower()
            # Match if any keyword is in the name
            if any(keyword in name_lower for keyword in keywords):
                matching_assistants.append(assistant)
        
        print(f"\nFound {len(matching_assistants)} assistants matching criteria")
        print("\nAssistants to process:")
        for asst in matching_assistants:
            print(f"  - {asst.get('name', 'Unnamed')}")
        
        if not matching_assistants:
            print("No matching assistants found. Exiting.")
            return
        
        # Create system_prompts directory if it doesn't exist
        prompts_dir = Path(__file__).parent.parent / "prompts" / "system_prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract and save prompts
        saved_count = 0
        skipped_count = 0
        updated_count = 0
        new_count = 0
        duplicate_count = 0
        
        for assistant in matching_assistants:
            name = assistant.get("name", "Unnamed")
            assistant_id = assistant.get("id", "")
            
            print(f"\nProcessing: {name} (ID: {assistant_id})")
            
            # Get full assistant details
            try:
                full_assistant = vapi.get_assistant(assistant_id)
                if not full_assistant:
                    print(f"  ⚠️  Could not fetch full details for {name}")
                    skipped_count += 1
                    continue
            except Exception as e:
                print(f"  ⚠️  Error fetching details: {e}")
                skipped_count += 1
                continue
            
            # Extract system prompt
            prompt = extract_system_prompt(full_assistant)
            
            if not prompt:
                print(f"  ⚠️  No system prompt found for {name}")
                skipped_count += 1
                continue
            
            # Check for duplicate content
            is_duplicate, existing_file = check_duplicate_content(prompts_dir, prompt)
            if is_duplicate:
                print(f"  ⏭️  Duplicate content (already exists as {existing_file}) - skipping")
                duplicate_count += 1
                continue
            
            # Sanitize filename
            filename = sanitize_filename(name)
            filepath = prompts_dir / f"{filename}.txt"
            
            # Check if file already exists (same name but different content)
            file_exists = filepath.exists()
            
            # Save to file
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(prompt)
                
                if file_exists:
                    print(f"  🔄 Updated: {filepath.name} ({len(prompt)} characters)")
                    updated_count += 1
                else:
                    print(f"  ✅ Saved: {filepath.name} ({len(prompt)} characters)")
                    new_count += 1
                saved_count += 1
            except Exception as e:
                print(f"  ❌ Error saving file: {e}")
                skipped_count += 1
        
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  ✅ Successfully saved/updated: {saved_count} prompts")
        print(f"    - New files: {new_count}")
        print(f"    - Updated files: {updated_count}")
        print(f"  ⏭️  Duplicates skipped: {duplicate_count}")
        print(f"  ⚠️  Skipped (errors/missing): {skipped_count}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

