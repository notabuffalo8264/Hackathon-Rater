import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

DATA = Path("data")
JSONL_PROJECTS = DATA / "projects.jsonl"
JSONL_DEVPOST = DATA / "devpost.jsonl"

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
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
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


def _join_tags(tags) -> str:
    if not tags:
        return ""
    if isinstance(tags, list):
        return " ".join([str(t) for t in tags if t])
    return str(tags)


def _make_search_text(p: dict) -> str:
    parts = []
    for key in ("title", "tagline", "description", "hackathon_name"):
        val = (p.get(key) or "").strip()
        if val:
            parts.append(val)
    tag_str = _join_tags(p.get("built_with_tags") or p.get("tags"))
    if tag_str:
        parts.append(tag_str)
    return "\n".join(parts).strip()


def _normalize_devpost(p: dict, source: str) -> dict:
    title = (p.get("title") or "").strip()
    description = (p.get("description") or "").strip()
    tagline = (p.get("tagline") or "").strip()
    built_with_tags = p.get("built_with_tags") or []
    if not isinstance(built_with_tags, list):
        built_with_tags = []

    url = p.get("url") or p.get("demo_url") or p.get("repo_url")
    started_date = p.get("started_date") or p.get("created_at") or p.get("pushed_at")

    normalized = {
        "id": str(url or title),
        "source": source,
        "url": url,
        "title": title,
        "tagline": tagline,
        "description": description,
        "started_date": started_date,
        "built_with_tags": built_with_tags,
        "hackathon_name": p.get("hackathon_name") or "",
        "repo_url": p.get("repo_url") or "",
        "demo_url": p.get("demo_url") or "",
        "winner": bool(p.get("winner")) if p.get("winner") is not None else False,
        "award_texts": p.get("award_texts") or [],
        "creators": p.get("creators") or [],
    }

    normalized["tags"] = built_with_tags
    normalized["created_at"] = started_date
    normalized["search_text"] = _make_search_text(normalized)
    normalized["text"] = normalized["search_text"]
    return normalized


def _normalize_legacy(p: dict) -> dict:
    title = (p.get("title") or "").strip()
    description = (p.get("description") or "").strip()
    tags = p.get("tags") or []
    if not isinstance(tags, list):
        tags = []

    normalized = {
        "id": str(p.get("id") or p.get("url") or title),
        "source": p.get("source") or "legacy",
        "url": p.get("url") or "",
        "title": title,
        "tagline": "",
        "description": description,
        "started_date": p.get("created_at") or p.get("pushed_at") or "",
        "built_with_tags": tags,
        "hackathon_name": "",
        "repo_url": p.get("repo_url") or "",
        "demo_url": p.get("demo_url") or "",
        "winner": bool(p.get("winner")) if p.get("winner") is not None else False,
        "award_texts": p.get("award_texts") or [],
        "creators": p.get("creators") or [],
    }

    normalized["tags"] = tags
    normalized["created_at"] = normalized["started_date"] or p.get("created_at")
    normalized["search_text"] = _make_search_text(normalized)
    normalized["text"] = normalized["search_text"]
    return normalized


def main():
    projects = []

    if JSONL_PROJECTS.exists():
        with JSONL_PROJECTS.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    projects.append(_normalize_legacy(raw))
                except Exception:
                    continue

    if JSONL_DEVPOST.exists():
        with JSONL_DEVPOST.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    if "scraped_at" in raw:
                        raw.pop("scraped_at", None)
                    projects.append(_normalize_devpost(raw, "devpost"))
                except Exception:
                    continue

    if not projects:
        raise RuntimeError("No projects loaded from projects.jsonl or devpost.jsonl")

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