from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.agent.state import AgentState
from app.agent.tools import search_knowledge_base
from app.config import settings


SYSTEM_PROMPT = """Ты — консультант программы международной стажировки "CdekStart".

Твои правила:
1. Отвечай ТОЛЬКО на основе предоставленного контекста из базы знаний.
2. Если в контексте нет информации — честно скажи об этом.
3. Никогда не выдумывай факты, цифры, даты.
4. Если вопрос касается конкретной страны (Германия или Франция), но страна не указана — задай уточняющий вопрос.
5. Если контекст содержит данные по обеим странам и пользователь не уточнил — спроси, какая страна интересует.
6. Общайся на том языке, на котором пишет пользователь.
7. Будь вежливым и профессиональным.

Контекст из базы знаний:
{context}
"""

CLARIFICATION_DETECTION_PROMPT = """Проанализируй вопрос пользователя и контекст из базы знаний.

Вопрос: {question}

Контекст: {context}

Определи:
1. Касается ли вопрос специфических правил страны (стипендия, налоги, виза, рабочий день)?
2. Если да — упомянул ли пользователь конкретную страну (Германия/Берлин или Франция/Париж)?

Ответь строго в формате JSON:
{{"needs_clarification": true/false, "reason": "краткое объяснение"}}

Только JSON, без пояснений."""


def get_llm():
    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1,
        )

    if settings.LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.1,
        )

    if settings.LLM_PROVIDER == "gigachat":
        from langchain_community.chat_models import GigaChat
        return GigaChat(
            credentials=settings.GIGACHAT_API_KEY,
            model=settings.GIGACHAT_MODEL,
            temperature=0.1,
            verify_ssl_certs=False,
        )

    raise ValueError(f"Неизвестный LLM_PROVIDER: {settings.LLM_PROVIDER}")


def retrieve_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    last_user_message = ""

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break

    history_context = ""
    if len(messages) > 1:
        history_parts = []
        for msg in messages[:-1]:
            if isinstance(msg, HumanMessage):
                history_parts.append(f"Пользователь: {msg.content}")
            elif isinstance(msg, AIMessage):
                history_parts.append(f"Ассистент: {msg.content}")
        history_context = "\n".join(history_parts[-6:])

    search_query = last_user_message
    if history_context:
        search_query = f"{history_context}\n{last_user_message}"

    result = search_knowledge_base.invoke({"query": search_query})

    return {
        **state,
        "context": result,
        "retrieved_docs": [result],
    }


def check_clarification_node(state: AgentState) -> AgentState:
    import json

    messages = state["messages"]
    context = state["context"]

    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break

    llm = get_llm()

    prompt = CLARIFICATION_DETECTION_PROMPT.format(
        question=last_user_message,
        context=context,
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content.strip())
        needs_clarification = parsed.get("needs_clarification", False)
    except Exception:
        needs_clarification = False

    clarification_question = ""
    if needs_clarification:
        clarification_question = (
            "Уточните, пожалуйста, какая страна вас интересует: "
            "Германия (Берлин) или Франция (Париж)?"
        )

    return {
        **state,
        "needs_clarification": needs_clarification,
        "clarification_question": clarification_question,
    }


def generate_answer_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    context = state["context"]

    llm = get_llm()

    system_message = SystemMessage(content=SYSTEM_PROMPT.format(context=context))

    chat_messages = [system_message] + list(messages)

    response = llm.invoke(chat_messages)

    return {
        **state,
        "final_answer": response.content,
        "needs_clarification": False,
    }


def clarification_answer_node(state: AgentState) -> AgentState:
    return {
        **state,
        "final_answer": state["clarification_question"],
        "needs_clarification": True,
    }


def should_clarify(state: AgentState) -> str:
    if state.get("needs_clarification", False):
        return "clarify"
    return "answer"