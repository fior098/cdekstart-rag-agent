from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    retrieve_node,
    check_clarification_node,
    generate_answer_node,
    clarification_answer_node,
    should_clarify,
)


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("check_clarification", check_clarification_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("clarification_answer", clarification_answer_node)

    workflow.set_entry_point("retrieve")

    workflow.add_edge("retrieve", "check_clarification")

    workflow.add_conditional_edges(
        "check_clarification",
        should_clarify,
        {
            "clarify": "clarification_answer",
            "answer": "generate_answer",
        },
    )

    workflow.add_edge("generate_answer", END)
    workflow.add_edge("clarification_answer", END)

    return workflow.compile()