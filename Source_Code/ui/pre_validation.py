# ==========================================================
# Validate Customer Name
# ==========================================================

import re

def validate_customer_name(
    customer_name: str
):

    if not customer_name.strip():

        return (
            False,
            "Customer Name is required."
        )

    return True, None


# ==========================================================
# Validate Customer Email
# ==========================================================

def is_valid_email(email):

    pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}$"
    )

    return re.match(pattern, email)

def validate_customer_email(
    customer_email: str
):

    if not customer_email.strip():

        return (
            False,
            "Customer Email is required."
        )

    if not is_valid_email(
        customer_email
    ):

        return (
            False,
            "Please enter a valid email address."
        )

    return True, None

# ==========================================================
# Validate Customer Ticket ID
# ==========================================================

def validate_ticket_id(
    ticket_id: str
):

    # Ticket ID is optional

    if not ticket_id:

        return True, None

    ticket_id = ticket_id.strip().upper()

    pattern = r"^INC\d{10}$"

    if not re.match(
        pattern,
        ticket_id
    ):

        return (
            False,
            "Ticket ID must be in format INCxxxxxxxxxx."
        )

    return True, None

# ==========================================================
# Validate All Inputs
# ==========================================================

def validate_session_inputs(
    customer_name: str,
    customer_email: str,
    ticket_id: str
):
    validators = [
        validate_customer_name(
            customer_name
        ),
        validate_customer_email(
            customer_email
        ),
        validate_ticket_id(
            ticket_id
        )
    ]

    for is_valid, error in validators:
        if not is_valid:
            return (
                False,
                error
            )

    return (
        True,
        None
    )