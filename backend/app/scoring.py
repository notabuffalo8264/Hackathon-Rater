from typing import List, Optional

def originality_score(similarities: List[float], *, specificity: Optional[float] = None) -> int:
    """Convert fused neighbor similarity scores (0..1) into 0..100 originality.

    Notes:
    - similarity should represent "same idea" closeness, not just topical semantics.
    - specificity (avg IDF of query terms) nudges scores downward for very generic prompts,
      because generic ideas tend to be common and also produce noisier similarity signals.
    """
    sims = [float(s) for s in similarities if s is not None and s == s]  # drop NaN
    if not sims:
        return 85

    sims = sorted(sims, reverse=True)
    top1 = sims[0]
    topk = sims[: min(7, len(sims))]
    avgk = sum(topk) / len(topk)

    # emphasize closest neighbor but keep robustness to one-off false positives
    s = 0.75 * top1 + 0.25 * avgk

    # main curve: a bit steeper near high similarity (penalize near-duplicates)
    score = 100 * (1.0 - s) ** 1.9

    # density penalty only if MANY are *very* close (multiple near-duplicates)
    close = sum(1 for x in topk if x >= 0.78)
    score -= 5 * max(0, close - 1)

    # generic-query penalty (optional)
    if specificity is not None:
        # Typical avg IDF in this corpus will vary; this gives a penalty
        # when the query is mostly common words.
        # specificity ~1.0 => very generic, ~2.0+ => reasonably specific.
        gen = max(0.0, min(1.0, (1.7 - float(specificity)) / 0.9))
        score -= 12.0 * gen

        # Specificity boost: reward detailed queries
        boost = max(0.0, min(20.0, (float(specificity) - 1.3) * 9.0))
        score += boost

        if float(specificity) >= 2.0:
            score += 8.0

        # Extra clamp for extremely generic or very short queries
        if float(specificity) < 0.5:
            score = min(score, 28)

    # clamp
    score = max(2, min(100, round(score)))
    return int(score)

def label_for_score(score: int) -> str:
    if score >= 82:
        return "Unique"
    if score >= 62:
        return "Distinct"
    if score >= 38:
        return "Crowded"
    return "Common"