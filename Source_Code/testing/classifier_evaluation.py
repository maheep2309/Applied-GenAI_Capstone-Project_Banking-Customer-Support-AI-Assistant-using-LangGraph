import os, sqlite3, json
from pathlib import Path

from llm.llm_models import *
from testing.test_cases import *

PROJECT_ROOT = Path(__file__).parent.parent

CUSTOMER_DB = (
        PROJECT_ROOT
        / "data"
        / "db"
        / "customer_support.sqlite"
    )

# ==========================================================
# Intent Classification Evaluation Function
# ==========================================================

def run_classifier_evaluation():

    conn = sqlite3.connect(CUSTOMER_DB)

    cursor = conn.cursor()

    # ------------------------------------------------------
    # Clear Existing Results
    # ------------------------------------------------------

    cursor.execute(
        """
        DELETE FROM intent_classifier_test_results
        """
    )

    # ------------------------------------------------------
    # Execute Test Cases
    # ------------------------------------------------------

    for test_case in CLASSIFIER_TEST_CASES:

        category = (
            test_case["category"]
        )

        query = (
            test_case["query"]
        )

        expected_intent = (
            test_case["expected_intent"]
        )

        # --------------------------------------------------
        # Invoke Intent Classifier
        # --------------------------------------------------

        try:

            result = (
                llm_classifier_chain.invoke(
                    {
                        "ticket_id": None,
                        "conversation_history": [],
                        "customer_query": query
                    }
                )
            )

            actual_intent = (
                result.intent.lower() # type: ignore
            )

        except Exception:

            actual_intent = "ERROR"

        # --------------------------------------------------
        # Determine Pass / Fail
        # --------------------------------------------------

        test_result = (
            "Pass"
            if actual_intent == expected_intent
            else "Fail"
        )

        # --------------------------------------------------
        # Save Result
        # --------------------------------------------------

        cursor.execute(
            """
            INSERT INTO intent_classifier_test_results (

                category,
                query,
                expected_intent,
                actual_intent,
                test_result

            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                category,
                query,
                expected_intent,
                actual_intent,
                test_result
            )
        )

    conn.commit()

    conn.close()

    print(
        "[SUCCESS] Classifier Evaluation Completed"
    )

# ==========================================================
# Get Classifier Evaluation Summary
# ==========================================================

def get_classifier_summary():

    conn = sqlite3.connect(CUSTOMER_DB)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            COUNT(*) AS total_tests,

            SUM(
                CASE
                    WHEN test_result = 'Pass'
                    THEN 1
                    ELSE 0
                END
            ) AS passed_tests,

            SUM(
                CASE
                    WHEN test_result = 'Fail'
                    THEN 1
                    ELSE 0
                END
            ) AS failed_tests,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN test_result = 'Pass'
                        THEN 1
                        ELSE 0
                    END
                ) /
                COUNT(*),
                2
            ) AS accuracy

        FROM intent_classifier_test_results
        """
    )

    result = dict(
        cursor.fetchone()
    )

    conn.close()

    return result


# ==========================================================
# Get Classifier Evaluation Results
# ==========================================================

def get_classifier_results():

    conn = sqlite3.connect(CUSTOMER_DB)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM intent_classifier_test_results
        ORDER BY test_id
        """
    )

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return results