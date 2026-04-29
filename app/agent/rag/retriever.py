from langchain_community.vectorstores import Chroma
from app.config import settings


def get_embeddings():
    if settings.EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)

    if settings.EMBEDDING_PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_EMBEDDING_MODEL,
        )

    raise ValueError(f"Неизвестный EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")


def get_retriever(vectorstore: Chroma):
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )