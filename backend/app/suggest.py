import math
import re
from collections import Counter
from typing import List, Tuple


STOP = {
    "the","a","an","and","or","to","of","in","for","with","on","at","by","from","as",
    "is","are","was","were","be","been","it","this","that","these","those","your","our",

    # question words
    "how","why","what","when","where","who","whom","which",

    # generic boilerplate
    "app","project","projects","repo","repository","code","using","use","uses","used",
    "build","built","create","creating","platform","website","web","api","service",
    "system","powered","tool","tools",

    # hackathon boilerplate
    "hackathon","demo","prototype",

    # schema/meta leakage
    "title","description","tags","tag","idea","ideas","originality","original","check","checker",
    "done","score","scoring","recent","alltime","all-time","all",
}

def tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    toks = re.findall(r"[a-z0-9]{3,}", s)
    return [t for t in toks if t not in STOP]


def top_terms(texts: List[str], k: int = 10) -> List[Tuple[str, int]]:
    c = Counter()
    for t in texts:
        c.update(tokenize(t))
    return c.most_common(k)


def _idf_from_texts(texts: List[str]) -> dict[str, float]:
    df = Counter()
    n = 0
    for t in texts:
        terms = set(tokenize(t))
        if not terms:
            continue
        n += 1
        df.update(terms)

    n = max(1, n)
    return {term: (math.log((n + 1) / (dfv + 1)) + 1.0) for term, dfv in df.items()}


def overlap_terms(query_text: str, neighbor_texts: List[str], k: int = 8) -> List[str]:
    q = set(tokenize(query_text))
    if not q or not neighbor_texts:
        return []

    idf = _idf_from_texts(neighbor_texts)

    neigh_terms = set()
    for t in neighbor_texts:
        neigh_terms.update(tokenize(t))

    inter = [term for term in q if term in neigh_terms]
    if not inter:
        return []

    # Require terms to be at least moderately informative in this local neighborhood.
    # If everything is generic, do not pretend we found "constraints".
    MIN_IDF = 1.35
    inter = [t for t in inter if idf.get(t, 1.0) >= MIN_IDF]
    if not inter:
        return []

    inter.sort(key=lambda term: (-(idf.get(term, 1.0)), term))
    return inter[:k]


def make_suggestions(query_text: str, neighbor_texts: List[str]) -> List[str]:
    ov = overlap_terms(query_text, neighbor_texts, k=8)
    neigh_top = [t for t, _ in top_terms(neighbor_texts, k=8)]

    suggestions: List[str] = []

    if ov:
        suggestions.append(f"**Why it looks similar:** overlaps on *specific* terms like {', '.join(ov[:6])}.")
    elif neigh_top:
        suggestions.append(
            "**Why it looks similar:** your description is still fairly general, so it clusters with "
            f"neighbors that commonly mention {', '.join(neigh_top[:6])}."
        )
    else:
        suggestions.append("**Why it looks similar:** not many strong shared constraints (good sign).")

    suggestions.append("**3 concrete ways to make it stand out:**")
    suggestions.append(
        "1) **Add a unique constraint**: specify a hard requirement competitors likely won’t match "
        "(offline-first, no accounts, runs in-browser, <$1/month compute, on-device only, or strict privacy)."
    )
    suggestions.append(
        "2) **Pick a narrow target workflow**: one user group + one moment in their day "
        "(e.g., nursing clinicals, IEP coordinators, ESL homework review, AP/IB planning, or dyslexia-friendly reading)."
    )
    suggestions.append(
        "3) **Define a measurable proof loop**: add a metric + feedback cycle "
        "(A/B comparison, weekly improvement curve, teacher/coach review, or “show your work” explanation)."
    )

    suggestions.append(
        "**Quick uniqueness twists:** personal data stays local; explainable scoring; works from exported files; "
        "supports accessibility settings; reproducible eval set; “why this match” transparency."
    )
    return suggestions