from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    LLM_PROVIDER: Literal["openai", "ollama", "gigachat"] = "openai"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"

    GIGACHAT_API_KEY: str = ""
    GIGACHAT_MODEL: str = "GigaChat"

    EMBEDDING_PROVIDER: Literal["openai", "ollama"] = "openai"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_PERSIST_DIR: str = "./chroma_db"
    DATA_DIR: str = "./data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()