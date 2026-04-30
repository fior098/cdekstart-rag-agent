from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.tools import search_knowledge_base
from app.config import settings
import json
import re


SYSTEM_PROMPT = """Ты — консультант программы международной стажировки "CdekStart".

## 1. Источник информации
Отвечай ТОЛЬКО на основе предоставленного контекста базы знаний. Не используй внешние знания.

## 2. Запрет на выдумывание
Не выдумывай цифры, даты, правила, требования или любую другую информацию. Если ответа нет в контексте — скажи: «Информация по вашему вопросу не найдена в базе знаний программы.»

## 3. Локации программы
В программе две локации: Германия (Берлин) и Франция (Париж). У каждой локации свои правила. Не путай страны.

## 4. Если пользователь указал страну
Ищи информацию ТОЛЬКО по указанной стране. Если по указанной стране информации нет — сообщи об этом.

## 5. Если пользователь не указал страну (одна страна в контексте)
Если в контексте присутствует информация только по одной стране — отвечай по этой стране без уточнения.

## 6. Если пользователь не указал страну (две страны в контексте)
Если в контексте присутствует информация по обеим странам — задай уточняющий вопрос: «Вы спрашиваете про Германию (Берлин) или Францию (Париж)?»

## 7. Вопросы, требующие уточнения страны
Налог, стипендия, рабочий день, виза, даты подачи заявок, даты начала стажировки — всегда требуют уточнения, если пользователь не назвал страну.

## 8. Общие вопросы
Если вопрос касается программы в целом (подача заявки, этапы отбора, условия проживания, проезд, страховка, сертификат) — ищи информацию в контексте. Если данные по странам различаются — уточни страну.

## 9. Учёт истории диалога
Если пользователь уже назвал страну в предыдущих сообщениях — используй эту информацию. Если пользователь меняет страну — ориентируйся на последнее упоминание.

## 10. Язык общения
Отвечай на том языке, на котором пишет пользователь.

## 11. Структура ответа
Давай чёткие структурированные ответы. Выделяй ключевые цифры и даты.

## 12. Вне темы программы
Если вопрос не относится к программе — вежливо скажи, что ты можешь помочь только с вопросами о стажировке CdekStart.

## 13. Неуверенность
Если ты не уверен в ответе — лучше уточни, чем отвечать наугад.

## 14. Приоритет явного указания
Явное указание страны пользователем имеет приоритет над любыми предположениями из контекста.

## 15. Контекст
Контекст базы знаний:
{context}
"""

CLARIFICATION_DETECTION_PROMPT = """Ответь ТОЛЬКО валидным JSON объектом, без пояснений, без markdown.

Вопрос пользователя: {question}

Контекст: {context}

Нужно ли уточнить страну (Германия или Франция)?
Ответь строго так:
{{"needs_clarification": true}} или {{"needs_clarification": false}}"""

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
    needs_clarification = False

    try:
        content = response.content.strip()

        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()

        json_match = re.search(r"\{.*?\}", content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        parsed = json.loads(content)

        if isinstance(parsed, dict):
            val = parsed.get("needs_clarification", False)
            if isinstance(val, str):
                needs_clarification = val.lower() == "true"
            else:
                needs_clarification = bool(val)
        else:
            needs_clarification = False

    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"Не удалось распарсить ответ LLM: {response.content!r}, ошибка: {e}"
        )
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

    if not context or context == "Информация не найдена.":
        context = "В базе знаний нет информации по этому вопросу."

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