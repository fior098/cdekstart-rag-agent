from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from contextlib import asynccontextmanager
from typing import Dict, List
import logging

from app.models import ChatRequest, ChatResponse
from app.agent.graph import build_graph
from app.agent.tools import set_vectorstore
from app.agent.rag.indexer import get_or_create_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sessions: Dict[str, List] = {}
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph

    logger.info("Инициализация векторного индекса...")
    vectorstore = get_or_create_index()
    set_vectorstore(vectorstore)
    logger.info("Векторный индекс готов.")

    graph = build_graph()
    logger.info("LangGraph агент собран.")

    yield

    logger.info("Завершение работы приложения.")


app = FastAPI(
    title="CdekStart RAG Agent",
    description="Чат-бот для консультации по международной стажировке CdekStart",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if graph is None:
        raise HTTPException(status_code=503, detail="Агент не инициализирован.")

    session_id = request.session_id
    user_message = request.message

    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append(HumanMessage(content=user_message))

    initial_state = {
        "messages": sessions[session_id].copy(),
        "context": "",
        "needs_clarification": False,
        "clarification_question": "",
        "final_answer": "",
        "retrieved_docs": [],
    }

    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка агента: {str(e)}")

    final_answer = result.get("final_answer", "Не удалось получить ответ.")
    needs_clarification = result.get("needs_clarification", False)

    sessions[session_id].append(AIMessage(content=final_answer))

    if len(sessions[session_id]) > 20:
        sessions[session_id] = sessions[session_id][-20:]

    return ChatResponse(
        session_id=session_id,
        response=final_answer,
        needs_clarification=needs_clarification,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "cleared", "session_id": session_id}