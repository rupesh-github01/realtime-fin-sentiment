# app/rag.py
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class RAGSummarizer:
    def __init__(self, chroma_persist="chroma_db"):
        # embedding function (local)
        self.emb = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        # vectorstore (wraps the same Chroma DB used by indexer)
        self.vs = Chroma(persist_directory=chroma_persist, embedding_function=self.emb)
        # LLM: requires OPENAI_API_KEY env var. Swap for other providers if you want.
        self.llm = OpenAI(temperature=0)
        self.qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.vs.as_retriever())

    def summarize(self, query: str):
        """
        Return one-line summary + 2 reasons grounded in sources.
        """
        prompt = f"Summarize the latest information about '{query}' in one short sentence. Then list up to 2 brief grounded reasons (cite source ids)."
        # RetrievalQA will fetch relevant docs and run the LLM
        return self.qa.run(prompt)
