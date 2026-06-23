import re
from typing import Optional
import sqlite3
from pathlib import Path
from langchain_core.tools import tool
from logs.logger import logger

PROJECT_ROOT = Path(__file__).parent.parent

CUSTOMER_DB = (
        PROJECT_ROOT
        / "data"
        / "db"
        / "customer_support.sqlite"
    )

# ==========================================================
# Extract Ticket ID From User Query
# ==========================================================

def extract_ticket_id(
    user_query: str
):

    user_query = user_query.upper()

    match = re.search(
        r"\bINC\d{10}\b",
        user_query
    )

    if match:

        return match.group(0), True

    if "INC" in user_query:

        return None, False

    return None, None

# ==========================================================
# Resolve Ticket ID conflict in case 2 different IDs found
# ==========================================================

def resolve_ticket_id(
    ui_ticket_id: Optional[str],
    user_query: str
):

    query_ticket_id, query_valid = (
        extract_ticket_id(user_query)
    )

    # --------------------------------------
    # Valid ticket found in query
    # --------------------------------------

    if query_valid is True:

        return query_ticket_id, True

    # --------------------------------------
    # Invalid ticket in query
    # --------------------------------------

    if query_valid is False:

        if ui_ticket_id:

            return ui_ticket_id, False

        return None, False

    # --------------------------------------
    # No ticket in query
    # --------------------------------------

    if ui_ticket_id:

        return ui_ticket_id, True

    return None, None

# ==========================================================
# Ticket Lookup
# ==========================================================

def get_ticket(ticket_id):
    conn = sqlite3.connect(CUSTOMER_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            ticket_id,
            customer_name,
            customer_email,
            ticket_description,
            status,
            customer_comments,
            tech_comments,
            created_at,
            updated_at
        FROM support_tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,)
    )
    ticket = cursor.fetchone()
    conn.close()
    return ticket

# ==========================================================
# Load Ticket Context & Return in Dict
# ==========================================================

def load_ticket_context_dict(
    ticket
):

    (
        ticket_id,
        customer_name,
        customer_email,
        ticket_description,
        ticket_status,
        customer_comments,
        tech_comments,
        created_at,
        updated_at
    ) = ticket

    return {
        "ticket_id":
            str(ticket_id),

        "customer_name":
            customer_name,

        "customer_email":
            customer_email,

        "ticket_description":
            ticket_description,

        "ticket_status":
            ticket_status,

        "customer_comments":
            customer_comments,

        "tech_comments":
            tech_comments,

        "created_at":
            created_at,

        "updated_at":
            updated_at
    }

# ==========================================================
# Update Ticket Status - Positive Handler
# ==========================================================

def update_ticket_status(
    ticket_id: str,
    status: str
):

    conn = sqlite3.connect(
        CUSTOMER_DB
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE support_tickets
        SET
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE ticket_id = ?
        """,
        (
            status,
            ticket_id
        )
    )

    conn.commit()
    conn.close()

# ===============================================================================
# Create a Tool to Lookup Ticket for LLM (Inquiry Agent & Negative Handler Agent)
# ===============================================================================

@tool
def lookup_ticket(
    ticket_id: str
):
    """
    Retrieve ticket details for a given ticket ID.
    """

    ticket = get_ticket(ticket_id)

    if not ticket:

        return {
            "found": False,
            "ticket_id": ticket_id
        }

    ticket_context = (
        load_ticket_context_dict(
            ticket
        )
    )

    return {
        "found": True,
        **ticket_context
    }

# ===============================================================================
# Generate New Ticket ID to be inserted into DB upon Ticket Creation
# ===============================================================================

def generate_ticket_id():

    conn = sqlite3.connect(
        CUSTOMER_DB
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticket_id
        FROM support_tickets
        """
    )

    tickets = cursor.fetchall()

    conn.close()

    # First Ticket
    if not tickets:

        return "INC0000000001"

    max_number = max(
        int(
            ticket[0].replace(
                "INC",
                ""
            )
        )
        for ticket in tickets
    )

    next_number = max_number + 1

    return (
        f"INC{next_number:010d}"
    )

# ===============================================================================
# Create a Tool to Create a Ticket for LLM (Negative Handler Agent)
# ===============================================================================

# ------------------------------------
# Create New Ticket
# ------------------------------------
def insert_ticket(
    customer_name: str,
    customer_email: str,
    ticket_description: str
):

    ticket_id = generate_ticket_id()

    conn = sqlite3.connect(
        CUSTOMER_DB
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO support_tickets
        (
            ticket_id,
            customer_name,
            customer_email,
            ticket_description,
            status,
            customer_comments,
            tech_comments
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            ticket_id,
            customer_name,
            customer_email,
            ticket_description,

            # Default Status
            "Open",

            # Initial Customer Comment
            ticket_description,

            # Technical Team Comments
            None
        )
    )

    conn.commit()

    conn.close()

    return {
        "ticket_id": ticket_id,
        "status": "Open"
    }


from langchain.tools import tool

# -------------------------------------------------------
# Define Tool - Create Ticket for Negative Handler Agent
# -------------------------------------------------------

@tool
def create_ticket(
    customer_name: str,
    customer_email: str,
    ticket_description: str
):
    """
    Create a new customer support ticket.

    Use when:
    - Customer reports a new issue.
    - A previously resolved issue has reoccurred.
    """

    return insert_ticket(
                            customer_name=customer_name,
                            customer_email=customer_email,
                            ticket_description=ticket_description
                        )

# =========================================================
# Add to Execution Trace
# ==========================================================

def add_trace(
    execution_trace: list[str],
    agent_name: str,
    details: list[str]
):

    execution_trace.append(
        f"========== {agent_name.upper()}: TRACE START =========="
    )

    execution_trace.extend(details)

    execution_trace.append(
        f"========== {agent_name.upper()}: TRACE END ==========\n"
    )

    # Persist to log file
    logger.info(
        f"{agent_name} | "
        + " | ".join(details)
    )

















































































