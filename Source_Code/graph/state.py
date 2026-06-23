from typing import Optional, Literal
from langgraph.graph import MessagesState

class BankingSupportState(MessagesState):

    # Customer Context
    customer_name: str
    customer_email: str
    ticket_id: Optional[str]
    thread_id: str

    # Current Request
    current_user_query: str
    # Ticket Validation in user query
    ticket_format_valid: Optional[bool]

    # Intent
    intent: Optional[str]
    interaction_type: Optional[str]
    classification_reasoning: Optional[str]
    resolution_confirmation: Optional[bool]

    # Ticket Context
    ticket_status: Optional[str]
    ticket_description: Optional[str]
    customer_comments: Optional[str]
    tech_comments: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    workflow_ticket_action: str
    previous_ticket_context: Optional[dict]

    # Agent Output
    agent_result: Optional[str]

    # Final Response
    final_response: Optional[str]

    # Monitoring
    execution_trace: list[str]

    # Evaluation
    evaluation_history: list[dict]
    intent_handling_score: int | None
    intent_handling_reasoning: str
    workflow_compliance_score: int | None
    workflow_compliance_reasoning: str
    customer_experience_score: int | None
    customer_experience_reasoning: str
    groundedness_score: int | None
    groundedness_reasoning: str
    overall_score: float | None
    judge_strengths: list[str]
    judge_improvements: list[str]
    judge_passed: bool
    failed_params: list[str]
    reflection_count: int

    # Customer Intelligence
    customer_satisfaction_summary: str
    customer_issue_profile: str
    customer_communication_profile: str
    customer_response_guidance: str
    customer_sensitivity: Literal[
        "LOW",
        "MEDIUM",
        "HIGH"
    ]