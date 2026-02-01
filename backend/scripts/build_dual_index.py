import json
from pathlib import Path
from datetime import datetime, timezone
import calendar

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

DATA = Path("data")
JSONL = DATA / "projects.jsonl"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

OUT_ALL_INDEX = DATA / "index_all.faiss"
OUT_RECENT_INDEX = DATA / "index_recent.faiss"
OUT_META = DATA / "projects_meta.json"
OUT_EMB = DATA / "embeddings.npy"
OUT_RECENT_ROWS = DATA / "recent_row_ids.json"

RECENT_MONTHS = 24  # change to 12/36 as you like


def parse_dt(s: str | None):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def month_subtract(dt: datetime, months: int) -> datetime:
    """Subtract N months from dt without numpy; clamps day to last day of target month."""
    y = dt.year
    m = dt.month - months
    while m <= 0:
        m += 12
        y -= 1
    last_day = calendar.monthrange(y, m)[1]
    d = min(dt.day, last_day)
    return dt.replace(year=y, month=m, day=d)


def l2_normalize(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norm


def main():
    DATA.mkdir(parents=True, exist_ok=True)

    projects = []
    with JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            projects.append(json.loads(line))

    if not projects:
        raise RuntimeError("projects.jsonl is empty")

    # Prefer embedding a compact "search_text" if present; fallback to "text"
    texts = []
    for p in projects:
        t = (p.get("search_text") or "").strip()
        if not t:
            t = (p.get("text") or "").strip()
        texts.append(t)

    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(texts, batch_size=64, show_progress_bar=True).astype("float32")
    emb = l2_normalize(emb)
    np.save(OUT_EMB, emb)

    with OUT_META.open("w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False)

    d = emb.shape[1]

    # All-time index (cosine via inner product on normalized vectors)
    idx_all = faiss.IndexFlatIP(d)
    idx_all.add(emb)
    faiss.write_index(idx_all, str(OUT_ALL_INDEX))

    # Recent index: define "recent" by pushed_at (what’s active lately)
    now = datetime.now(timezone.utc)
    cutoff = month_subtract(now, RECENT_MONTHS)

    recent_rows = []
    for i, p in enumerate(projects):
        dt = parse_dt(p.get("pushed_at")) or parse_dt(p.get("created_at"))
        if dt and dt >= cutoff:
            recent_rows.append(i)

    emb_recent = emb[recent_rows] if recent_rows else emb[:0]
    idx_recent = faiss.IndexFlatIP(d)
    if len(recent_rows) > 0:
        idx_recent.add(emb_recent)
    faiss.write_index(idx_recent, str(OUT_RECENT_INDEX))

    OUT_RECENT_ROWS.write_text(json.dumps(recent_rows), encoding="utf-8")

    print(f"All-time: {len(projects)} projects")
    print(f"Recent (>= {cutoff.date()} by pushed_at): {len(recent_rows)} projects")
    print(f"Wrote: {OUT_ALL_INDEX}, {OUT_RECENT_INDEX}, {OUT_META}, {OUT_RECENT_ROWS}, {OUT_EMB}")


if __name__ == "__main__":
    main()