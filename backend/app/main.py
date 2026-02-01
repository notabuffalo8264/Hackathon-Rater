from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .models import CheckRequest, CheckResponse, Neighbor
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


@app.post("/check", response_model=CheckResponse)
def check(req: CheckRequest):
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