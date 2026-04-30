from langchain_core.tools import tool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_chroma import Chroma

_vectorstore = None


def set_vectorstore(vs):
    global _vectorstore
    _vectorstore = vs


@tool
def search_knowledge_base(query: str) -> str:
    """Ищет информацию в базе знаний по стажировке CdekStart."""
    if _vectorstore is None:
        return "База знаний недоступна."

    docs = _vectorstore.similarity_search(query, k=4)

    if not docs:
        return "Информация не найдена."

    results = []
    for doc in docs:
        source = doc.metadata.get("source_file", "unknown")
        results.append(f"[Источник: {source}]\n{doc.page_content}")

    return "\n\n---\n\n".join(results)