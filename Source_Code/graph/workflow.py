from langgraph.graph import StateGraph, END

from langgraph.checkpoint.memory import InMemorySaver
from graph.state import BankingSupportState
from graph.nodes import *
from graph.edges import *
from llm.llm_models import *

def build_graph():

    builder = StateGraph(BankingSupportState)

    builder.add_node(
        "classifier",
        classifier_node
    )

    builder.add_node(
        "positive_agent",
        positive_agent_node
    )

    builder.add_node(
        "negative_agent",
        negative_agent_node
    )

    builder.add_node(
        "inquiry_agent",
        inquiry_agent_node
    )

    builder.add_node(
        "response_generator",
        response_generator_node
    )

    builder.add_node(
        "llm_judge",
        llm_judge_node
    )

    builder.add_node(
        "customer_intelligence_agent",
        customer_intelligence_agent_node
        )

    builder.set_entry_point(
        "classifier"
    )

    builder.add_edge(
        "classifier",
        "customer_intelligence_agent"
    )

    # Intent Routing
    builder.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "positive": "positive_agent",

            "negative": "negative_agent",

            "inquiry": "inquiry_agent"
        }
    )

    builder.add_edge(
        "customer_intelligence_agent",
        "response_generator"
    )
    
    
    builder.add_edge(
        "positive_agent",
        "response_generator"
    )

    builder.add_edge(
        "negative_agent",
        "response_generator"
    )

    builder.add_edge(
        "inquiry_agent",
        "response_generator"
    )
    
    builder.add_edge(
        "response_generator",
        "llm_judge"
    )

    # Reflection Loop
    builder.add_conditional_edges(
        "llm_judge",
        route_after_judge,
        {
            "retry":
                "response_generator",

            "pass":
                END
        }
    )
    
    memory = InMemorySaver()
    
    graph = builder.compile(checkpointer=memory)

    return graph