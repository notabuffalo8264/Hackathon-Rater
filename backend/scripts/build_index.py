import json
from pathlib import Path
from datetime import datetime, timezone
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
    """Subtract months without extra deps; clamps day to last day of resulting month."""
    y = dt.year
    m = dt.month - months
    while m <= 0:
        m += 12
        y -= 1
    # clamp day
    import calendar
    last_day = calendar.monthrange(y, m)[1]
    d = min(dt.day, last_day)
    return dt.replace(year=y, month=m, day=d)


def safe_normalize(emb: np.ndarray) -> np.ndarray:
    emb = np.nan_to_num(emb, nan=0.0, posinf=0.0, neginf=0.0).astype("float32")
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return emb / norms


def choose_text(p: dict) -> str:
    # Prefer the shorter “search_text” if available; fallback to “text”
    st = (p.get("search_text") or "").strip()
    if len(st) >= 20:
        return st
    return (p.get("text") or "").strip()


def main():
    projects = []
    with JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                projects.append(json.loads(line))
            except Exception:
                continue

    if not projects:
        raise RuntimeError("projects.jsonl is empty or unreadable")

    texts = [choose_text(p) for p in projects]

    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(texts, batch_size=64, show_progress_bar=True).astype("float32")
    emb = safe_normalize(emb)

    # Save embeddings (optional)
    np.save(OUT_EMB, emb)

    # Save meta aligned to embeddings
    OUT_META.write_text(json.dumps(projects, ensure_ascii=False), encoding="utf-8")

    d = emb.shape[1]

    # All-time index (cosine similarity because vectors are normalized)
    idx_all = faiss.IndexFlatIP(d)
    idx_all.add(emb)
    faiss.write_index(idx_all, str(OUT_ALL_INDEX))

    # Recent index
    now = datetime.now(timezone.utc)
    cutoff = month_subtract(now, RECENT_MONTHS)

    recent_rows: list[int] = []
    for i, p in enumerate(projects):
        dt = parse_dt(p.get("created_at")) or parse_dt(p.get("pushed_at"))
        if dt and dt >= cutoff:
            recent_rows.append(i)

    emb_recent = emb[recent_rows] if recent_rows else emb[:0]
    idx_recent = faiss.IndexFlatIP(d)
    if len(recent_rows) > 0:
        idx_recent.add(emb_recent)
    faiss.write_index(idx_recent, str(OUT_RECENT_INDEX))

    OUT_RECENT_ROWS.write_text(json.dumps(recent_rows), encoding="utf-8")

    print(f"All-time: {len(projects)} projects")
    print(f"Recent (>= {cutoff.date()}): {len(recent_rows)} projects")


if __name__ == "__main__":
    main()