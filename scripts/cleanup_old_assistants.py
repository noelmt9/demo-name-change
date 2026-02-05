#!/usr/bin/env python3
"""
Manual cleanup script for deleting expired assistants from VAPI.

Run this script manually when you want to clean up assistants that have
passed their retention period.

Usage:
    python scripts/cleanup_old_assistants.py [--dry-run]

Options:
    --dry-run    Show what would be deleted without actually deleting
"""

import sys
import os
from datetime import datetime

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import activity_logger
from services import vapi


def cleanup_expired_assistants(dry_run: bool = False) -> dict:
    """
    Delete all assistants that have passed their expiry date.

    Args:
        dry_run: If True, only show what would be deleted without deleting

    Returns:
        Dict with counts of deleted, failed, and skipped assistants
    """
    results = {
        "deleted": 0,
        "failed": 0,
        "skipped": 0,
        "details": []
    }

    # Get all expired assistants
    expired = activity_logger.get_expired_assistants()

    if not expired:
        print("No expired assistants found.")
        return results

    print(f"Found {len(expired)} expired assistant(s):\n")

    for assistant in expired:
        vapi_id = assistant["vapi_assistant_id"]
        name = assistant["assistant_name"]
        created_at = assistant["created_at"]
        expires_at = assistant["expires_at"]
        retention_days = assistant["retention_days"]

        print(f"  - {name}")
        print(f"    VAPI ID: {vapi_id}")
        print(f"    Created: {created_at}")
        print(f"    Expired: {expires_at}")
        print(f"    Retention: {retention_days} days")

        if dry_run:
            print(f"    [DRY RUN] Would delete this assistant\n")
            results["skipped"] += 1
            results["details"].append({
                "id": vapi_id,
                "name": name,
                "status": "skipped (dry run)"
            })
            continue

        # Try to delete from VAPI
        try:
            vapi.delete_assistant(vapi_id)
            print(f"    [DELETED] Successfully deleted from VAPI\n")

            # Mark as deleted in our database
            activity_logger.mark_assistant_deleted(vapi_id)

            results["deleted"] += 1
            results["details"].append({
                "id": vapi_id,
                "name": name,
                "status": "deleted"
            })

        except Exception as e:
            error_msg = str(e)
            print(f"    [FAILED] {error_msg}\n")

            # If the assistant doesn't exist in VAPI (404), still mark as deleted locally
            if "404" in error_msg or "not found" in error_msg.lower():
                activity_logger.mark_assistant_deleted(vapi_id)
                print(f"    [INFO] Marked as deleted locally (not found in VAPI)\n")
                results["deleted"] += 1
                results["details"].append({
                    "id": vapi_id,
                    "name": name,
                    "status": "deleted (not found in VAPI)"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "id": vapi_id,
                    "name": name,
                    "status": f"failed: {error_msg}"
                })

    return results


def print_summary(results: dict) -> None:
    """Print a summary of the cleanup operation."""
    print("\n" + "=" * 50)
    print("CLEANUP SUMMARY")
    print("=" * 50)
    print(f"  Deleted:  {results['deleted']}")
    print(f"  Failed:   {results['failed']}")
    print(f"  Skipped:  {results['skipped']}")
    print("=" * 50)


def main():
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("VAPI Assistant Cleanup Script")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if dry_run:
        print("Mode: DRY RUN (no deletions will occur)")
    else:
        print("Mode: LIVE (will delete expired assistants)")
    print("=" * 50 + "\n")

    try:
        results = cleanup_expired_assistants(dry_run=dry_run)
        print_summary(results)

        # Exit with error code if any failures
        if results["failed"] > 0:
            sys.exit(1)

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
