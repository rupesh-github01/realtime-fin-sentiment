# app/dashboard.py
import streamlit as st
import pandas as pd
from pathlib import Path
import json
import time

LIVE_FEED = Path(__file__).resolve().parents[1] / "data" / "live_feed.jsonl"

st.set_page_config(page_title="Real-Time News & Sentiment", layout="wide")
st.title("Real-Time Financial News & Sentiment Dashboard (Demo)")

def load_live_feed():
    if not LIVE_FEED.exists():
        return pd.DataFrame()
    rows = []
    with LIVE_FEED.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except:
                pass
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # ensure sentiment numeric
    if "sentiment" in df.columns:
        df["sentiment"] = pd.to_numeric(df["sentiment"], errors="coerce").fillna(0.0)
    return df

auto = st.checkbox("Auto-refresh every 3s", value=False)
if auto:
    # simple auto-refresh: wait then rerun
    time.sleep(3)
    st.experimental_rerun()

df = load_live_feed()

st.sidebar.header("Controls")
st.sidebar.write("Live feed file:", str(LIVE_FEED))
st.sidebar.write("Items in feed:", 0 if df.empty else len(df))
if st.sidebar.button("Manual refresh"):
    df = load_live_feed()

# Layout: feed left, charts right
col1, col2 = st.columns([2,3])

with col1:
    st.header("Live Feed (most recent first)")
    if df.empty:
        st.info("No live items yet. Run handler: `python app/handler.py`")
    else:
        # show latest 50
        for _, row in df.sort_values("received_at", ascending=False).head(50).iterrows():
            ticker = row.get("ticker") or "-"
            ts = row.get("received_at") or row.get("timestamp") or ""
            summary = row.get("summary", "")
            text = row.get("text","")
            st.markdown(f"**{ticker}**  `{ts}`  •  {row.get('source','')}")
            st.write(text)
            st.caption(summary)

with col2:
    st.header("Per-ticker rolling sentiment")
    if df.empty:
        st.info("No data to show.")
    else:
        # compute per-ticker rolling mean of last N events per ticker
        N = st.slider("Rolling window size (events)", min_value=3, max_value=100, value=10)
        # take most recent events grouped by ticker
        df_sorted = df.sort_values("received_at")
        # compute simple rolling averages over time per ticker
        charts = {}
        for ticker, group in df_sorted.groupby("ticker"):
            if ticker is None:
                continue
            g = group.tail(200)  # limit to recent history
            # cumulative mean (as a simple trend); could do time-windowed
            g = g.reset_index(drop=True)
            g["rolling_mean"] = g["sentiment"].rolling(window=min(N, len(g))).mean().fillna(method="bfill")
            charts[ticker] = g[["received_at","rolling_mean"]].set_index("received_at").rolling_mean
        if charts:
            # present top 4 tickers by count
            counts = df["ticker"].value_counts().head(4).index.tolist()
            for t in counts:
                g = df_sorted[df_sorted["ticker"]==t].tail(200).reset_index(drop=True)
                g["rolling_mean"] = g["sentiment"].rolling(window=min(N, len(g))).mean().fillna(method="bfill")
                if not g.empty:
                    st.subheader(f"{t} (last {len(g)} items)")
                    st.line_chart(g["rolling_mean"])
        else:
            st.info("No tickers found in feed.")
