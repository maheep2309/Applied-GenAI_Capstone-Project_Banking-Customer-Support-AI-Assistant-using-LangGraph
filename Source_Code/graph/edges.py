from graph.utils import *

# ==========================================================
# Intent Router
# ==========================================================

def route_intent(state):
    add_trace(
        state["execution_trace"],
        "Intent Router",
        [
            f"Classified Intent={state['intent']}",
            f"Classified Interation Type={state['interaction_type']}",
            f"Classification Reasoning={state['classification_reasoning']}",
            f"Resolution Confirmation={state['resolution_confirmation']}"
        ]
    )
    return state["intent"]


# ==========================================================
# Reflection Router
# ==========================================================

MAX_REFLECTION_COUNT = 5

def route_after_judge(state):

    if state["judge_passed"]:
        
        add_trace(
            state["execution_trace"],
            "Judge Router",
            [
                f"Judge Passed={state['judge_passed']}",
                f"Reflection Count={state['reflection_count']}",
                f"Failed Parameters={state['failed_params']}"
            ]
        )
        
        return "pass"
    if state["reflection_count"] >= MAX_REFLECTION_COUNT:
        
        add_trace(
            state["execution_trace"],
            "Judge Router",
            [
                f"Judge Passed={state['judge_passed']}",
                f"Reflection Count={state['reflection_count']}",
                f"Failed Parameters={state['failed_params']}"
            ]
        )
        
        return "pass"
    
    return "retry"