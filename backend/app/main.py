from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .models import CheckRequest, CheckResponse, Neighbor, ScoreResponse
from .store import ProjectStore
from .scoring import originality_score, label_for_score
from .suggest import make_suggestions

app = FastAPI(title="Hackathon Originality Checker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store: ProjectStore | None = None
last_response: CheckResponse | None = None


def trend_label(score_all: int, score_recent: int):
    if score_all >= 60 and score_recent <= 40:
        return ("Novel historically, crowded recently",
                "Ideas like this were rarer historically, but have become common recently.")
    if score_all <= 40 and score_recent <= 40:
        return ("Crowded historically and now",
                "This space is heavily explored both historically and recently.")
    if score_all >= 60 and score_recent >= 60:
        return ("Still unusual",
                "Even in recent projects, this appears relatively uncommon.")
    if score_all <= 40 and score_recent >= 60:
        return ("Was common, now differentiating",
                "Historically common, but recent projects show less saturation.")
    return ("Mixed saturation",
            "Some overlap exists; adding a sharper niche/constraint can increase novelty.")


def is_good_neighbor(p) -> bool:
    tl = (p.type_label or "").lower()
    if tl in {"template", "list", "platform"}:
        return False

    t = (p.title or "").strip().lower()
    d = (p.description or "").strip().lower()

    # hard filter: generic starter/boilerplate collections
    bad_title_substrings = [
        "starter", "boilerplate", "template", "blueprint", "misc", "resources",
        "examples", "sample", "skeleton", "kickstart"
    ]
    if any(x in t for x in bad_title_substrings):
        return False

    generic_titles = {
        "hackathon", "hackathons", "hackathon project", "hackathon-project",
        "project", "projects", "1st-hackathon",
    }
    if t in generic_titles:
        return False

    # descriptions that say nothing
    if len(d) < 60 and ("hackathon" in d or "repository" in d or "project" in d):
        return False

    return True


def build_neighbors(sims, idxs, k_keep: int, qtext: str):
    assert store is not None
    candidates = []
    texts = []

    for emb_sim, idx in zip(sims, idxs):
        if idx is None or idx < 0:
            continue
        if emb_sim != emb_sim:  # NaN
            continue

        p = store.projects[int(idx)]
        if not p:
            continue

        overlap = store.weighted_overlap(qtext, p.text)
        fused = store.combined_similarity(float(emb_sim), overlap)

        candidates.append((fused, float(emb_sim), float(overlap), p))

    candidates.sort(key=lambda x: x[0], reverse=True)

    neighbors = []
    for fused, emb_sim, overlap, p in candidates:
        if not is_good_neighbor(p):
            continue

        neighbors.append(Neighbor(
            id=p.id,
            title=p.title,
            snippet=(p.description[:180] + ("..." if len(p.description) > 180 else "")),
            url=p.url,
            tagline=p.tagline,
            description=p.description,
            started_date=p.started_date or p.created_at,
            built_with_tags=p.built_with_tags or p.tags,
            hackathon_name=p.hackathon_name,
            repo_url=p.repo_url,
            demo_url=p.demo_url,
            winner=p.winner,
            award_texts=p.award_texts,
            creators=p.creators,
            similarity=float(fused),
            semantic_similarity=float(emb_sim),
            rare_overlap=float(overlap),
        ))
        texts.append(p.text)

        if len(neighbors) >= k_keep:
            break

    return neighbors, texts


@app.on_event("startup")
def _startup():
    global store
    store = ProjectStore(
        index_all_path=settings.index_all_path,
        index_recent_path=settings.index_recent_path,
        recent_row_ids_path=settings.recent_row_ids_path,
        meta_path=settings.meta_path,
        embed_model_name=settings.embed_model_name,
        local_model_only=False,
    )


@app.get("/health")
def health():
    return {"ok": True}


def _compute_check(req: CheckRequest) -> CheckResponse:
    assert store is not None

    k = req.k or settings.top_k_default
    k_search = max(120, int(k) * 30)  # widen more; filters remove junk

    qvec = store.embed_query(req.title, req.description, req.tags)

    sims_all, idxs_all = store.search_all(qvec, k_search)
    sims_recent, idxs_recent = store.search_recent(qvec, k_search)

    qtext = store.query_text(req.title, req.description, req.tags)
    specificity = store.query_specificity(qtext)

    neighbors_all, texts_all = build_neighbors(sims_all, idxs_all, k, qtext)
    neighbors_recent, texts_recent = build_neighbors(sims_recent, idxs_recent, k, qtext)

    score_all = originality_score([n.similarity for n in neighbors_all], specificity=specificity)
    score_recent = originality_score([n.similarity for n in neighbors_recent], specificity=specificity)

    label_all = label_for_score(score_all)
    label_recent = label_for_score(score_recent)

    tlabel, tnote = trend_label(score_all, score_recent)

    suggestions = make_suggestions(
        query_text=qtext,
        neighbor_texts=[*texts_recent, *texts_all],
    )

    return CheckResponse(
        score_all=score_all,
        score_recent=score_recent,
        label_all=label_all,
        label_recent=label_recent,
        trend_label=tlabel,
        trend_note=tnote,
        neighbors_all=neighbors_all,
        neighbors_recent=neighbors_recent,
        suggestions=suggestions,
    )


def _parse_tags(tags: Optional[str]) -> Optional[List[str]]:
    if not tags:
        return None
    parsed = [t.strip() for t in tags.split(",") if t.strip()]
    return parsed or None


@app.post("/check", response_model=CheckResponse)
def check(req: CheckRequest):
    global last_response
    last_response = _compute_check(req)
    return last_response


@app.get("/score", response_model=ScoreResponse)
def score(
    title: Optional[str] = None,
    description: str = "",
    tags: Optional[str] = None,
    k: Optional[int] = None,
):
    global last_response
    if title:
        last_response = _compute_check(
            CheckRequest(
                title=title,
                description=description,
                tags=_parse_tags(tags),
                k=k or settings.top_k_default,
            )
        )
    if last_response is None:
        return ScoreResponse(
            score_all=0,
            score_recent=0,
            label_all="",
            label_recent="",
            trend_label="",
            trend_note="",
        )
    return ScoreResponse(
        score_all=last_response.score_all,
        score_recent=last_response.score_recent,
        label_all=last_response.label_all,
        label_recent=last_response.label_recent,
        trend_label=last_response.trend_label,
        trend_note=last_response.trend_note,
    )


@app.get("/projects", response_model=List[Neighbor])
def projects(
    title: Optional[str] = None,
    description: str = "",
    tags: Optional[str] = None,
    k: Optional[int] = None,
):
    global last_response
    if title:
        last_response = _compute_check(
            CheckRequest(
                title=title,
                description=description,
                tags=_parse_tags(tags),
                k=k or settings.top_k_default,
            )
        )
    if last_response is None:
        return []
    return last_response.neighbors_recent or last_response.neighbors_all


@app.get("/suggestions", response_model=List[str])
def suggestions(
    title: Optional[str] = None,
    description: str = "",
    tags: Optional[str] = None,
    k: Optional[int] = None,
):
    global last_response
    if title:
        last_response = _compute_check(
            CheckRequest(
                title=title,
                description=description,
                tags=_parse_tags(tags),
                k=k or settings.top_k_default,
            )
        )
    if last_response is None:
        return []
    return last_response.suggestions