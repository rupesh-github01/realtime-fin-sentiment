# app/handler.py
import asyncio
import json
from asyncio import Queue
from pathlib import Path
from datetime import datetime
from app.ingest import simulate_stream, consumer
from app.preprocessor import normalize_item
from app.indexer import VectorIndexer
from app.rag import RAGSummarizer

LIVE_FEED = Path(__file__).resolve().parents[1] / "data" / "live_feed.jsonl"
LIVE_FEED.parent.mkdir(parents=True, exist_ok=True)

indexer = VectorIndexer(persist_directory="chroma_db")
rag = RAGSummarizer(chroma_persist="chroma_db")

async def handle(item):
    """
    item: already-normalized dict from preprocessor.normalize_item
    Steps:
      1. add to index
      2. call rag summarizer (runs in thread)
      3. append enriched item to data/live_feed.jsonl
    """
    try:
        doc_id = item["id"]
        text = item["text"]
        # 1) index (blocking call executed in thread)
        await asyncio.to_thread(indexer.add_item, doc_id, text, item)
        # 2) generate summary via RAG (blocking -> thread)
        # Provide ticker as query when available for better grounding
        query = item.get("ticker") or text[:80]
        summary = await asyncio.to_thread(rag.summarize, query)
        # 3) attach summary and store to live feed
        enriched = dict(item)
        enriched["summary"] = summary
        enriched["received_at"] = datetime.utcnow().isoformat()
        with LIVE_FEED.open("a", encoding="utf-8") as f:
            f.write(json.dumps(enriched, default=str) + "\n")
        print(f"[HANDLED] {doc_id} ticker={item.get('ticker')} summary={summary[:80]!s}")
    except Exception as e:
        print("Error in handle:", e)

async def main(replay_delay: float = 1.0):
    q = Queue()
    # start producer
    prod = asyncio.create_task(simulate_stream(q, delay=replay_delay))
    # start consumer which delegates to our handle
    cons = asyncio.create_task(consumer(q, handle))
    await prod
    # wait until queue processed
    await q.join()
    cons.cancel()

if __name__ == "__main__":
    # optional: change delay to speed up replay
    asyncio.run(main(replay_delay=1.0))
