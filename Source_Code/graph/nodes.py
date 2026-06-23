import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents.middleware.types import InputAgentState
from typing import cast, Any
from langchain_core.messages import AnyMessage

from graph.state import BankingSupportState
from graph.utils import *
from llm.llm_models import *
from graph.edges import *
from data.database import *

# ==============================================================================================================================================
# Classifier Node
# ==============================================================================================================================================

def classifier_node(state: BankingSupportState):

    # ------------------------------------------------------
    # Resolve Ticket Context
    # ------------------------------------------------------

    resolved_ticket_id, ticket_format_valid = (
        resolve_ticket_id(
            ui_ticket_id=state.get("ticket_id"),
            user_query=state["current_user_query"]
        )
    )

    # ------------------------------------------------------
    # Build Conversation History to be passed to LLM
    # ------------------------------------------------------

    conversation_history = "\n".join(
        [
            (
                f"{message.type}: "
                f"{message.content}"
            )
            for message in state.get(
                "messages",
                []
            )[-10:]
        ]
    )

    # ------------------------------------------------------
    # Invoke Classifier
    # ------------------------------------------------------

    classification = (
        llm_classifier_chain.invoke(
            {
                "ticket_id":
                    resolved_ticket_id
                    or "Not Provided",

                "conversation_history":
                    conversation_history
                    or "No prior conversation.",

                "customer_query":
                    state["current_user_query"]
            }
        )
    )

    # Append User query to conversation context (final response to be appended in the final node)
    new_user_message = HumanMessage(
        content=state["current_user_query"]
    )
    
    # ------------------------------------------------------
    # Execution Trace
    # ------------------------------------------------------

    # Extracting Last AI Message
    existing_messages = list(state.get("messages",[]))
    last_ai_message = "None"
    for msg in reversed(existing_messages):
        if isinstance(msg, AIMessage):
            last_ai_message = msg.content
            break

    execution_trace = list(state.get("execution_trace",[]))
    execution_trace.append(
        "******************************* STARTING CONVERSATION .....  *******************************"
    )

    add_trace(execution_trace, "Classifier",
        [
            f"LangGraph Memory Message Count (0 -> 2 -> 4 ...) = {len(existing_messages)}",
            f"Previous AI Response={last_ai_message}",
            f"Intent={classification.intent}",  # type: ignore
            f"Interaction={classification.interaction_type}",  # type: ignore
            f"Resolution Confirmation={classification.resolution_confirmation}",  # type: ignore
            f"Reasoning={classification.classification_reasoning}",  # type: ignore
            f"Ticket ID={resolved_ticket_id}",
            f"Ticket Format Valid={ticket_format_valid}"
        ]
    )

    # ------------------------------------------------------
    # Return State Updates
    # ------------------------------------------------------

    return {
        "ticket_id":
            resolved_ticket_id,

        "ticket_format_valid":
            ticket_format_valid,

        "intent":
            classification.intent, # type: ignore

        "interaction_type":
            classification.interaction_type, # type: ignore

        "resolution_confirmation":
            classification.resolution_confirmation, # type: ignore
        
        "classification_reasoning":
            classification.classification_reasoning, # type: ignore

        "messages": [
            new_user_message
        ],
        
        "execution_trace":
            execution_trace,

        # For every conversation (i.e. start of classifier node), we clear these values as these are needed by Judge per conversation only
        "previous_ticket_context": None,
        "workflow_ticket_action": "",
    }

# ==============================================================================================================================================
# Positive Agent Node
# ==============================================================================================================================================

def positive_agent_node(state: BankingSupportState):

    execution_trace = list(
        state.get(
            "execution_trace",
            []
        )
    )

    ticket_id = state.get(
        "ticket_id"
    )
    resolution_confirmation = state.get(
        "resolution_confirmation",
        False
    )

    # ------------------------------------------------------
    # No Ticket ID Available
    # ------------------------------------------------------

    if not ticket_id:

        response = (
            f"Dear {state['customer_name']},\n\n"
            "Thank you for your feedback. "
            "We are pleased that we were able "
            "to assist you.\n\n"
            "If you require any further assistance, "
            "please do not hesitate to contact us."
        )

        add_trace(
            execution_trace,
            "Positive Agent",
            [
                "Ticket ID = None",
                "No Ticket ID in User-query. Generic Thank-you response generated",
                "(Deterministic Response)"
            ]
        )

        return {
            "agent_result":
                response,

            "execution_trace":
                execution_trace,

            "workflow_ticket_action": "no_ticket_reference",
            "previous_ticket_context": None,
        }

    # ------------------------------------------------------
    # Ticket Lookup
    # ------------------------------------------------------

    ticket = get_ticket(
        ticket_id
    )

    if not ticket:

        response = (
            f"Dear {state['customer_name']},\n\n"
            f"Thank you for your feedback.\n\n"
            f"We appreciate your message "
            f"regarding ticket {ticket_id}.\n\n"
            "However, we were unable to locate "
            "this ticket in our records. \n\n"
            "Please share a valid Ticket ID."
        )

        add_trace(
            execution_trace,
            "Positive Agent",
            [
                f"Ticket ID = {ticket_id}",
                "Ticket lookup failed as it doesn't exist in the system. Requested User to share valid Ticket ID "
                "(Deterministic Response)"
            ]
        )

        return {
            "agent_result":
                response,

            "execution_trace":
                execution_trace,

            "workflow_ticket_action": "no_ticket_reference",
            "previous_ticket_context": None,
        }

    # ------------------------------------------------------
    # Load Ticket Context
    # ------------------------------------------------------

    ticket_context = (
        load_ticket_context_dict(
            ticket
        )
    )

    current_status = (
        ticket_context.get(
            "ticket_status",
            ""
        )
    )


    # ------------------------------------------------------
    # Auto Close Ticket On Resolution Confirmation
    # ------------------------------------------------------

    if (
        resolution_confirmation
        and
        current_status
        and
        current_status.lower()
        in [
            "open",
            "in-progress",
            "waiting user information"
        ]
        ):

        # Update Ticket to Resolved
        update_ticket_status(
            ticket_id,
            "Resolved"
        )

        ticket = get_ticket(
            ticket_id
        )

        # Load updated ticket
        ticket_context = (
            load_ticket_context_dict(
                ticket
            )
        )

        tech_notes = (
                        ticket_context["tech_comments"]
                        or "No resolution notes available."
                    )
        
        response = (
            f"Dear {state['customer_name']},\n\n"
            "Thank you for your feedback.\n\n"
            "We are pleased that your issue "
            "has been resolved:-\n\n"
            f"Ticket ID: {ticket_context['ticket_id']}\n"
            f"Status: {ticket_context['ticket_status']}\n"
            f"Created By: {ticket_context['customer_name']}\n"
            f"Issue: {ticket_context['ticket_description']}\n"
            f"Resolution: {tech_notes}\n\n"
            "Thank you for banking with us. "
            "We appreciate your continued trust "
            "and look forward to serving you again."
        )
   
        # Add Trace
        add_trace(
            execution_trace,
            "Positive Agent",
            [
                f"Ticket ID={ticket_id}",
                f"Final Status={ticket_context['ticket_status']}",
                f"Issue={ticket_context['ticket_description']}",
                "Customer confirmed issue resolved. Ticket Updated to Resolved",
                "Resolution summary generated"
                "(Deterministic Response)"
            ]
        )

        return {

            "ticket_id":
                ticket_context[
                    "ticket_id"
                ],

            "ticket_status":
                ticket_context[
                    "ticket_status"
                ],

            "ticket_description":
                ticket_context[
                    "ticket_description"
                ],

            "customer_comments":
                ticket_context[
                    "customer_comments"
                ],

            "tech_comments":
                ticket_context[
                    "tech_comments"
                ],

            "created_at":
                ticket_context[
                    "created_at"
                ],

            "updated_at":
                ticket_context[
                    "updated_at"
                ],

            "agent_result":
                response,
            
            "execution_trace":
                execution_trace,

            "workflow_ticket_action": "existing_ticket_resolved",
            "previous_ticket_context": None,
        }


    # No Resolution Confirmation - Dont update ticket to Resolved
    else:

        tech_notes = (
            ticket_context["tech_comments"]
            or "No updates available."
        )

        response = (
            f"Dear {state['customer_name']},\n\n"
            "Thank you for your message.\n\n"
            "We appreciate your acknowledgement.\n\n"
            "Your ticket remains active and our team "
            "continues to work on the issue.\n\n"
            f"Ticket ID: {ticket_context['ticket_id']}\n"
            f"Status: {ticket_context['ticket_status']}\n"
            f"Created By: {ticket_context['customer_name']}\n"
            f"Issue: {ticket_context['ticket_description']}\n"
            f"Latest Update: {tech_notes}\n\n"
            "We will continue to provide updates as "
            "progress is made."
        )

        add_trace(
            execution_trace,
            "Positive Agent",
            [
                f"Ticket ID={ticket_id}",
                f"Status={ticket_context['ticket_status']}",
                "Positive acknowledgement received",
                "Resolution confirmation=False",
                "Ticket left unchanged"
                "(Deterministic Response)"
            ]
        )

        return {

            "ticket_id":
                ticket_context[
                    "ticket_id"
                ],

            "ticket_status":
                ticket_context[
                    "ticket_status"
                ],

            "ticket_description":
                ticket_context[
                    "ticket_description"
                ],

            "customer_comments":
                ticket_context[
                    "customer_comments"
                ],

            "tech_comments":
                ticket_context[
                    "tech_comments"
                ],

            "created_at":
                ticket_context[
                    "created_at"
                ],

            "updated_at":
                ticket_context[
                    "updated_at"
                ],

            "agent_result":
                response,
            
            "execution_trace":
                execution_trace,

            "workflow_ticket_action": "existing_ticket_used",
            "previous_ticket_context": None,
        }

# ==============================================================================================================================================
# Inquiry Agent Node
# ==============================================================================================================================================

def inquiry_agent_node(
    state: BankingSupportState
):

    # ------------------------------------------------------
    # Execution Trace
    # ------------------------------------------------------

    execution_trace = list(
        state.get(
            "execution_trace",
            []
        )
    )

    # Get complete context
    messages = list(state.get("messages",[]))       
    
    ticket_id = state.get("ticket_id")

    # ------------------------------------------------------
    # Reponse - No Ticked ID / Invalid Ticket ID
    # ------------------------------------------------------

    ticket_format_valid = state.get(
            "ticket_format_valid"
        )
    
    if ticket_format_valid is False:

        response = (
            "The ticket number provided does not "
            "appear to be valid.\n\n"
            "Please provide a valid ticket ID "
            "(Example: INC0000000001)."
        )

        add_trace(
            execution_trace,
            "Inquiry Agent",
            [
                "Invalid ticket format detected"
                "(Deterministic Response)"
            ]
        )

        return {
            "agent_result": response,
            "execution_trace": execution_trace,
            "workflow_ticket_action": "no_ticket_reference",
            "previous_ticket_context":None
            }
    
    if not ticket_id:

        response = (
            "I could not identify a valid "
            "ticket number in your request.\n\n"
            "Please provide a valid Ticket ID "
            "(Example: INC0000000001)."
        )

        add_trace(
            execution_trace,
            "Inquiry Agent",
            [
                "No Ticket ID available in the user query"
                "(Deterministic Response)"
            ]
        )

        return {
            "agent_result":
                response,

            "execution_trace":
                execution_trace,

            "workflow_ticket_action": "no_ticket_reference",

            "previous_ticket_context":None
        }


    # ------------------------------------------------------
    # Invoke Inquiry Agent - Ticket ID Found
    # ------------------------------------------------------

    # Runtime Context
    runtime_context = (
        "Conversation Context\n\n"

        f"Current Customer Name: "
        f"{state['customer_name']}\n"

        f"Current Customer Email: "
        f"{state['customer_email']}\n"

        f"Requested Ticket ID: "
        f"{ticket_id}\n\n"

        "Instructions:\n"
        "- Always address the customer using Current Customer Name.\n"
        "- Never use ticket creator name as greeting.\n"
        "- Display ticket creator only as Created By.\n"
        "- This agent is read-only.\n"
        "- Never modify ticket data.\n"
        "- Never create new tickets.\n"
        "- Use lookup_ticket tool only.\n"
        "- Use the validated ticket ID when calling lookup_ticket.\n"
    )

    # Build Agent Messages
    # (Do NOT modify state['messages'])

    agent_messages = [
        SystemMessage(
            content=runtime_context
        ),
        *messages
    ]

    # Wrap messages in InputAgentState for agent invocation
    agent_input = InputAgentState(
        messages=cast(
            list[AnyMessage | dict[str, Any]],
            agent_messages
        )
    )

    # Invoke Inquiry Agent
    result = inquiry_agent.invoke(
        agent_input
    )

    # ------------------------------------------------------
    # Extract Final Response
    # ------------------------------------------------------

    response = (
        result["messages"][-1].content
    )

    # ------------------------------------------------------
    # Trace
    # ------------------------------------------------------

    add_trace(
        execution_trace,
        "Inquiry Agent",
        [
            f"Lookup Ticket ID={ticket_id}",
            "Customer-friendly response generated",
            f"Inquiry Agent Response: {response}"
        ]
    )

    # ------------------------------------------------------
    # Return
    # ------------------------------------------------------

    return {
        "agent_result":
            response,

        "execution_trace":
            execution_trace,
        
        "workflow_ticket_action": "existing_ticket_used",
            
        "previous_ticket_context":None
    }

# ==============================================================================================================================================
# Negative Agent Node
# ==============================================================================================================================================

def negative_agent_node(
    state: BankingSupportState
):

    # ------------------------------------------------------
    # Execution Trace
    # ------------------------------------------------------

    execution_trace = list(
        state.get(
            "execution_trace",
            []
        )
    )

    # ------------------------------------------------------
    # Conversation Context
    # ------------------------------------------------------

    messages = list(
        state.get(
            "messages",
            []
        )
    )

    ticket_id = state.get(
        "ticket_id"
    )

    # ------------------------------------------------------
    # Previous Ticket Context
    # ------------------------------------------------------

    previous_ticket_context = None

    if ticket_id:

        ticket = get_ticket(ticket_id)

        if ticket:

            previous_ticket_context = (
                load_ticket_context_dict(ticket)
            )

   # ------------------------------------------------------
    # Runtime Context
    # ------------------------------------------------------

    runtime_context = (
        "Current Customer Context\n\n"

        f"Current Customer Name: "
        f"{state['customer_name']}\n"

        f"Current Customer Email: "
        f"{state['customer_email']}\n"

        f"Validated Ticket ID: "
        f"{ticket_id or 'None'}\n\n"

        "Instructions:\n"
        "- Always address the customer using Current Customer Name.\n"
        "- Never use ticket creator name as greeting.\n"
        "- Display ticket creator only as Created By.\n"
        "- Use Current Customer Name and Email when creating tickets.\n"
        "- Use the customer's complaint as the ticket description.\n"
        "- When a Validated Ticket ID exists, always call lookup_ticket first.\n"
        "- If ticket status is Open, In-progress, or Waiting user information, do not create a new ticket.\n"
        "- If ticket status is Resolved and the customer is still reporting the issue, create a new ticket.\n"
        "- If no Validated Ticket ID exists, create a new ticket.\n"
        "- Do not invent customer information.\n"
    )

    # ------------------------------------------------------
    # Build Agent Messages
    # ------------------------------------------------------

    agent_messages = [
        SystemMessage(
            content=runtime_context
        ),
        *messages
    ]

    # ------------------------------------------------------
    # Agent Input
    # ------------------------------------------------------

    agent_input = InputAgentState(
        messages=cast(
            list[AnyMessage | dict[str, Any]],
            agent_messages
        )
    )

    # ------------------------------------------------------
    # Invoke Negative Agent
    # ------------------------------------------------------

    result = negative_agent.invoke(
        agent_input
    )

    # ------------------------------------------------------
    # Extract Final Response
    # ------------------------------------------------------

    response = (
        result["messages"][-1].content
    )

    # ------------------------------------------------------
    # Capture Newly Created Ticket ID
    # ------------------------------------------------------

    created_ticket_id = None
    workflow_ticket_action = "existing_ticket_used"

    # Check if Agent called Ticket Creation Tool to create a new ticket
    for msg in result["messages"]:

        # Tool Messages generated by create_ticket
        if hasattr(msg, "name") and msg.name == "create_ticket":
            try:
                tool_output = json.loads(
                    msg.content
                )
                created_ticket_id = (
                    tool_output.get(
                        "ticket_id"
                    )
                )
            except Exception:
                pass
    
    if created_ticket_id:
        workflow_ticket_action = "new_ticket_created"
        
        if (
            previous_ticket_context
            and
            previous_ticket_context.get("ticket_status","").lower() == "resolved"
            ):
            
            workflow_ticket_action = "new_ticket_created_from_resolved_ticket"
    
    # If a new ticket was created, make it the active ticket in state

    active_ticket_id = (
        created_ticket_id
        if created_ticket_id
        else ticket_id
    )

    # ------------------------------------------------------
    # Execution Trace
    # ------------------------------------------------------

    previous_status = (
        previous_ticket_context.get("ticket_status","None")
        if previous_ticket_context
        else "None"
    )
    
    
    add_trace(
        execution_trace,
        "Negative Agent",
        [
            f"Original Ticket ID={ticket_id}",
            f"Original Ticket Status={previous_status}",
            f"Created Ticket ID={created_ticket_id}",
            f"Active Ticket ID={active_ticket_id}",
            f"Workflow Ticket Action={workflow_ticket_action}",
            "Negative Agent Response generated"
            f"Negative Agent Response: {response}"
        ]
    )

    # ------------------------------------------------------
    # Return
    # ------------------------------------------------------

    return {

        "agent_result":
            response,

        "ticket_id":
            active_ticket_id,

        "workflow_ticket_action":
            workflow_ticket_action,

        "previous_ticket_context":
            previous_ticket_context,

        "execution_trace":
            execution_trace
    }


# ==============================================================================================================================================
# Final Response Generator Node
# ==============================================================================================================================================

def response_generator_node(
    state: BankingSupportState
):

# ------------------------------------------------------
# Reflection Context
# ------------------------------------------------------

    reflection_count = (
        state.get(
            "reflection_count",
            0
        )
    )

    workflow_ticket_action = (
    state.get(
        "workflow_ticket_action",
        ""
        )
    )

    previous_ticket_context = (
        state.get(
            "previous_ticket_context"
        )
    )

    judge_improvements = (
        state.get(
            "judge_improvements",
            []
        )
    )

    failed_params = (
        state.get(
            "failed_params",
            []
        )
    )
    
    execution_trace = list(
        state.get(
            "execution_trace",
            []
        )
    )

    # ------------------------------------------------------
    # Reflection Attempt
    # ------------------------------------------------------

    if (
        state.get("judge_passed") is False
        and
        judge_improvements
    ):
        reflection_count += 1

    # ------------------------------------------------------
    # Judge Improvement Context
    # ------------------------------------------------------

    improvement_context = (
        "\n".join(
            [
                f"- {item}"
                for item in judge_improvements
            ]
        )
        if judge_improvements
        else
        "None"
    )

    # ------------------------------------------------------
    # Failed Parameters Context
    # ------------------------------------------------------

    failed_param_context = (
        "\n".join(
            [
                f"- {item}"
                for item in failed_params
            ]
        )
        if failed_params
        else
        "None"
    )



    ticket_context = None
    ticket_id = state.get("ticket_id")

    if ticket_id:

        ticket = get_ticket(ticket_id)
        if ticket:
            ticket_context = (
                load_ticket_context_dict(
                    ticket
                )
            )
   
    result = (
        llm_response_generator_chain.invoke(
            {
                "user_query": state["current_user_query"],
                "customer_name": state["customer_name"],
                "intent": state["intent"],
                "interaction_type": state["interaction_type"],
                "resolution_confirmation": state.get("resolution_confirmation",False),
                "agent_result": state["agent_result"],
                "ticket_context": ticket_context,
                "previous_ticket_context": previous_ticket_context,
                "workflow_ticket_action": workflow_ticket_action,
                "reflection_count": reflection_count,
                "failed_params": failed_param_context,
                "judge_improvements": improvement_context,
                "customer_issue_profile": state["customer_issue_profile"],
                "customer_response_guidance": state["customer_response_guidance"],
                "customer_sensitivity": state["customer_sensitivity"]
            }
        )
    )

    
    # ------------------------------------------------------
    # Execution Trace
    # ------------------------------------------------------

    previous_ticket_id = None

    if previous_ticket_context:
        previous_ticket_id = (
            previous_ticket_context.get(
                "ticket_id"
            )
        )


    add_trace(
        execution_trace,
        "Response Generator",
        [
            f"Intent={state['intent']}",
            f"Active Ticket ID={ticket_id}",
            f"Previous Ticket ID={previous_ticket_id}",
            f"Workflow Ticket Action={workflow_ticket_action}",
            f"Previous Ticket Context Available={previous_ticket_context is not None}",
            "Latest ticket context loaded from database",
            f"Customer Issue Profile={state["customer_issue_profile"]}",
            f"Customer Response Guidance={state["customer_response_guidance"]}",
            f"Customer Sensitivity={state["customer_sensitivity"]}",
            "Customer response generated",
            f"Response Generator Agent Response: {result.user_response}" # type: ignore
        ]
    )


    return {
        "final_response":
            result.user_response, # type: ignore
        
        "reflection_count": 
            reflection_count,

        "execution_trace":
            execution_trace
    }

# ==============================================================================================================================================
# LLM Judge Node
# ==============================================================================================================================================

def llm_judge_node(state):

    updated_messages = list(
        state.get("messages",[])
    )

    execution_trace = list(
        state.get(
            "execution_trace",
            []
        )
    )

    evaluation_history = list(
    state.get(
        "evaluation_history",
        []
        )
    )

    # Build Conversation History from messages in conversation format
    conversation_history = "\n".join(
        [
            f"{message.type}: {message.content}"
            for message in state.get("messages", [])[-10:]
        ]
    )

    # Active Ticket Context
    ticket_context = "No active ticket context available."
    ticket_id = state.get("ticket_id")

    if ticket_id:
        ticket_details = get_ticket(ticket_id)

        if ticket_details:
            ticket_context = load_ticket_context_dict(ticket_details)
    
    previous_ticket_context = (
        state.get(
            "previous_ticket_context"
        )
    )
        
    # Invoke LLM-as-Judge
    evaluation = (
        llm_judge_chain.invoke(
            {
                "conversation_history":
                    conversation_history,

                "user_query":
                    state["current_user_query"],

                "intent":
                    state["intent"],
                
                "ticket_context":
                    ticket_context,
                
                "previous_ticket_context":
                    previous_ticket_context,
                
                "workflow_ticket_action":
                    state.get("workflow_ticket_action",""),

                "final_response":
                    state["final_response"]
            }
        )
    )

    # Build Faild Parameters
    failed_params = []
    failure_reasoning = []

    if (evaluation.intent_handling_score< 9): # type: ignore
        failed_params.append("Intent Handling")
        failure_reasoning.append(
            f"Intent Handling: "
            f"{evaluation.intent_handling_reasoning}" # type: ignore
        )

    if (evaluation.workflow_compliance_score< 9): # type: ignore
        failed_params.append("Workflow Compliance")
        failure_reasoning.append(
            f"Workflow Compliance: "
            f"{evaluation.workflow_compliance_reasoning}" # type: ignore
        )
    if (evaluation.customer_experience_score< 9): # type: ignore
        failed_params.append("Customer Experience")
        failure_reasoning.append(
            f"Customer Experience: "
            f"{evaluation.customer_experience_reasoning}" # type: ignore
        )
    if (evaluation.groundedness_score< 9): # type: ignore
        failed_params.append("Groundedness")
        failure_reasoning.append(
            f"Groundedness: "
            f"{evaluation.groundedness_reasoning}" # type: ignore
        )

    # Updated Judge Passed Flag
    judge_passed = (len(failed_params)== 0)

    # Calculate Overall Score
    overall_score = round(
    (
        evaluation.intent_handling_score # type: ignore
        +
        evaluation.workflow_compliance_score # type: ignore
        +
        evaluation.customer_experience_score # type: ignore
        +
        evaluation.groundedness_score # type: ignore
    ) / 4, 1
    )

    # Append Evaluation History for Evals Dashboard 
    evaluation_history.append(
    {
        "query":
            state["current_user_query"],

        "intent":
            state["intent"],

        "workflow_ticket_action":
            state.get(
                "workflow_ticket_action",
                ""
            ),

        "overall_score":
            overall_score,

        "judge_passed":
            judge_passed,

        "reflection_count":
            state["reflection_count"],

        "failed_params":
            failed_params,

        "intent_handling_score":
            evaluation.intent_handling_score, # type: ignore

        "intent_handling_reasoning":
            evaluation.intent_handling_reasoning, # type: ignore

        "workflow_compliance_score":
            evaluation.workflow_compliance_score, # type: ignore

        "workflow_compliance_reasoning":
            evaluation.workflow_compliance_reasoning, # type: ignore

        "customer_experience_score":
            evaluation.customer_experience_score, # type: ignore

        "customer_experience_reasoning":
            evaluation.customer_experience_reasoning, # type: ignore

        "groundedness_score":
            evaluation.groundedness_score, # type: ignore

        "groundedness_reasoning":
            evaluation.groundedness_reasoning, # type: ignore

        "judge_strengths":
            evaluation.judge_strengths, # type: ignore

        "judge_improvements":
            evaluation.judge_improvements # type: ignore
    }
    )
    
    # Add Trace
    judge_trace = [
            f"Workflow Ticket Action={state.get('workflow_ticket_action')}",
            f"Previous Ticket Context Available={state.get('previous_ticket_context') is not None}",
            f"Intent Handling={evaluation.intent_handling_score}", # type: ignore
            f"Workflow Compliance={evaluation.workflow_compliance_score}", # type: ignore
            f"Customer Experience={evaluation.customer_experience_score}", # type: ignore
            f"Groundedness={evaluation.groundedness_score}", # type: ignore
            f"Overall Score={overall_score}",
            f"Judge Passed={judge_passed}",
            f"Failed Parameters={failed_params}",
            f"Reflection Count={state['reflection_count']}"
                ]
    
    judge_trace.extend(
        failure_reasoning
    )
    
    judge_trace.extend(
        [
            f"Judge Improvement Comments: {item}"
            for item in evaluation.judge_improvements # type: ignore
        ]
    )
    add_trace(
        execution_trace,
        "LLM Judge",
        judge_trace
    )

    # -----------------------------------------------------------------------------------------------------------------------
    # append final response to messages and store eval results in db (user query is already appended in each of the handlers)
    # -----------------------------------------------------------------------------------------------------------------------

    final_response_approved = (
        judge_passed
        or
        state["reflection_count"] >= MAX_REFLECTION_COUNT
    )

    if final_response_approved:

        # Save Evaluation Results in DB
        save_evaluation_result(

            thread_id=state.get(
                "thread_id",
                ""
            ),

            customer_email=
                state["customer_email"],

            query=state["current_user_query"],

            final_response=state["final_response"],

            intent=state["intent"],

            workflow_ticket_action=state.get(
                "workflow_ticket_action",
                ""
            ),

            overall_score=overall_score,

            judge_passed=judge_passed,

            reflection_count=state["reflection_count"],

            intent_handling_score=
                evaluation.intent_handling_score, # type: ignore

            intent_handling_reasoning=
                evaluation.intent_handling_reasoning, # type: ignore

            workflow_compliance_score=
                evaluation.workflow_compliance_score, # type: ignore

            workflow_compliance_reasoning=
                evaluation.workflow_compliance_reasoning, # type: ignore

            customer_experience_score=
                evaluation.customer_experience_score, # type: ignore

            customer_experience_reasoning=
                evaluation.customer_experience_reasoning, # type: ignore

            groundedness_score=
                evaluation.groundedness_score, # type: ignore

            groundedness_reasoning=
                evaluation.groundedness_reasoning, # type: ignore

            failed_params=
                failed_params,

            judge_strengths=
                evaluation.judge_strengths, # type: ignore

            judge_improvements=
                evaluation.judge_improvements # type: ignore
        )

        # Save Assitant Final Response to Messages
        updated_messages.append(
            AIMessage(
                content=state["final_response"]
            )
        )

    return {

        "messages":
            updated_messages,

        "intent_handling_score":
            evaluation.intent_handling_score, # type: ignore

        "intent_handling_reasoning":
            evaluation.intent_handling_reasoning, # type: ignore

        "workflow_compliance_score":
            evaluation.workflow_compliance_score, # type: ignore

        "workflow_compliance_reasoning":
            evaluation.workflow_compliance_reasoning, # type: ignore

        "customer_experience_score":
            evaluation.customer_experience_score, # type: ignore

        "customer_experience_reasoning":
            evaluation.customer_experience_reasoning, # type: ignore

        "groundedness_score":
            evaluation.groundedness_score, # type: ignore

        "groundedness_reasoning":
            evaluation.groundedness_reasoning, # type: ignore

        "judge_strengths":
            evaluation.judge_strengths, # type: ignore

        "judge_improvements":
            evaluation.judge_improvements, # type: ignore

        "failed_params":
            failed_params,

        "judge_passed":
            judge_passed,

        "overall_score":
            overall_score,

        "evaluation_history":
            evaluation_history,

        "execution_trace":
            execution_trace
    }

# ==============================================================================================================================================
# Customer Intelligence Agent Node
# ==============================================================================================================================================

def customer_intelligence_agent_node(
    state: BankingSupportState
):
    # ------------------------------------------------------
    # Context
    # ------------------------------------------------------

    customer_email = state.get(
        "customer_email",
        ""
    )

    intent = state.get(
        "intent",
        ""
    )

    # ------------------------------------------------------
    # Retrieve Historical Customer Data
    # ------------------------------------------------------

    customer_profile = (
        get_customer_profile(
            customer_email
        )
    )

    evaluation_profile = (
        get_customer_evaluation_profile(
            customer_email
        )
    )

    # ------------------------------------------------------
    # Build Customer Intelligence Context
    # ------------------------------------------------------

    customer_intelligence_context = {

        "intent":
            intent,

        "customer_profile":
            json.dumps(
                customer_profile,
                indent=2
            ),

        "evaluation_profile":
            json.dumps(
                evaluation_profile,
                indent=2
            )
    }

    # ------------------------------------------------------
    # Invoke Customer Intelligence Chain
    # ------------------------------------------------------
       
    result = (
        llm_customer_intelligence_chain.invoke(
            customer_intelligence_context
        )
    )

    # ------------------------------------------------------
    # Return
    # ------------------------------------------------------

    return {

        "customer_satisfaction_summary":
            result.customer_satisfaction_summary, # type: ignore

        "customer_issue_profile":
            result.customer_issue_profile, # type: ignore

        "customer_communication_profile":
            result.customer_communication_profile, # type: ignore

        "customer_response_guidance":
            result.customer_response_guidance, # type: ignore

        "customer_sensitivity":
            result.customer_sensitivity # type: ignore
    }