# app/ingest.py
import asyncio
import json
from pathlib import Path
from asyncio import Queue
from typing import AsyncIterator
from app.preprocessor import normalize_item

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "sample_news.jsonl"

async def simulate_stream(queue: Queue, delay: float = 1.0):
    with open(DATA_FILE, "r") as f:
        for line in f:
            raw = json.loads(line)
            normalized = normalize_item(raw)
            await queue.put(normalized)
            await asyncio.sleep(delay)  # simulate arrival
    # keep alive (in real app, the stream would be ongoing)
    await asyncio.sleep(0.1)

async def consumer(queue: Queue, handler):
    while True:
        item = await queue.get()
        try:
            await handler(item)
        except Exception as e:
            print("handler error", e)
        queue.task_done()

# Example handler placeholder
async def print_handler(item):
    print("RECEIVED", item)

async def main():
    q = Queue()
    prod = asyncio.create_task(simulate_stream(q, delay=1.0))
    cons = asyncio.create_task(consumer(q, print_handler))
    await prod
    await q.join()
    cons.cancel()

if __name__ == "__main__":
    asyncio.run(main())
