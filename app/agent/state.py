from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    context: str
    needs_clarification: bool
    clarification_question: str
    final_answer: str
    retrieved_docs: List[str]