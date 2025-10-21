import re
from datetime import datetime
from typing import Dict
import math

POS_WORDS = {"good","great","positive","praise","beats","beats expectations","jumps","rise","strong","upgrade"}
NEG_WORDS = {"concern","recall","drop","decline","worse","question","regulatory","down","risk","delay"}

def extract_ticker(text : str, meta: Dict):
    if meta.get('ticker'):
        return meta['ticker'].upper()
    m = re.findall(r"\$([A-Z]{1,5}",text)
    if m:
        return m[0]
    caps = re.findall(r"\b([A-Z]{2,5})\b", text)
    return caps[0] if caps else None

def simple_sentiment(text:str):
    txt = text.lower()
    pos = sum(1 for w in POS_WORDS if w in txt)
    neg = sum(1 for w in NEG_WORDS if w in txt)

    score = (pos-neg)/max(1,pos+neg) if (pos+neg) > 0 else 0.0
    return max(-1.0,min(1.0,score))

def normalize_item(raw: Dict):
    text = raw.get("text","")
    ts = raw.get("timestamp")
    try:
        ts = datetime.fromisoformat(ts.replace("Z","+00:00"))
    except Exception:
        ts = datetime.utcnow()
    ticker = extract_ticker(text, raw)
    sentiment = simple_sentiment(text)
    return {
        "id": raw.get("id"),
        "timestamp": ts.isoformat(),
        "ticker": ticker,
        "source": raw.get("source",""),
        "text": text,
        "sentiment": sentiment
    }