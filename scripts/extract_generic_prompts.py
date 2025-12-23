"""Script to extract system prompts from Generic VAPI assistants."""

import sys
from pathlib import Path

# Add parent directory to path to import services
sys.path.insert(0, str(Path(__file__).parent.parent))

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


def main():
    """Main function to extract and save Generic prompts."""
    print("Fetching assistants from VAPI...")
    
    try:
        # Get all assistants (limit 500)
        assistants = vapi.list_assistants(limit=500)
        print(f"Found {len(assistants)} assistants total")
        
        # Filter assistants with "Generic" in name (case-insensitive)
        generic_assistants = []
        
        for assistant in assistants:
            name = assistant.get("name", "")
            # Case-insensitive search for "Generic"
            if "generic" in name.lower():
                generic_assistants.append(assistant)
        
        print(f"\nFound {len(generic_assistants)} assistants with 'Generic' in name:")
        for asst in generic_assistants:
            print(f"  - {asst.get('name', 'Unnamed')}")
        
        if not generic_assistants:
            print("No Generic assistants found. Exiting.")
            return
        
        # Create system_prompts directory if it doesn't exist
        prompts_dir = Path(__file__).parent.parent / "prompts" / "system_prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract and save prompts
        saved_count = 0
        skipped_count = 0
        updated_count = 0
        
        for assistant in generic_assistants:
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
            
            # Sanitize filename
            filename = sanitize_filename(name)
            filepath = prompts_dir / f"{filename}.txt"
            
            # Check if file already exists
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
                saved_count += 1
            except Exception as e:
                print(f"  ❌ Error saving file: {e}")
                skipped_count += 1
        
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  ✅ Successfully saved/updated: {saved_count} prompts")
        if updated_count > 0:
            print(f"  🔄 Updated existing: {updated_count} prompts")
        print(f"  ⚠️  Skipped: {skipped_count} assistants")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

