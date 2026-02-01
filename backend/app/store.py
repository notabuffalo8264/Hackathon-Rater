import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class Project:
    id: str
    title: str
    description: str
    tags: List[str]
    url: Optional[str]
    created_at: Optional[str]

    search_text: str
    text: str

    source: str = "unknown"
    pushed_at: Optional[str] = None
    stars: Optional[int] = None
    language: Optional[str] = None
    submission_score: Optional[float] = None
    type_label: Optional[str] = None


# Stopwords tuned to remove schema/meta/UI words and generic hackathon boilerplate.
_STOP = {
    # function words
    "the","a","an","and","or","to","of","in","for","with","on","at","by","from","as",
    "is","are","was","were","be","been","it","this","that","these","those","your","our",

    # question words (these should NEVER drive "constraints")
    "how","why","what","when","where","who","whom","which",

    # generic software boilerplate
    "app","project","projects","repo","repository","code","using","use","uses","used",
    "build","built","create","creating","platform","website","web","api","service",
    "system","powered","tool","tools",

    # hackathon boilerplate
    "hackathon","demo","prototype",

    # form/schema leakage (your exact bug)
    "title","description","tags","tag","idea","ideas","originality","original",
    "check","checker","done","score","scoring","recent","alltime","all-time","all",
}

# Lines we want to strip if the frontend accidentally includes UI labels or button text
_UI_LINE_RE = re.compile(
    r"^\s*(title|description|tags|check originality|done)\s*$",
    re.IGNORECASE
)

def _sanitize_user_text(s: str) -> str:
    """Remove common UI/label lines and collapse whitespace."""
    if not s:
        return ""
    lines = []
    for line in s.splitlines():
        if _UI_LINE_RE.match(line.strip()):
            continue
        lines.append(line)
    out = "\n".join(lines).strip()
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    toks = re.findall(r"[a-z0-9]{3,}", s)
    return [t for t in toks if t not in _STOP]


def _make_search_text(p: dict) -> str:
    title = (p.get("title") or "").strip()
    desc = (p.get("description") or "").strip()
    tags = p.get("tags") or []
    tag_str = " ".join([t for t in tags if isinstance(t, str)])

    parts = []
    if title:
        parts.append(title)
    if desc:
        parts.append(desc)
    if tag_str:
        parts.append(tag_str)
    return "\n".join(parts).strip()


def _safe_unit(vecs: np.ndarray) -> np.ndarray:
    vecs = np.nan_to_num(vecs, nan=0.0, posinf=0.0, neginf=0.0).astype("float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return vecs / norms


class ProjectStore:
    def __init__(
        self,
        index_all_path: str,
        index_recent_path: str,
        recent_row_ids_path: str,
        meta_path: str,
        embed_model_name: str,
        local_model_only: bool = False,
    ):
        self.index_all = faiss.read_index(index_all_path)
        self.index_recent = faiss.read_index(index_recent_path)

        with open(meta_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        with open(recent_row_ids_path, "r", encoding="utf-8") as f:
            self.recent_row_ids = json.load(f)

        self.total_projects = len(raw)
        self.recent_projects = len(self.recent_row_ids)
        self.embed_model_name = embed_model_name

        allowed = set(Project.__dataclass_fields__.keys())

        normalized = []
        for p in raw:
            p = dict(p)
            if not p.get("search_text"):
                p["search_text"] = _make_search_text(p)
            if not p.get("text"):
                p["text"] = p["search_text"]
            if not isinstance(p.get("tags"), list):
                p["tags"] = []
            normalized.append(p)

        self.projects: List[Project] = [
            Project(**{k: v for k, v in p.items() if k in allowed})
            for p in normalized
        ]

        if self.index_all.ntotal != len(self.projects):
            raise RuntimeError("index_all size mismatch with metadata (rebuild indices)")

        # Corpus-wide DF/IDF so overlap scoring emphasizes rare shared constraints.
        self._df = Counter()
        for p in self.projects:
            self._df.update(set(_tokenize(p.search_text)))
        n_docs = max(1, len(self.projects))
        self._idf = {t: (math.log((n_docs + 1) / (df + 1)) + 1.0) for t, df in self._df.items()}
        self._n_docs = n_docs

        self.model = SentenceTransformer(
            embed_model_name,
            local_files_only=local_model_only,
        )

    def query_text(self, title: str, description: str, tags: Optional[List[str]] = None) -> str:
        """Clean query text WITHOUT schema labels or UI button text."""
        tags = tags or []
        t = _sanitize_user_text(title or "")
        d = _sanitize_user_text(description or "")

        parts = []
        if t:
            parts.append(t)
        if d:
            parts.append(d)
        if tags:
            parts.append(" ".join([_sanitize_user_text(x) for x in tags if isinstance(x, str)]))
        return "\n".join([p for p in parts if p]).strip()

    def embed_query(self, title: str, description: str, tags: Optional[List[str]] = None) -> np.ndarray:
        q = self.query_text(title, description, tags)
        vec = self.model.encode([q]).astype("float32")
        return _safe_unit(vec)

    def search_all(self, qvec: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        sims, idxs = self.index_all.search(qvec, k)
        sims = np.nan_to_num(sims, nan=-1.0, posinf=-1.0, neginf=-1.0)
        return sims[0].tolist(), idxs[0].tolist()

    def search_recent(self, qvec: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        sims, idxs = self.index_recent.search(qvec, k)
        sims = np.nan_to_num(sims, nan=-1.0, posinf=-1.0, neginf=-1.0)

        out_sims: List[float] = []
        out_global: List[int] = []

        for sim, local_idx in zip(sims[0].tolist(), idxs[0].tolist()):
            if local_idx is None or local_idx < 0:
                continue
            global_idx = self.recent_row_ids[local_idx]
            out_sims.append(float(sim))
            out_global.append(int(global_idx))

        return out_sims, out_global

    def query_specificity(self, qtext: str) -> float:
        terms = set(_tokenize(qtext))
        if not terms:
            return 0.0
        vals = [self._idf.get(t, 1.0) for t in terms]
        return float(sum(vals) / len(vals))

    def weighted_overlap(self, qtext: str, doc_text: str) -> float:
        q_terms = set(_tokenize(qtext))
        if not q_terms:
            return 0.0
        d_terms = set(_tokenize(doc_text))
        inter = q_terms & d_terms
        if not inter:
            return 0.0
        num = sum(self._idf.get(t, 1.0) for t in inter)
        den = sum(self._idf.get(t, 1.0) for t in q_terms)
        return float(num / den) if den > 0 else 0.0

    def combined_similarity(self, emb_sim: float, overlap: float) -> float:
        """Fuse semantic similarity with constraint overlap.

        Hard requirement: if overlap is extremely small, do NOT let embeddings claim "same idea".
        """
        emb_sim = float(emb_sim)
        overlap = float(overlap)

        o = max(0.0, min(1.0, overlap)) ** 0.7

        # If constraints barely overlap, this is *not* the same idea (topical at best).
        if o < 0.08:
            # cap aggressively: keep it low even if embeddings are high
            return float(max(0.0, min(0.22, 0.22 * max(0.0, emb_sim))))

        if o < 0.18:
            w_emb = 0.30
        elif o < 0.30:
            w_emb = 0.45
        else:
            w_emb = 0.60

        s = w_emb * max(0.0, emb_sim) + (1.0 - w_emb) * o
        return float(max(0.0, min(1.0, s)))