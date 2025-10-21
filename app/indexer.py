# app/indexer.py
from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings

# Use a small sentence-transformer
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class VectorIndexer:
    def __init__(self, persist_directory="chroma_db"):
        self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection("news")
        self.embed = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    def add_item(self, doc_id: str, text: str, metadata: dict):
        emb = self.embed.embed_query(text)
        # chroma expects list for embeddings
        self.collection.add(documents=[text], metadatas=[metadata], ids=[doc_id], embeddings=[emb])
        self.client.persist()

    def query(self, query_text: str, k=3):
        emb = self.embed.embed_query(query_text)
        res = self.collection.query(query_embeddings=[emb], n_results=k)
        return res
