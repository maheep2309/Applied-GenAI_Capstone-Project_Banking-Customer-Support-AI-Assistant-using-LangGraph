import streamlit as st
import sqlite3, json
import pandas as pd
from pathlib import Path
from ui.pre_validation import *
from graph.workflow import build_graph
from data.database import *
from graph.utils import *
from data.database import *
from testing.classifier_evaluation import *

def run_app():

    # ==========================================================
    # Database Configuration
    # ==========================================================

    PROJECT_ROOT = Path(__file__).parent.parent

    CUSTOMER_DB = (
        PROJECT_ROOT
        / "data"
        / "db"
        / "customer_support.sqlite"
    )
    
    #create_customer_support_db()

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
    # Load Ticket Context
    # ==========================================================

    def load_ticket_context(ticket):
        (
            ticket_id_db,
            customer_name_db,
            customer_email_db,
            ticket_description,
            ticket_status,
            customer_comments,
            tech_comments,
            created_at,
            updated_at
        ) = ticket

        st.session_state.ticket_found = True
        st.session_state.ticket_id = str(ticket_id_db)
        st.session_state.ticket_status = ticket_status
        st.session_state.ticket_description = ticket_description
        st.session_state.customer_comments = customer_comments
        st.session_state.tech_comments = tech_comments
        st.session_state.created_at = created_at
        st.session_state.updated_at = updated_at

    # ==========================================================
    # Thread ID Generator
    # ==========================================================

    def generate_thread_id(
        customer_name,
        customer_email
    ):

        return (
            f"{customer_name.strip().lower().replace(' ', '_')}_"
            f"{customer_email.strip().lower()}"
        )

    # ==========================================================
    # Reset Session
    # ==========================================================

    def reset_session():

        for key in list(
            st.session_state.keys()
        ):
            del st.session_state[key]

        initialize_session_state()

    # ==========================================================
    # Reset Current Evaluation State
    # ==========================================================

    def reset_current_evaluation_state():

        st.session_state.reflection_count = 0
        st.session_state.judge_passed = False
        st.session_state.failed_params = []
        st.session_state.judge_strengths = []
        st.session_state.judge_improvements = []
        st.session_state.overall_score = None
        st.session_state.intent_handling_score = None
        st.session_state.intent_handling_reasoning = ""
        st.session_state.workflow_compliance_score = None
        st.session_state.workflow_compliance_reasoning = ""
        st.session_state.customer_experience_score = None
        st.session_state.customer_experience_reasoning = ""
        st.session_state.groundedness_score = None
        st.session_state.groundedness_reasoning = ""
        st.session_state.workflow_ticket_action = ""
        st.session_state.customer_satisfaction_summary = ""
        st.session_state.customer_issue_profile = ""
        st.session_state.customer_communication_profile = ""
        st.session_state.customer_response_guidance = ""
        st.session_state.customer_sensitivity = ""

    # ==========================================================
    # Build Welcome Message
    # ==========================================================

    def build_welcome_message():

        if st.session_state.ticket_id:

            tech_comments = (
                st.session_state.tech_comments
                if st.session_state.tech_comments
                else "None"
            )

            return f"""
                    Welcome {st.session_state.customer_name}.

                    I found your existing ticket details below:

                    | Field | Value |
                    |---------|---------|
                    | 🎫 Ticket ID | {st.session_state.ticket_id} |
                    | 📌 Status | {st.session_state.ticket_status} |
                    | 📝 Issue Description | {st.session_state.ticket_description} |
                    | 🔧 Tech Notes | {tech_comments} |
                    | 📅 Created | {st.session_state.created_at} |
                    | 🔄 Last Updated | {st.session_state.updated_at} |

                    How may I assist you today?
                    """

        return f"""
                Welcome {st.session_state.customer_name}.

                How may I assist you today?
                """
    # ====================================================================================================================================================
    # Process User Message - Call Graph
    # ====================================================================================================================================================

    def process_user_message():

        graph_input = {

            "thread_id":
                st.session_state.thread_id,
                
            "customer_name":
                st.session_state.customer_name,

            "customer_email":
                st.session_state.customer_email,

            "ticket_id":
                st.session_state.ticket_id,

            "current_user_query":
                st.session_state.current_user_query,

            "ticket_status":
                st.session_state.ticket_status,

            "ticket_description":
                st.session_state.ticket_description,

            "customer_comments":
                st.session_state.customer_comments,

            "tech_comments":
                st.session_state.tech_comments,

            "created_at":
                st.session_state.created_at,

            "updated_at":
                st.session_state.updated_at,

            "execution_trace":
                st.session_state.execution_trace,
            
            "evaluation_history":
                st.session_state.evaluation_history,

            "reflection_count":
                0
        }

        # ------------------------------------------------------
        # Add Trace
        # ------------------------------------------------------
               
        add_trace(
            st.session_state.execution_trace,
            "UI Graph",
            [
                "Invoking Graph...."
            ]
        )
        
        # ------------------------------------------------------
        # Invoke LangGraph
        # ------------------------------------------------------

        result = st.session_state.graph.invoke(
            graph_input,  # type: ignore
            config={
                "configurable": {
                    "thread_id":
                        st.session_state.thread_id
                }
            }
        )

        if result.get("ticket_id"):
            st.session_state.ticket_id = (
                result["ticket_id"]
            )

        # ------------------------------------------------------
        # Store Results
        # ------------------------------------------------------

        st.session_state.final_response = (
            result.get(
                "final_response",
                ""
            )
        )

        st.session_state.execution_trace = (
            result.get(
                "execution_trace",
                []
            )
        )

        st.session_state.intent = (
            result.get(
                "intent",
                ""
            )
        )

        st.session_state.workflow_ticket_action = (
            result.get(
                "workflow_ticket_action",
                ""
            )
        )

        st.session_state.intent_handling_score = (
            result.get(
                "intent_handling_score"
            )
        )

        st.session_state.intent_handling_reasoning = (
            result.get(
                "intent_handling_reasoning",
                ""
            )
        )

        st.session_state.workflow_compliance_score = (
            result.get(
                "workflow_compliance_score"
            )
        )

        st.session_state.workflow_compliance_reasoning = (
            result.get(
                "workflow_compliance_reasoning",
                ""
            )
        )

        st.session_state.customer_experience_score = (
            result.get(
                "customer_experience_score"
            )
        )

        st.session_state.customer_experience_reasoning = (
            result.get(
                "customer_experience_reasoning",
                ""
            )
        )

        st.session_state.groundedness_score = (
            result.get(
                "groundedness_score"
            )
        )

        st.session_state.groundedness_reasoning = (
            result.get(
                "groundedness_reasoning",
                ""
            )
        )

        st.session_state.overall_score = (
            result.get(
                "overall_score"
            )
        )

        st.session_state.judge_strengths = (
            result.get(
                "judge_strengths",
                []
            )
        )

        st.session_state.judge_improvements = (
            result.get(
                "judge_improvements",
                []
            )
        )

        st.session_state.judge_passed = (
            result.get(
                "judge_passed",
                False
            )
        )

        st.session_state.failed_params = (
            result.get(
                "failed_params",
                []
            )
        )

        st.session_state.reflection_count = (
            result.get(
                "reflection_count",
                0
            )
        )

        st.session_state.evaluation_history = (
            result.get(
                "evaluation_history",
                []
            )
        )

        st.session_state.customer_satisfaction_summary = (
            result.get(
                "customer_satisfaction_summary",
                ""
            )
        )

        st.session_state.customer_issue_profile = (
            result.get(
                "customer_issue_profile",
                ""
            )
        )

        st.session_state.customer_communication_profile = (
            result.get(
                "customer_communication_profile",
                ""
            )
        )

        st.session_state.customer_response_guidance = (
            result.get(
                "customer_response_guidance",
                ""
            )
        )

        st.session_state.customer_sensitivity = (
            result.get(
                "customer_sensitivity",
                ""
            )
        )

        # ------------------------------------------------------
        # Return
        # ------------------------------------------------------

        return (
            st.session_state.final_response
        )

    # ====================================================================================================================================================
    # Session State Initialization
    # ====================================================================================================================================================

    def initialize_session_state():

        defaults = {
            # Session
            "session_started": False,
            "thread_id": "",
            # Customer Context
            "customer_name": "",
            "customer_email": "",
            "ticket_id": "",
            # Chat
            "messages": [],
            "current_user_query": "",
            # Ticket Context
            "ticket_found": False,
            "ticket_status": "",
            "ticket_description": "",
            "customer_comments": "",
            "tech_comments": "",
            "created_at": "",
            "updated_at": "",
            "workflow_ticket_action": "",
            "previous_ticket_context": None,
            # Graph Output
            "final_response": "",
            # Monitoring
            "execution_trace": [],
            # Evaluation
            "intent_handling_score": None,
            "intent_handling_reasoning": "",
            "workflow_compliance_score": None,
            "workflow_compliance_reasoning": "",
            "customer_experience_score": None,
            "customer_experience_reasoning": "",
            "groundedness_score": None,
            "groundedness_reasoning": "",
            "overall_score": None,
            "judge_strengths": [],
            "judge_improvements": [],
            "judge_passed": False,
            "failed_params":[],
            "reflection_count": 0,
            "evaluation_history": [],
            # CSAT
            "csat_submitted": False,
            "csat_rating": None,
            "csat_comment": "",
            # Customer Intelligence
            "customer_satisfaction_summary":"",
            "customer_issue_profile":"",
            "customer_communication_profile":"",
            "customer_response_guidance":"",
            "customer_sensitivity":"",
            # LangGraph
            "graph": None,
            "intent": "",
            "resolution_confirmation": False
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

        # Build Graph Once Per Session
        if st.session_state.graph is None:
            
            st.session_state.graph = build_graph()
            
            add_trace(
                st.session_state.execution_trace,
                    "UI Initialization",
                        [
                            "LangGraph Instance created"
                        ]
                    )
    
    
    
    # Call Session State Inialization
    initialize_session_state()

    # ==========================================================
    # Page Configuration
    # ==========================================================

    st.set_page_config(
        page_title="Banking Customer Support AI Assistant",
        page_icon="🏦",
        layout="wide"
    )
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # ====================================================================================================================================================
    # Customer Assistant Tab
    # ====================================================================================================================================================

    def render_customer_assistant_tab():

        left_col, right_col = st.columns([1, 4])

        # ======================================================
        # LEFT PANEL
        # ======================================================

        with left_col:

            st.subheader("Customer Details")

            # --------------------------------------------------
            # Session Not Started
            # --------------------------------------------------

            if not st.session_state.session_started:

                customer_name = st.text_input("Customer Name *")
                customer_email = st.text_input("Customer Email *")
                ticket_id = st.text_input("Existing Ticket Number (Optional)").strip().upper()

                # ----------------------------------------------
                # Start Session Event
                # ----------------------------------------------

                if st.button("Start Session", use_container_width=True):
                    is_valid, error = validate_session_inputs(customer_name, customer_email, ticket_id)

                    if not is_valid:
                        st.error(error)
                    else:
                        # ----------------------------------------------
                        # Initialize Customer Session
                        # ----------------------------------------------

                        # Optional Ticket Lookup
                        if ticket_id:
                            
                            ticket = get_ticket(ticket_id)
                            
                            if ticket is None:
                                st.error(f"Ticket #{ticket_id} does not exist.")
                                return

                            load_ticket_context(ticket)
                        
                        st.session_state.customer_name = customer_name
                        st.session_state.customer_email = customer_email
                        st.session_state.ticket_id = ticket_id
                        st.session_state.thread_id = generate_thread_id(customer_name, customer_email)
                        st.session_state.session_started = True

                        add_trace(
                            st.session_state.execution_trace,
                            "UI Session",
                            [
                                f"Customer Name={customer_name}",
                                f"Customer Email={customer_email}",
                                f"Thread ID={st.session_state.thread_id}",
                                "Session Started"
                            ]
                        )
                        
                        st.rerun()

            # --------------------------------------------------
            # Session Started
            # --------------------------------------------------

            else:

                st.text_input(
                    "Customer Name",
                    value=st.session_state.customer_name,
                    disabled=True
                )

                st.text_input(
                    "Customer Email",
                    value=st.session_state.customer_email,
                    disabled=True
                )

                st.text_input(
                    "Ticket Number",
                    value=st.session_state.ticket_id,
                    disabled=True
                )

                # Display Classification
                if st.session_state.intent == "positive":

                    st.success(
                        "🟢 Positive / Resolution Confirmation"
                    )

                elif st.session_state.intent == "negative":

                    st.error(
                        "🔴 Negative / Complaint"
                    )

                elif st.session_state.intent == "inquiry":

                    st.info(
                        "🔵 Inquiry"
                    )

                st.divider()

                if st.button(
                    "New Session",
                    use_container_width=True
                ):

                    reset_session()

                    st.rerun()

        # ======================================================
        # RIGHT PANEL
        # ======================================================

        with right_col:

            if not st.session_state.session_started:
                return

            st.subheader("Chat History")

            # --------------------------------------------------
            # Welcome Message
            # --------------------------------------------------

            if not st.session_state.messages:

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": build_welcome_message()
                    }
                )

            # --------------------------------------------------
            # Chat History
            # --------------------------------------------------

            for message in st.session_state.messages:

                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
           
            # --------------------------------------------------
            # CSAT Feedback
            # --------------------------------------------------

            if st.session_state.final_response:

                render_csat_section()           
            
            # --------------------------------------------------
            # User Chat Input Event
            # --------------------------------------------------

            user_message = st.chat_input("Type your message...")

            if user_message:

                # -----------------------------------------------------
                # Reset Current Evaluation State for every user query
                # -----------------------------------------------------
                reset_current_evaluation_state()
                
                st.session_state.current_user_query = user_message
                
                # -----------------------------------------------------------------------
                # Graph Incovation Function Called & Context Appended (User + AI Message)
                # -----------------------------------------------------------------------
                        
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": user_message
                    }
                )
                              
                assistant_response = process_user_message()

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_response
                    }
                )

                # -----------------------------------------
                # End Session Button
                # -----------------------------------------

                left_col, right_col = st.columns([6, 1])

                with right_col:

                    if st.button(
                        "End Session",
                        use_container_width=True
                    ):

                        add_trace(
                            st.session_state.execution_trace,
                            "UI Session",
                            [
                                f"Thread ID={st.session_state.thread_id}",
                                "Session Ended By User"
                            ]
                        )

                        reset_session()

                        st.rerun()

                st.rerun()

    # ====================================================================================================================================================
    # Evaluations Tab
    # ====================================================================================================================================================

    def render_evals_tab():

        st.subheader(
            "Model Evaluation Dashboard"
        )

        # ------------------------------------------------------
        # Load Evaluation Data
        # ------------------------------------------------------

        summary = get_evaluation_summary()

        evaluations = get_evaluation_results(
            limit=100
        )

        if not evaluations:

            st.info(
                "No evaluation results available yet."
            )

            return

        # ------------------------------------------------------
        # Evaluation Summary
        # ------------------------------------------------------

        st.markdown(
            "### Evaluation Summary"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Evaluations",
                summary["total_evaluations"]
            )

        with col2:
            st.metric(
                "Pass Rate",
                f"{summary['pass_rate']}%"
            )

        with col3:
            st.metric(
                "Avg Overall Score",
                summary["avg_overall_score"]
            )

        with col4:
            st.metric(
                "Avg Reflections",
                summary["avg_reflection_count"]
            )

        st.divider()

        # ------------------------------------------------------
        # Average Judge Scores
        # ------------------------------------------------------

        st.markdown(
            "### Average Judge Scores"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Intent Handling",
                summary["avg_intent_score"]
            )

        with col2:
            st.metric(
                "Workflow Compliance",
                summary["avg_workflow_score"]
            )

        with col3:
            st.metric(
                "Customer Experience",
                summary["avg_customer_score"]
            )

        with col4:
            st.metric(
                "Groundedness",
                summary["avg_groundedness_score"]
            )

        st.divider()

        # ------------------------------------------------------
        # Recent Evaluations
        # ------------------------------------------------------

        st.markdown(
            "### Recent Evaluations"
        )

        history_df = pd.DataFrame(
            [
                {
                    "Evaluation ID":
                        row["evaluation_id"],

                    "Overall Score":
                        row["overall_score"],

                    "Status":
                        "✅ Passed"
                        if row["judge_passed"]
                        else "❌ Failed",

                    "Failed Parameters":
                        (
                            f"{len(json.loads(row['failed_params']))} Failed"
                            if row["failed_params"]
                            else "0 Failed"
                        ),

                    "Intent":
                        row["intent"],

                    "Workflow Action":
                        row["workflow_ticket_action"],

                    "Reflections":
                        row["reflection_count"],

                    "Created":
                        row["created_at"]
                }
                for row in evaluations
            ]
        )

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # ------------------------------------------------------
        # Evaluation Details
        # ------------------------------------------------------

        st.markdown(
            "### Evaluation Details"
        )

        for row in evaluations:

            try:

                strengths = json.loads(
                    row["judge_strengths"]
                )

                improvements = json.loads(
                    row["judge_improvements"]
                )

                failed_params = json.loads(
                    row["failed_params"]
                )

            except Exception:

                strengths = []
                improvements = []
                failed_params = []

            with st.expander(
                f"Evaluation #{row['evaluation_id']} | Overall Score: {row['overall_score']}/10"
            ):

                # --------------------------------------------------
                # Conversation Summary
                # --------------------------------------------------

                st.markdown(
                    "#### Conversation Summary"
                )

                st.write(
                    f"**Intent:** {row['intent']}"
                )

                st.write(
                    f"**Workflow Action:** {row['workflow_ticket_action']}"
                )

                st.write(
                    f"**Judge Passed:** {'Yes' if row['judge_passed'] else 'No'}"
                )

                st.write(
                    f"**Reflection Count:** {row['reflection_count']}"
                )

                st.divider()

                # --------------------------------------------------
                # User Query
                # --------------------------------------------------

                st.markdown(
                    "#### User Query"
                )

                st.info(
                    row["query"]
                )

                # --------------------------------------------------
                # Final Customer Response
                # --------------------------------------------------

                st.markdown(
                    "#### Final Customer Response"
                )

                st.info(
                    row["final_response"]
                )

                st.divider()

                # --------------------------------------------------
                # Judge Scores
                # --------------------------------------------------

                st.markdown(
                    "#### Judge Scores"
                )

                score_df = pd.DataFrame(
                    [
                        {
                            "Parameter":
                                "Intent Handling",

                            "Objective":
                                "Customer intent correctly understood and addressed",

                            "Score":
                                row["intent_handling_score"],

                            "Result":
                                "✅ Passed"
                                if row["intent_handling_score"] >= 9
                                else "❌ Failed"
                        },

                        {
                            "Parameter":
                                "Workflow Compliance",

                            "Objective":
                                "Workflow action correctly communicated",

                            "Score":
                                row["workflow_compliance_score"],

                            "Result":
                                "✅ Passed"
                                if row["workflow_compliance_score"] >= 9
                                else "❌ Failed"
                        },

                        {
                            "Parameter":
                                "Customer Experience",

                            "Objective":
                                "Empathy, clarity and professionalism",

                            "Score":
                                row["customer_experience_score"],

                            "Result":
                                "✅ Passed"
                                if row["customer_experience_score"] >= 9
                                else "❌ Failed"
                        },

                        {
                            "Parameter":
                                "Groundedness",

                            "Objective":
                                "Response fully supported by available context",

                            "Score":
                                row["groundedness_score"],

                            "Result":
                                "✅ Passed"
                                if row["groundedness_score"] >= 9
                                else "❌ Failed"
                        }
                    ]
                )

                st.dataframe(
                    score_df,
                    hide_index=True,
                    use_container_width=True
                )

                # --------------------------------------------------
                # Judge Reasoning
                # --------------------------------------------------

                st.markdown(
                    "#### Judge Reasoning"
                )

                with st.expander(
                    "Intent Handling"
                ):
                    st.write(
                        row["intent_handling_reasoning"]
                    )

                with st.expander(
                    "Workflow Compliance"
                ):
                    st.write(
                        row["workflow_compliance_reasoning"]
                    )

                with st.expander(
                    "Customer Experience"
                ):
                    st.write(
                        row["customer_experience_reasoning"]
                    )

                with st.expander(
                    "Groundedness"
                ):
                    st.write(
                        row["groundedness_reasoning"]
                    )

                st.divider()

                # --------------------------------------------------
                # Failed Parameters
                # --------------------------------------------------

                st.markdown(
                    "#### Failed Parameters"
                )

                if failed_params:

                    for item in failed_params:

                        st.error(
                            item
                        )

                else:

                    st.success(
                        "No failed parameters."
                    )

                # --------------------------------------------------
                # Judge Strengths
                # --------------------------------------------------

                st.markdown(
                    "#### Response Strengths"
                )

                if strengths:

                    for item in strengths:

                        st.success(
                            item
                        )

                else:

                    st.info(
                        "No strengths captured."
                    )

                # --------------------------------------------------
                # Judge Improvements
                # --------------------------------------------------

                st.markdown(
                    "#### Response Improvement - Recommendations"
                )

                if improvements:

                    for item in improvements:

                        st.warning(
                            item
                        )

                else:

                    st.success(
                        "No improvements required."
                    )

    # ====================================================================================================================================================
    # Intent Classification Evaluation Tab (Test Cases)
    # ====================================================================================================================================================

    def render_evals_test_cases_tab():

        st.subheader(
            "Intent Classification Evaluation Using Manual Predefined Test Cases"
        )

        # ------------------------------------------------------
        # Run Evaluation
        # ------------------------------------------------------

        col1, col2 = st.columns([1, 5])

        with col1:

            if st.button(
                "Run Evaluation",
                use_container_width=True
            ):

                with st.spinner(
                    "Running classifier evaluation..."
                ):

                    run_classifier_evaluation()

                st.success(
                    "Classifier evaluation completed."
                )

                st.rerun()

        # ------------------------------------------------------
        # Load Results
        # ------------------------------------------------------

        summary = (
            get_classifier_summary()
        )

        results = (
            get_classifier_results()
        )

        if not results:

            st.info(
                "No classifier evaluation results available."
            )

            return

        # ------------------------------------------------------
        # Summary Metrics
        # ------------------------------------------------------

        st.markdown(
            "### Intent Classification / Agent Routing Accuracy"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Tests",
                summary["total_tests"]
            )

        with col2:

            st.metric(
                "Passed",
                summary["passed_tests"]
            )

        with col3:

            st.metric(
                "Failed",
                summary["failed_tests"]
            )

        with col4:

            st.metric(
                "Accuracy",
                f"{summary['accuracy']}%"
            )

        st.divider()

        # ------------------------------------------------------
        # Detailed Results
        # ------------------------------------------------------

        st.markdown(
            "### Test Results"
        )

        results_df = pd.DataFrame(
            [
                {
                    "Test ID":
                        row["test_id"],

                    "Category":
                        row["category"],

                    "Query":
                        row["query"],

                    "Expected Intent":
                        row["expected_intent"],

                    "Actual Intent":
                        row["actual_intent"],

                    "Result":
                        (
                            "✅ Pass"
                            if row["test_result"] == "Pass"
                            else "❌ Fail"
                        )
                }
                for row in results
            ]
        )

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # ------------------------------------------------------
        # Failed Test Cases
        # ------------------------------------------------------

        failed_results = [
            row
            for row in results
            if row["test_result"] == "Fail"
        ]

        st.markdown(
            "### Failed Test Cases"
        )

        if not failed_results:

            st.success(
                "All classifier test cases passed."
            )

            return

        for row in failed_results:

            with st.expander(
                f"❌ Test #{row['test_id']} | {row['category']}"
            ):

                st.write(
                    f"**Query:** {row['query']}"
                )

                st.write(
                    f"**Expected Intent:** {row['expected_intent']}"
                )

                st.write(
                    f"**Actual Intent:** {row['actual_intent']}"
                )

    # ====================================================================================================================================================
    # Define CSAT Section
    # ====================================================================================================================================================

    def render_csat_section():

        if st.session_state.csat_submitted:

            st.caption(
                "✅ Thank you for your feedback."
            )

            return

        # --------------------------------------------------
        # Right Aligned Feedback Controls
        # --------------------------------------------------

        label_col, thumbs_up_col, thumbs_down_col = st.columns(
            [20, 1, 1]
        )

        with label_col:

            st.markdown(
                """
                <div style="
                    text-align:right;
                    padding-top:10px;
                    color:#888888;
                    font-size:14px;
                ">
                    Was this helpful?
                </div>
                """,
                unsafe_allow_html=True
            )

        # --------------------------------------------------
        # Thumbs Up
        # --------------------------------------------------

        with thumbs_up_col:

            if st.button(
                "👍",
                key="thumbs_up_btn"
            ):

                save_csat_feedback(

                    thread_id=
                        st.session_state.thread_id,

                    customer_name=
                        st.session_state.customer_name,

                    customer_email=
                        st.session_state.customer_email,

                    active_ticket_id=
                        st.session_state.ticket_id,

                    intent_category=
                        st.session_state.intent,

                    workflow_ticket_action=
                        st.session_state.workflow_ticket_action,

                    overall_score=
                        st.session_state.overall_score,

                    final_response=
                        st.session_state.final_response,

                    feedback_rating=
                        "thumbs_up",

                    feedback_comment=
                        None
                )

                st.session_state.csat_submitted = True

                st.rerun()

        # --------------------------------------------------
        # Thumbs Down
        # --------------------------------------------------

        with thumbs_down_col:

            if st.button(
                "👎",
                key="thumbs_down_btn"
            ):

                st.session_state.csat_rating = (
                    "thumbs_down"
                )

        # --------------------------------------------------
        # Negative Feedback
        # --------------------------------------------------

        if (
            st.session_state.csat_rating
            ==
            "thumbs_down"
        ):

            st.markdown("<br>", unsafe_allow_html=True)

            st.text_area(

                "What could be improved?",

                key="csat_comment",

                placeholder=
                    "Please share what could have been better..."
            )

            if st.button(
                "Submit Feedback",
                use_container_width=True
            ):

                if not (
                    st.session_state.csat_comment
                    .strip()
                ):

                    st.warning(
                        "Feedback comments are mandatory for thumbs down."
                    )

                    return

                save_csat_feedback(

                    thread_id=
                        st.session_state.thread_id,

                    customer_name=
                        st.session_state.customer_name,

                    customer_email=
                        st.session_state.customer_email,

                    active_ticket_id=
                        st.session_state.ticket_id,

                    intent_category=
                        st.session_state.intent,

                    workflow_ticket_action=
                        st.session_state.workflow_ticket_action,

                    overall_score=
                        st.session_state.overall_score,

                    final_response=
                        st.session_state.final_response,

                    feedback_rating=
                        "thumbs_down",

                    feedback_comment=
                        st.session_state.csat_comment
                )

                st.session_state.csat_submitted = True

                st.rerun()

    # ====================================================================================================================================================
    # Render Customer Profile Tab
    # ====================================================================================================================================================

    def render_customer_profile_tab():

        if not st.session_state.customer_email:

            st.info(
                "Start a customer session to view profile insights."
            )

            return

        customer_profile = get_customer_profile(
            st.session_state.customer_email
        )

        evaluation_profile = get_customer_evaluation_profile(
            st.session_state.customer_email
        )

        # --------------------------------------------------
        # Customer Intelligence
        # --------------------------------------------------

        customer_satisfaction_summary = (
            st.session_state.customer_satisfaction_summary
        )

        customer_issue_profile = (
            st.session_state.customer_issue_profile
        )

        customer_communication_profile = (
            st.session_state.customer_communication_profile
        )

        customer_response_guidance = (
            st.session_state.customer_response_guidance
        )

        customer_sensitivity = (
            st.session_state.customer_sensitivity
        )

        # --------------------------------------------------
        # Derived Metrics
        # --------------------------------------------------

        conversation_count = (
            evaluation_profile["evaluation_count"]
        )

        feedback_count = (

            customer_profile["thumbs_up_count"]

            +

            customer_profile["thumbs_down_count"]
        )

        no_feedback_count = max(

            0,

            conversation_count - feedback_count
        )

        participation_rate = 0

        if conversation_count > 0:

            participation_rate = round(

                (
                    feedback_count
                    /
                    conversation_count
                )
                * 100,

                1
            )

        # --------------------------------------------------
        # Customer Profile Header
        # --------------------------------------------------

        st.subheader(
            "👤 Customer Profile Dashboard"
        )

        st.markdown(
            f"""
            **Customer Name:** {st.session_state.customer_name} | {customer_profile["customer_email"]}
            """
        )

        # --------------------------------------------------
        # Metrics
        # --------------------------------------------------

        metric_col1, \
        metric_col2, \
        metric_col3, \
        metric_col4, \
        metric_col5, \
        metric_col6 = st.columns(6)

        with metric_col1:

            st.metric(
                "Conversations",
                conversation_count
            )

        with metric_col2:

            st.metric(
                "👍 Thumbs Up",
                customer_profile["thumbs_up_count"]
            )

        with metric_col3:

            st.metric(
                "👎 Thumbs Down",
                customer_profile["thumbs_down_count"]
            )

        with metric_col4:

            st.metric(
                "➖ No Feedback",
                no_feedback_count
            )

        with metric_col5:

            st.metric(
                "Avg Judge Score",
                evaluation_profile["avg_overall_score"]
            )

        with metric_col6:

            st.metric(
                "CSAT Participation",
                f"{participation_rate}%"
            )

        st.divider()

        # ==================================================
        # Customer Intelligence
        # ==================================================

        st.subheader(
            "🧠 Customer Intelligence"
        )

        sensitivity_icon = {

            "LOW": "🟢",

            "MEDIUM": "🟡",

            "HIGH": "🔴"

        }.get(
            customer_sensitivity,
            "⚪"
        )

        st.markdown(
            f"""
            **Customer Sensitivity:** {sensitivity_icon} {customer_sensitivity}
            """
        )

        # --------------------------------------------------
        # No Intelligence Yet
        # --------------------------------------------------

        if not any([

            customer_satisfaction_summary,

            customer_issue_profile,

            customer_communication_profile,

            customer_response_guidance

        ]):

            st.info(
                "Customer intelligence will appear after the first interaction."
            )

            return

        # --------------------------------------------------
        # Satisfaction Overview
        # --------------------------------------------------

        st.subheader(
            "📊 Satisfaction Overview"
        )

        st.info(
            customer_satisfaction_summary
        )

        # --------------------------------------------------
        # Issue Profile
        # --------------------------------------------------

        st.subheader(
            "🔍 Issue Profile"
        )

        st.info(
            customer_issue_profile
        )

        # --------------------------------------------------
        # Communication Profile
        # --------------------------------------------------

        st.subheader(
            "💬 Communication Profile"
        )

        st.info(
            customer_communication_profile
        )

        # --------------------------------------------------
        # Response Guidance
        # --------------------------------------------------

        st.subheader(
            "🎯 Response Guidance"
        )

        st.info(
            customer_response_guidance
        )
 
    
    # ====================================================================================================================================================
    # Main Application
    # ====================================================================================================================================================

    st.markdown(
        """
        # 🏦 Banking Customer Support AI Assistant

        Multi-Agent Customer Support System using LangGraph
        """
    )

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Customer Assistant",
            "Response Evaluation (LLM-as-Judge)",
            "Current Customer Profiling",
            "Agent Execution Trace",
            "Intent Classification Evaluation (Manual Test-Cases)"
        ]
    )

    with tab1:

        render_customer_assistant_tab()

    with tab2:

        render_evals_tab()

    with tab3:
        
        render_customer_profile_tab()
    
    with tab4:

        st.subheader("Workflow Node Traces")
        if not st.session_state.execution_trace:
            st.info("No execution trace available.")
        else:
            st.code(
                "\n".join(
                    st.session_state.execution_trace
                )
            )
    
    with tab5:
        
        render_evals_test_cases_tab()
        
