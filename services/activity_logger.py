"""Activity logging service using SQLite for tracking assistant creation and AI content generation."""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any


# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "activity_log.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection, creating the database if needed."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn


def initialize_db() -> None:
    """Initialize the database schema if not exists."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create assistants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS created_assistants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vapi_assistant_id TEXT UNIQUE NOT NULL,
            assistant_name TEXT NOT NULL,
            template_assistant_id TEXT,
            user_email TEXT,
            user_id TEXT,
            variables_json TEXT,
            faq_prompt TEXT,
            explain_due_message TEXT,
            retention_days INTEGER DEFAULT 14,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            deleted_at TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE
        )
    """)

    # Create FAQ generations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faq_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_assistant_id TEXT,
            user_email TEXT,
            input_faqs_json TEXT NOT NULL,
            generated_prompt TEXT NOT NULL,
            was_accepted BOOLEAN DEFAULT FALSE,
            accepted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create explain due refinements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS explain_due_refinements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_assistant_id TEXT,
            user_email TEXT,
            original_message TEXT NOT NULL,
            refinement_instructions TEXT NOT NULL,
            refined_message TEXT NOT NULL,
            was_accepted BOOLEAN DEFAULT FALSE,
            accepted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Initialize database on module import
initialize_db()


def log_assistant_creation(
    vapi_assistant_id: str,
    assistant_name: str,
    template_assistant_id: Optional[str] = None,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None,
    faq_prompt: Optional[str] = None,
    explain_due_message: Optional[str] = None,
    retention_days: int = 14
) -> int:
    """
    Log an assistant creation event.

    Args:
        vapi_assistant_id: The VAPI ID of the created assistant
        assistant_name: Name given to the assistant
        template_assistant_id: ID of the template assistant used
        user_email: Email of the user who created it
        user_id: Firebase UID of the user
        variables: Dict of variable name -> value used
        faq_prompt: Custom FAQ prompt if any
        explain_due_message: Custom explain due message if any
        retention_days: How long to keep the assistant (0 = indefinitely)

    Returns:
        The ID of the created log entry
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Calculate expiry date (None if retention_days is 0 = keep indefinitely)
    expires_at = None
    if retention_days > 0:
        expires_at = datetime.now() + timedelta(days=retention_days)

    cursor.execute("""
        INSERT INTO created_assistants (
            vapi_assistant_id, assistant_name, template_assistant_id,
            user_email, user_id, variables_json, faq_prompt, explain_due_message,
            retention_days, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vapi_assistant_id,
        assistant_name,
        template_assistant_id,
        user_email,
        user_id,
        json.dumps(variables) if variables else None,
        faq_prompt,
        explain_due_message,
        retention_days,
        expires_at.isoformat() if expires_at else None
    ))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return log_id


def log_faq_generation(
    template_assistant_id: str,
    user_email: Optional[str],
    input_faqs: List[Dict[str, str]],
    generated_prompt: str
) -> int:
    """
    Log an FAQ generation request.

    Args:
        template_assistant_id: ID of the template assistant
        user_email: Email of the user
        input_faqs: List of FAQ dicts with 'trigger' and 'instruction'
        generated_prompt: The generated FAQ prompt

    Returns:
        The ID of the created log entry
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO faq_generations (
            template_assistant_id, user_email, input_faqs_json, generated_prompt
        ) VALUES (?, ?, ?, ?)
    """, (
        template_assistant_id,
        user_email,
        json.dumps(input_faqs),
        generated_prompt
    ))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return log_id


def log_explain_due_refinement(
    template_assistant_id: str,
    user_email: Optional[str],
    original_message: str,
    refinement_instructions: str,
    refined_message: str
) -> int:
    """
    Log an explain due refinement request.

    Args:
        template_assistant_id: ID of the template assistant
        user_email: Email of the user
        original_message: The original explain due message
        refinement_instructions: User's instructions for refinement
        refined_message: The AI-refined message

    Returns:
        The ID of the created log entry
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO explain_due_refinements (
            template_assistant_id, user_email, original_message,
            refinement_instructions, refined_message
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        template_assistant_id,
        user_email,
        original_message,
        refinement_instructions,
        refined_message
    ))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return log_id


def mark_faq_accepted(generation_id: int, add_to_training: bool = True) -> None:
    """
    Mark an FAQ generation as accepted by the user.

    Args:
        generation_id: ID of the FAQ generation record
        add_to_training: If True, also add to vector DB for training feedback
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get the FAQ data first (for training feedback)
    cursor.execute("SELECT * FROM faq_generations WHERE id = ?", (generation_id,))
    row = cursor.fetchone()

    cursor.execute("""
        UPDATE faq_generations
        SET was_accepted = TRUE, accepted_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), generation_id))

    conn.commit()
    conn.close()

    # Add to vector DB for training feedback
    if add_to_training and row:
        try:
            from services.vector_db import add_user_accepted_faq
            input_faqs = json.loads(row["input_faqs_json"]) if row["input_faqs_json"] else []
            generated_prompt = row["generated_prompt"]
            user_email = row["user_email"]

            add_user_accepted_faq(
                input_faqs=input_faqs,
                generated_prompt=generated_prompt,
                user_email=user_email
            )
        except Exception as e:
            # Don't fail if training feedback fails
            print(f"Warning: Failed to add FAQ to training set: {e}")


def mark_explain_due_accepted(refinement_id: int) -> None:
    """Mark an explain due refinement as accepted by the user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE explain_due_refinements
        SET was_accepted = TRUE, accepted_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), refinement_id))

    conn.commit()
    conn.close()


def get_expired_assistants() -> List[Dict[str, Any]]:
    """
    Get all assistants that have expired and haven't been deleted yet.

    Returns:
        List of assistant records that are past their expiry date
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM created_assistants
        WHERE is_deleted = FALSE
          AND expires_at IS NOT NULL
          AND expires_at < ?
    """, (datetime.now().isoformat(),))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def mark_assistant_deleted(vapi_assistant_id: str) -> None:
    """Mark an assistant as deleted in the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE created_assistants
        SET is_deleted = TRUE, deleted_at = ?
        WHERE vapi_assistant_id = ?
    """, (datetime.now().isoformat(), vapi_assistant_id))

    conn.commit()
    conn.close()


def get_accepted_faqs(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all accepted FAQ generations for training feedback.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of accepted FAQ generation records
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM faq_generations
        WHERE was_accepted = TRUE
        ORDER BY accepted_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_accepted_explain_dues(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all accepted explain due refinements for training feedback.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of accepted explain due refinement records
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM explain_due_refinements
        WHERE was_accepted = TRUE
        ORDER BY accepted_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_all_created_assistants(include_deleted: bool = False) -> List[Dict[str, Any]]:
    """
    Get all assistants created via the app.

    Args:
        include_deleted: Whether to include deleted assistants

    Returns:
        List of assistant records
    """
    conn = get_connection()
    cursor = conn.cursor()

    if include_deleted:
        cursor.execute("SELECT * FROM created_assistants ORDER BY created_at DESC")
    else:
        cursor.execute("""
            SELECT * FROM created_assistants
            WHERE is_deleted = FALSE
            ORDER BY created_at DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
