from pydantic_settings import BaseSettings
from typing import Literal
from pathlib import Path

class Settings(BaseSettings):
    LLM_PROVIDER: Literal["openai", "ollama", "gigachat"] = "ollama"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    GIGACHAT_API_KEY: str = ""
    GIGACHAT_MODEL: str = "GigaChat"

    EMBEDDING_PROVIDER: Literal["openai", "ollama"] = "ollama"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_PERSIST_DIR: str = "./chroma_db"
    DATA_DIR: str = "./data"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"

settings = Settings()