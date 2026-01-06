"""Script to initialize vector DB and load training examples."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, skip

from services.vector_db import initialize_db, bulk_load_training_examples


def main():
    """Initialize vector DB and load training examples."""
    import os
    from config import OPENAI_API_KEY
    
    print("="*60)
    print("Initializing Vector DB")
    print("="*60)
    
    # Check for API key
    if not OPENAI_API_KEY:
        print("\n⚠️  WARNING: OPENAI_API_KEY not found!")
        print("   Please set OPENAI_API_KEY in your .env file or environment variables.")
        print("   The script needs this to generate embeddings for training examples.")
        print("\n   Example .env file:")
        print("   OPENAI_API_KEY=sk-...")
        return
    
    try:
        # Initialize collection
        print("\n1. Initializing Qdrant collection...")
        created = initialize_db()
        if created:
            print("   ✅ Collection created")
        else:
            print("   ℹ️  Collection already exists")
        
        # Load training examples
        print("\n2. Loading training examples into vector DB...")
        count = bulk_load_training_examples()
        if count > 0:
            print(f"   ✅ Loaded {count} training examples")
        else:
            print("   ⚠️  No training examples loaded. Check that:")
            print("      - Training example files exist in prompts/training_examples/")
            print("      - Files are in the correct format")
            print("      - OPENAI_API_KEY is valid")
        
        print(f"\n{'='*60}")
        print("Vector DB initialization complete!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

