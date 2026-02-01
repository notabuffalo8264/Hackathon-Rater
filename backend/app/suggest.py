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

    # common verbs/nouns that read poorly in suggestions
    "estimate","estimator","detect","detection","suggest","suggestions","alternative","alternatives",
    "notes","note","action","actions","mechanic","mechanics",
}

def tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    toks = re.findall(r"[a-z][a-z0-9]{2,}", s)
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


def _best_term(query_text: str, neighbor_texts: List[str]) -> str:
    tokens = tokenize(query_text)
    if not tokens:
        return "idea"

    idf = _idf_from_texts(neighbor_texts) if neighbor_texts else {}
    ranked = sorted(tokens, key=lambda t: (-(idf.get(t, 1.0)), -len(t), t))
    return ranked[0] if ranked else tokens[0]


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


def _seed_from_text(text: str) -> int:
    if not text:
        return 0
    return sum(ord(c) for c in text) % 10_000


def _pick(items: List[str], seed: int, offset: int = 0) -> str:
    if not items:
        return ""
    return items[(seed + offset) % len(items)]


def _detect_domain(tokens: List[str]) -> str:
    domain_map = {
        "health": {"health", "clinic", "nurse", "patient", "medical", "hospital", "diagnosis"},
        "sports": {"sport", "athlete", "coach", "football", "basketball", "soccer", "training"},
        "education": {"school", "student", "teacher", "class", "study", "learning", "curriculum"},
        "finance": {"finance", "budget", "billing", "invoice", "payment", "bank"},
        "sustainability": {"carbon", "climate", "energy", "sustainability", "emissions"},
        "security": {"security", "fraud", "auth", "privacy", "risk"},
        "accessibility": {"accessibility", "assistive", "disability", "screenreader"},
    }
    token_set = set(tokens)
    for domain, keywords in domain_map.items():
        if token_set & keywords:
            return domain
    return "general"


def make_suggestions(query_text: str, neighbor_texts: List[str], score: int | None = None) -> List[str]:
    ov = overlap_terms(query_text, neighbor_texts, k=8)
    neigh_top = [t for t, _ in top_terms(neighbor_texts, k=8)]
    tokens = tokenize(query_text)
    domain = _detect_domain(tokens)
    seed = _seed_from_text(query_text)

    overlap_phrase = ", ".join(ov[:6]) if ov else ""
    key_term = _best_term(query_text, neighbor_texts)
    if key_term in {"idea", "this"} and tokens:
        key_term = tokens[0]

    suggestions: List[str] = []

    # Length-based guidance
    if len(tokens) <= 1:
        suggestions.append(
            "Add 1–2 sentences describing the user, the problem, and the expected outcome."
        )
    elif len(tokens) <= 5:
        suggestions.append(
            "Include a target user and the exact decision or task they’re doing."
        )

    # Rating-based guidance
    if score is not None:
        if score >= 80:
            suggestions.append(
                "This is already quite original. Focus on a crisp demo and a measurable win."
            )
        elif score >= 60:
            suggestions.append(
                "You’re differentiated—tighten the niche to stand out even more."
            )
        elif score >= 40:
            suggestions.append(
                "This is somewhat crowded. Pick a narrower workflow or constraint."
            )
        else:
            suggestions.append(
                "This space is very crowded. Consider a sharper niche or a new angle."
            )

    if ov:
        suggestions.append(
            f"You overlap with existing projects on {overlap_phrase}. Consider shifting one of those terms to a more specific constraint."
        )
    elif len(tokens) <= 2:
        suggestions.append(
            "Your description is very broad. Add a specific user, moment, and measurable outcome to stand out."
        )
    elif neigh_top:
        suggestions.append(
            "Your description is broad; similar projects often mention "
            f"{', '.join(neigh_top[:5])}. Narrow the focus to one concrete workflow."
        )
    else:
        suggestions.append(
            "Your idea has fewer shared constraints, which is promising—add a crisp niche to reinforce it."
        )

    constraint_templates = [
        "Add a hard constraint: offline-first, on-device only, or no accounts for {term}.",
        "Choose a strict environment (low-connectivity, classroom, or field use) for {term}.",
    ]

    workflow_templates = [
        "Specify the exact user moment for {term}: who uses it, when, and for what decision?",
        "Pick one role in {domain} and a single step they repeat daily; design for that.",
        "Clarify the trigger for {term} (new event, deadline, or alert) and the next action.",
    ]

    proof_templates = [
        "Define a measurable outcome: time saved, accuracy gain, or error reduction for {term}.",
        "Add a feedback loop: how will {term} improve week over week?",
    ]

    data_templates = [
        "Name the key data source for {term} (sensor, logs, forms, or APIs).",
        "Explain the signal you rely on for {term} and how you’ll collect it.",
    ]

    beta_suggestions = [
        _pick(constraint_templates, seed).format(term=key_term),
        _pick(workflow_templates, seed, 1).format(term=key_term, domain=domain),
        _pick(proof_templates, seed, 2).format(term=key_term),
        _pick(data_templates, seed, 3).format(term=key_term),
    ]

    suggestions.extend([f"[BETA] {s}" for s in beta_suggestions])

    return suggestions