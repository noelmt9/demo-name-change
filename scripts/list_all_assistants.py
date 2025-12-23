"""Script to list all assistants and identify potential Generic ones."""

import sys
from pathlib import Path

# Add parent directory to path to import services
sys.path.insert(0, str(Path(__file__).parent.parent))

from services import vapi


def main():
    """List all assistants and show potential Generic ones."""
    print("Fetching all assistants from VAPI...")
    
    try:
        assistants = vapi.list_assistants(limit=500)
        print(f"Found {len(assistants)} assistants total\n")
        
        # List all assistants with "Generic" in name
        generic_assistants = []
        other_assistants = []
        
        for assistant in assistants:
            name = assistant.get("name", "Unnamed")
            if "generic" in name.lower():
                generic_assistants.append(name)
            else:
                other_assistants.append(name)
        
        print("=" * 60)
        print(f"Assistants with 'Generic' in name ({len(generic_assistants)}):")
        print("=" * 60)
        for name in sorted(generic_assistants):
            print(f"  - {name}")
        
        # Also check for assistants that might be generic but not named that way
        # Look for patterns like "Demo", "Template", "Base", etc.
        potential_generic_keywords = ["demo", "template", "base", "standard", "default"]
        potential_generic = []
        
        for assistant in assistants:
            name = assistant.get("name", "Unnamed").lower()
            if any(keyword in name for keyword in potential_generic_keywords):
                if "generic" not in name:  # Don't double-count
                    potential_generic.append(assistant.get("name", "Unnamed"))
        
        if potential_generic:
            print(f"\n{'=' * 60}")
            print(f"Potential Generic assistants (not explicitly named 'Generic') ({len(potential_generic)}):")
            print("=" * 60)
            for name in sorted(potential_generic):
                print(f"  - {name}")
        
        print(f"\n{'=' * 60}")
        print(f"Total assistants: {len(assistants)}")
        print(f"  - With 'Generic': {len(generic_assistants)}")
        print(f"  - Others: {len(other_assistants)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

