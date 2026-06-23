import os, sqlite3, json
from pathlib import Path


# ==========================================================
# Create Data Directory
# ==========================================================

PROJECT_ROOT = Path(__file__).parent.parent

CUSTOMER_DB = (
        PROJECT_ROOT
        / "data"
        / "db"
        / "customer_support.sqlite"
    )

# ==========================================================
# Customer Support Database
# ==========================================================

def create_customer_support_db():

    conn = sqlite3.connect(CUSTOMER_DB)
    cursor = conn.cursor()

    # ------------------------------------------------------
    # Create Table - Support Tickets
    # ------------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (

        ticket_id TEXT PRIMARY KEY,

        customer_name TEXT NOT NULL,

        customer_email TEXT NOT NULL,

        ticket_description TEXT NOT NULL,

        status TEXT DEFAULT 'Open'
            CHECK (
                status IN (
                    'Open',
                    'In-progress',
                    'Waiting user information',
                    'Resolved'
                )
            ),

        customer_comments TEXT,

        tech_comments TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ------------------------------------------------------
    # Create Table - Evaluation Results
    # ------------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_results (

        evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        thread_id TEXT,
        
        customer_email TEXT,

        query TEXT NOT NULL,

        final_response TEXT,

        intent TEXT NOT NULL,

        workflow_ticket_action TEXT NOT NULL,

        overall_score REAL,

        judge_passed INTEGER,

        reflection_count INTEGER,

        intent_handling_score INTEGER,
        intent_handling_reasoning TEXT,

        workflow_compliance_score INTEGER,
        workflow_compliance_reasoning TEXT,

        customer_experience_score INTEGER,
        customer_experience_reasoning TEXT,

        groundedness_score INTEGER,
        groundedness_reasoning TEXT,

        failed_params TEXT,

        judge_strengths TEXT,

        judge_improvements TEXT
    )
    """)

    # ------------------------------------------------------
    # Create Table - Classifier Test Results
    # ------------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intent_classifier_test_results (

        test_id INTEGER PRIMARY KEY AUTOINCREMENT,

        category TEXT NOT NULL,

        query TEXT NOT NULL,

        expected_intent TEXT NOT NULL,

        actual_intent TEXT NOT NULL DEFAULT '',

        test_result TEXT
            CHECK (
                test_result IN (
                    'Pass',
                    'Fail'
                )
            ),

        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ------------------------------------------------------
    # Create Table - CSAT
    # ------------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS csat (

        csat_id INTEGER PRIMARY KEY AUTOINCREMENT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        thread_id TEXT,

        customer_name TEXT NOT NULL,

        customer_email TEXT NOT NULL,

        active_ticket_id TEXT,

        intent_category TEXT NOT NULL,

        workflow_ticket_action TEXT,

        overall_score REAL,

        final_response TEXT,

        feedback_rating TEXT
            CHECK (
                feedback_rating IN (
                    'thumbs_up',
                    'thumbs_down',
                    'no_feedback'
                )
            ),

        feedback_comment TEXT

    )
    """)

    # ------------------------------------------------------
    # Seed Ticket Data in Support Tickets Table
    # ------------------------------------------------------

    cursor.executemany("""
    INSERT OR IGNORE INTO support_tickets (

        ticket_id,
        customer_name,
        customer_email,
        ticket_description,
        status,
        customer_comments,
        tech_comments,
        created_at,
        updated_at

    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dummy_tickets)

    conn.commit()
    conn.close()

    print(
        f"[SUCCESS] Created Database Objects: {CUSTOMER_DB}"
    )

# ==========================================================
# Save Evaluation Result
# ==========================================================

def save_evaluation_result(

    thread_id,
    customer_email,
    query,
    final_response,
    intent,
    workflow_ticket_action,
    overall_score,
    judge_passed,
    reflection_count,
    intent_handling_score,
    intent_handling_reasoning,
    workflow_compliance_score,
    workflow_compliance_reasoning,
    customer_experience_score,
    customer_experience_reasoning,
    groundedness_score,
    groundedness_reasoning,
    failed_params,
    judge_strengths,
    judge_improvements
):

    conn = sqlite3.connect(
        CUSTOMER_DB
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO evaluation_results (

            thread_id,

            customer_email,

            query,

            final_response,

            intent,

            workflow_ticket_action,

            overall_score,

            judge_passed,

            reflection_count,

            intent_handling_score,
            intent_handling_reasoning,

            workflow_compliance_score,
            workflow_compliance_reasoning,

            customer_experience_score,
            customer_experience_reasoning,

            groundedness_score,
            groundedness_reasoning,

            failed_params,

            judge_strengths,

            judge_improvements

        )

        VALUES (

            ?, ?, ?, ?, ?, ?,

            ?, ?, ?,

            ?, ?,

            ?, ?,

            ?, ?,

            ?, ?,

            ?, ?, ?

        )
        """,

        (

            thread_id,

            customer_email,

            query,

            final_response,

            intent,

            workflow_ticket_action,

            overall_score,

            int(judge_passed),

            reflection_count,

            intent_handling_score,
            intent_handling_reasoning,

            workflow_compliance_score,
            workflow_compliance_reasoning,

            customer_experience_score,
            customer_experience_reasoning,

            groundedness_score,
            groundedness_reasoning,

            json.dumps(failed_params),

            json.dumps(judge_strengths),

            json.dumps(judge_improvements)
        )
    )

    conn.commit()

    conn.close()

# ==========================================================
# Get Evaluation Results
# ==========================================================

def get_evaluation_results(limit=100):

    conn = sqlite3.connect(CUSTOMER_DB)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM evaluation_results
        ORDER BY evaluation_id DESC
        LIMIT ?
        """,
        (limit,)
    )

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return results


# ==========================================================
# Get Evaluation Summary
# ==========================================================

def get_evaluation_summary():

    conn = sqlite3.connect(CUSTOMER_DB)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            COUNT(*) AS total_evaluations,

            ROUND(
                AVG(overall_score),
                2
            ) AS avg_overall_score,

            ROUND(
                AVG(intent_handling_score),
                2
            ) AS avg_intent_score,

            ROUND(
                AVG(workflow_compliance_score),
                2
            ) AS avg_workflow_score,

            ROUND(
                AVG(customer_experience_score),
                2
            ) AS avg_customer_score,

            ROUND(
                AVG(groundedness_score),
                2
            ) AS avg_groundedness_score,

            ROUND(
                AVG(reflection_count),
                2
            ) AS avg_reflection_count,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN judge_passed = 1
                        THEN 1
                        ELSE 0
                    END
                ) /
                COUNT(*),
                2
            ) AS pass_rate

        FROM evaluation_results
        """
    )

    result = dict(
        cursor.fetchone()
    )

    conn.close()

    return result

# ==========================================================
# Save CSAT Feedback
# ==========================================================

def save_csat_feedback(
    thread_id,
    customer_name,
    customer_email,
    active_ticket_id,
    intent_category,
    workflow_ticket_action,
    overall_score,
    final_response,
    feedback_rating,
    feedback_comment=None
):

    conn = sqlite3.connect(CUSTOMER_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO csat (
            thread_id,
            customer_name,
            customer_email,
            active_ticket_id,
            intent_category,
            workflow_ticket_action,
            overall_score,
            final_response,
            feedback_rating,
            feedback_comment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thread_id,
            customer_name,
            customer_email,
            active_ticket_id,
            intent_category,
            workflow_ticket_action,
            overall_score,
            final_response,
            feedback_rating,
            feedback_comment
        )
    )
    conn.commit()
    conn.close()

# ==============================================================================================================================================
# Get Customer Profile
# ==============================================================================================================================================

def get_customer_profile(
    customer_email: str
):

    conn = sqlite3.connect(
        CUSTOMER_DB
    )

    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # Customer Interaction Metrics
    # ------------------------------------------------------------------

    cursor.execute(
        """
        SELECT

            COUNT(*) AS interaction_count,

            SUM(
                CASE
                    WHEN feedback_rating='thumbs_up'
                    THEN 1
                    ELSE 0
                END
            ) AS thumbs_up_count,

            SUM(
                CASE
                    WHEN feedback_rating='thumbs_down'
                    THEN 1
                    ELSE 0
                END
            ) AS thumbs_down_count,

            SUM(
                CASE
                    WHEN feedback_rating='no_feedback'
                    THEN 1
                    ELSE 0
                END
            ) AS no_feedback_count

        FROM csat

        WHERE customer_email = ?
        """,
        (
            customer_email,
        )
    )

    metrics = cursor.fetchone()

    # ------------------------------------------------------------------
    # Feedback History
    # ------------------------------------------------------------------

    cursor.execute(
        """
        SELECT

            feedback_rating,
            feedback_comment,
            intent_category,
            workflow_ticket_action,
            overall_score,
            active_ticket_id,
            created_at

        FROM csat

        WHERE customer_email = ?
        AND (
                feedback_comment IS NOT NULL
            AND TRIM(feedback_comment) <> ''
        )

        ORDER BY created_at DESC
        """,
        (
            customer_email,
        )
    )

    feedback_history = []

    for row in cursor.fetchall():

        feedback_history.append(

            {
                "rating":
                    row[0],

                "comment":
                    row[1],

                "intent":
                    row[2],

                "workflow_action":
                    row[3],

                "overall_score":
                    row[4],

                "ticket_id":
                    row[5],

                "created_at":
                    row[6]
            }
        )

    conn.close()

    return {

        "customer_email":
            customer_email,

        "interaction_count":
            metrics[0] or 0,

        "thumbs_up_count":
            metrics[1] or 0,

        "thumbs_down_count":
            metrics[2] or 0,

        "no_feedback_count":
            metrics[3] or 0,

        "feedback_history":
            feedback_history
    }

# ==============================================================================================================================================
# Get Customer Evaluation Profile
# ==============================================================================================================================================

def get_customer_evaluation_profile(
    customer_email: str
):

    conn = sqlite3.connect(
        CUSTOMER_DB
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *

        FROM evaluation_results

        WHERE customer_email = ?
        """,
        (
            customer_email,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    # --------------------------------------------------
    # Evaluation Count
    # --------------------------------------------------

    evaluation_count = len(
        rows
    )

    # --------------------------------------------------
    # Average Overall Score
    # --------------------------------------------------

    avg_overall_score = 0

    if evaluation_count > 0:

        avg_overall_score = round(

            sum(
                row["overall_score"] or 0

                for row in rows
            )

            / evaluation_count,

            2
        )

    # --------------------------------------------------
    # Historical Failure Patterns
    # --------------------------------------------------
    
    historical_queries = []

    # --------------------------------------------------
    # Historical Failure Patterns
    # --------------------------------------------------

    failed_parameter_counts = []

    # --------------------------------------------------
    # Judge Improvements
    # --------------------------------------------------

    judge_improvements = []

    # --------------------------------------------------
    # Process Historical Evaluations
    # --------------------------------------------------

    for row in rows:

        # ----------------------------------------------
        # User Queries
        # ----------------------------------------------      

        if row["query"]:

            historical_queries.append(
                row["query"]
            )
        
        # ----------------------------------------------
        # Failed Parameters
        # ----------------------------------------------

        try:

            failed_params = json.loads(

                row["failed_params"] or "[]"
            )

        except:

            failed_params = []

        failed_parameter_counts.extend(
            failed_params
        )

        # ----------------------------------------------
        # Judge Improvements
        # ----------------------------------------------

        try:

            improvements = json.loads(

                row["judge_improvements"] or "[]"
            )

        except:

            improvements = []

        judge_improvements.extend(
            improvements
        )

    # --------------------------------------------------
    # Return
    # --------------------------------------------------

    return {

        "evaluation_count":
            evaluation_count,

        "avg_overall_score":
            avg_overall_score,

        "failed_parameter_counts":
            failed_parameter_counts,

        "judge_improvements":
            judge_improvements,
        
        "historical_queries":
            historical_queries,
    }

# ==========================================================
# Create Dummy Data - support_tickets
# ==========================================================

dummy_tickets = [

    (
        "INC0000000001",
        "John Smith",
        "john.smith@gmail.com",
        "Debit card replacement has not been delivered after 10 business days.",
        "Open",
        "Customer followed up regarding card delivery delay.",
        "Replacement card dispatch verification pending.",
        "2026-06-01 09:15:00",
        "2026-06-01 09:15:00"
    ),

    (
        "INC0000000002",
        "Emma Johnson",
        "emma.j@gmail.com",
        "Unable to login to internet banking account despite entering correct credentials.",
        "Resolved",
        "Customer reported login failure on both mobile and desktop.",
        "Password reset completed and customer confirmed successful login.",
        "2026-06-02 10:30:00",
        "2026-06-03 15:45:00"
    ),

    (
        "INC0000000003",
        "Michael Brown",
        "michael.b@gmail.com",
        "Credit card transaction declined at merchant location.",
        "In-progress",
        "Customer confirmed sufficient credit limit available.",
        "Transaction review initiated with card operations team.",
        "2026-06-03 11:20:00",
        "2026-06-04 09:10:00"
    ),

    (
        "INC0000000004",
        "Olivia Davis",
        "olivia.d@gmail.com",
        "UPI payment debited but beneficiary did not receive funds.",
        "Resolved",
        "Customer requested urgent review as payment was for rent.",
        "Transaction reconciled and amount credited back to account.",
        "2026-06-04 08:45:00",
        "2026-06-05 13:25:00"
    ),

    (
        "INC0000000005",
        "William Wilson",
        "william.w@gmail.com",
        "Cheque book request submitted online but not yet received.",
        "Waiting user information",
        "Customer unsure if registered mailing address is correct.",
        "Awaiting customer confirmation of registered mailing address.",
        "2026-06-05 14:00:00",
        "2026-06-06 10:40:00"
    ),

    (
        "INC0000000006",
        "Sophia Taylor",
        "sophia.t@gmail.com",
        "Mobile banking application closes unexpectedly during login.",
        "Open",
        "Customer contacted support three times regarding the issue.",
        "Issue assigned to digital banking support team.",
        "2026-06-06 09:00:00",
        "2026-06-06 09:00:00"
    ),

    (
        "INC0000000007",
        "James Anderson",
        "james.a@gmail.com",
        "Unable to download account statement for the last quarter.",
        "Resolved",
        "Customer required statement for income tax filing.",
        "Statement generated and shared via registered email address.",
        "2026-06-07 12:30:00",
        "2026-06-07 16:20:00"
    ),

    (
        "INC0000000008",
        "Isabella Thomas",
        "isabella.t@gmail.com",
        "International debit card transaction blocked while travelling abroad.",
        "In-progress",
        "Customer expressed frustration due to lack of access to funds.",
        "Card usage restrictions under review by risk management team.",
        "2026-06-08 08:10:00",
        "2026-06-08 17:45:00"
    ),

    (
        "INC0000000009",
        "Benjamin Jackson",
        "ben.jackson@gmail.com",
        "Loan EMI payment reflected in account but loan balance not updated.",
        "Open",
        "Customer concerned about impact on credit history.",
        "Loan servicing team investigating account reconciliation.",
        "2026-06-08 11:15:00",
        "2026-06-08 11:15:00"
    ),

    (
        "INC0000000010",
        "Mia White",
        "mia.white@gmail.com",
        "ATM cash withdrawal failed but amount was debited from account.",
        "Resolved",
        "Customer reported cash was required urgently during travel.",
        "Failed ATM transaction reversed successfully.",
        "2026-06-09 07:55:00",
        "2026-06-09 15:30:00"
    ),

    (
        "INC0000000011",
        "Lucas Harris",
        "lucas.h@gmail.com",
        "Requested credit card limit enhancement has not been processed.",
        "In-progress",
        "Customer submitted supporting income documents last week.",
        "Eligibility assessment currently in progress.",
        "2026-06-09 10:10:00",
        "2026-06-10 09:45:00"
    ),

    (
        "INC0000000012",
        "Charlotte Martin",
        "charlotte.m@gmail.com",
        "Unable to add a new beneficiary for fund transfer.",
        "Open",
        "Customer receives an error after OTP verification.",
        "Beneficiary registration logs under investigation.",
        "2026-06-10 13:20:00",
        "2026-06-10 13:20:00"
    ),

    (
        "INC0000000013",
        "Henry Thompson",
        "henry.t@gmail.com",
        "Duplicate debit observed for a single POS transaction.",
        "Resolved",
        "Customer shared transaction screenshots for verification.",
        "Duplicate transaction reversed and account corrected.",
        "2026-06-10 08:25:00",
        "2026-06-11 14:05:00"
    ),

    (
        "INC0000000014",
        "Amelia Garcia",
        "amelia.g@gmail.com",
        "Fixed deposit account opening request remains pending.",
        "Waiting user information",
        "Customer has not yet uploaded requested KYC documents.",
        "Additional KYC documents required from customer.",
        "2026-06-11 16:10:00",
        "2026-06-12 09:50:00"
    ),

    (
        "INC0000000015",
        "Alexander Martinez",
        "alex.m@gmail.com",
        "Unable to generate debit card PIN through mobile banking.",
        "Open",
        "Customer attempted PIN generation multiple times without success.",
        "PIN generation service issue escalated to card support team.",
        "2026-06-12 10:45:00",
        "2026-06-12 10:45:00"
    ),

    (
        "INC0000000016",
        "Evelyn Robinson",
        "evelyn.r@gmail.com",
        "Loan closure certificate requested but not yet received.",
        "Resolved",
        "Customer requires certificate for property sale documentation.",
        "Closure certificate sent to registered email address.",
        "2026-06-12 11:35:00",
        "2026-06-13 12:40:00"
    ),

    (
        "INC0000000017",
        "Daniel Clark",
        "daniel.c@gmail.com",
        "UPI transaction limit exceeded message displayed incorrectly.",
        "In-progress",
        "Customer reports transaction value was well below the limit.",
        "UPI transaction logs being reviewed.",
        "2026-06-13 09:20:00",
        "2026-06-13 17:15:00"
    ),

    (
        "INC0000000018",
        "Harper Rodriguez",
        "harper.r@gmail.com",
        "Credit card reward points not credited for eligible purchases.",
        "Open",
        "Customer identified multiple transactions missing reward points.",
        "Rewards processing team reviewing transaction eligibility.",
        "2026-06-13 15:40:00",
        "2026-06-13 15:40:00"
    ),

    (
        "INC0000000019",
        "Matthew Lewis",
        "matthew.l@gmail.com",
        "Address change request submitted but account details not updated.",
        "Waiting user information",
        "Customer has not provided updated address proof document.",
        "Proof of address document required for verification.",
        "2026-06-14 08:00:00",
        "2026-06-14 09:30:00"
    ),

    (
        "INC0000000020",
        "Ella Lee",
        "ella.lee@gmail.com",
        "Annual fee charged on credit card despite fee waiver eligibility.",
        "Resolved",
        "Customer believes annual spending criteria were met.",
        "Fee reversal approved and credited to card account.",
        "2026-06-14 10:15:00",
        "2026-06-14 14:50:00"
    )

]