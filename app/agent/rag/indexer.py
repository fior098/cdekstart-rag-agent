import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from app.config import settings
from app.rag.retriever import get_embeddings


def load_documents():
    documents = []
    for filename in os.listdir(settings.DATA_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(settings.DATA_DIR, filename)
            loader = TextLoader(filepath, encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source_file"] = filename
            documents.extend(docs)
    return documents


def build_index():
    documents = load_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(documents)

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )

    return vectorstore


def get_or_create_index():
    embeddings = get_embeddings()

    if os.path.exists(settings.CHROMA_PERSIST_DIR) and os.listdir(
            settings.CHROMA_PERSIST_DIR
    ):
        vectorstore = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )
        return vectorstore

    return build_index()