from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from typing import Literal
from llm.prompts import *
from graph.utils import *

import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ==========================================================
# Initialize LLM - Determinitstic
# ==========================================================

def get_llm():

    llm =  ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY, # type: ignore
            temperature=0
        )
    return llm

# ==========================================================
# Initialize LLM - Less Determinitstic (For Final Response)
# ==========================================================

def get_llm_FR():

    llm =  ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY, # type: ignore
            temperature=0.2
        )
    return llm


# ==========================================================
# LLM - Classifier
# ==========================================================

class ClassificationOutput(BaseModel):

    intent: str = Field(
        description=
        "positive, negative or inquiry"
    )

    interaction_type: str = Field(
        description=
        "new or follow_up"
    )

    resolution_confirmation: bool = Field(
        description=
        (
            "True only when the customer explicitly "
            "confirms that the issue is resolved, fixed, "
            "working, completed or the ticket can be closed."
        )
    )

    classification_reasoning: str = Field(
        description=
        "One sentence reasoning for classification."
    )

get_llm_classifier = get_llm()

llm_classifier = (
    get_llm_classifier.with_structured_output(
        ClassificationOutput
    )
)

llm_classifier_chain = CLASSIFIER_PROMPT | llm_classifier

# ==========================================================
# LLM - Inquiry Agent
# ==========================================================

get_llm_inquiry = get_llm()

# translates a multi-layered LangChain blueprint object (ChatPromptTemplate) down into a single, clean Python string
formatted_prompt = INQUIRY_AGENT_PROMPT.format()

inquiry_agent = create_agent(
    model= get_llm_inquiry,
    tools= [lookup_ticket],
    system_prompt= formatted_prompt
)

# ==========================================================
# LLM - Negative Agent
# ==========================================================

get_llm_negative = get_llm()

formatted_prompt = NEGATIVE_AGENT_PROMPT.format()

negative_agent = create_agent(
    model=get_llm_negative,
    tools=[lookup_ticket, create_ticket],
    system_prompt=formatted_prompt
)

# ==========================================================
# LLM - Response Generator
# ==========================================================

class ResponseGeneratorOutput(
    BaseModel
):
    user_response: str


get_llm_response_generator = get_llm_FR()

llm_response_generator = (
    get_llm_response_generator.with_structured_output(
        ResponseGeneratorOutput
    )
)

llm_response_generator_chain = RESPONSE_GENERATOR_PROMPT | llm_response_generator

# ==========================================================
# LLM - Judge
# ==========================================================

from pydantic import BaseModel, Field


class JudgeOutput(BaseModel):

    intent_handling_score: float = Field(
        description="Score from 1 to 10 for intent handling."
    )
    intent_handling_reasoning: str = Field(
        description="Reasoning for intent handling score."
    )
    workflow_compliance_score: float = Field(
        description="Score from 1 to 10 for workflow compliance."
    )
    workflow_compliance_reasoning: str = Field(
        description="Reasoning for workflow compliance score."
    )
    customer_experience_score: float = Field(
        description="Score from 1 to 10 for customer experience."
    )
    customer_experience_reasoning: str = Field(
        description="Reasoning for customer experience score."
    )
    groundedness_score: float = Field(
        description="Score from 1 to 10 for groundedness."
    )
    groundedness_reasoning: str = Field(
        description="Reasoning for groundedness score."
    )
    judge_strengths: list[str] = Field(
        description="Meaningful strengths identified in the final response."
    )
    judge_improvements: list[str] = Field(
        description="Actionable improvements required to achieve scores of 9 or higher across all failed parameters."
    )

get_llm_judge = get_llm()

llm_judge = (
    get_llm_judge.with_structured_output(
        JudgeOutput
    )
)

llm_judge_chain = JUDGE_PROMPT | llm_judge

# ==========================================================
# LLM - Customer Intelligence Agent
# ==========================================================

class CustomerIntelligenceOutput(BaseModel):

    customer_satisfaction_summary: str = Field(
        description=
        """
        Summarize overall customer satisfaction using:

        - evaluation_count
        - thumbs_up_count
        - thumbs_down_count
        - no_feedback_count
        - avg_overall_score

        Include:

        - total conversations
        - feedback participation
        - participation rate
        - satisfaction trend
        - overall experience quality

        Keep concise and evidence-based.
        """
    )

    customer_issue_profile: str = Field(
        description=
        """
        Summarize recurring customer issue patterns using:

        - historical_queries
        - intent history
        - workflow history

        Identify:

        - recurring issue categories
        - recurring inquiry patterns
        - recurring operational concerns
        - recurring service requests

        Focus on repeated patterns.

        Ignore isolated events.
        """
    )

    customer_communication_profile: str = Field(
        description=
        """
        Summarize customer communication preferences.

        Use ONLY customer feedback comments.

        Examples:

        - prefers detailed updates
        - values clarity
        - appreciates responsiveness

        If insufficient evidence exists, explicitly state:

        'Communication preferences cannot be determined confidently from available customer feedback history.'
        """
    )

    customer_response_guidance: str = Field(
        description=
        """
        Generate actionable guidance for future Response Generators.

        Consider:

        - recurring issue patterns
        - satisfaction history
        - judge recommendations
        - current intent

        Examples:

        - increase empathy
        - provide timelines
        - acknowledge previous interactions
        - provide proactive status updates
        - use structured troubleshooting

        Guidance should be specific and actionable.
        """
    )

    customer_sensitivity: Literal[
        "LOW",
        "MEDIUM",
        "HIGH"
    ] = Field(
        description=
        """
        Customer relationship risk.

        LOW:
        Predominantly positive history,
        few complaints,
        strong evaluation scores.

        MEDIUM:
        Multiple complaints,
        recurring concerns,
        mixed satisfaction trend.

        HIGH:
        Frequent dissatisfaction,
        escalation indicators,
        repeated unresolved concerns.

        Return ONLY:
        LOW
        MEDIUM
        HIGH
        """
    )

get_customer_intelligence = get_llm()

llm_customer_intelligence = (
    get_customer_intelligence.with_structured_output(
        CustomerIntelligenceOutput
    )
)

llm_customer_intelligence_chain = CUSTOMER_INTELLIGENCE_AGENT_PROMPT | llm_customer_intelligence