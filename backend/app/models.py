from typing import List, Optional
from pydantic import BaseModel, Field


class CheckRequest(BaseModel):
    title: str
    description: str = ""
    tags: Optional[List[str]] = None
    k: int = 5


class Neighbor(BaseModel):
    id: str
    title: str
    snippet: str
    url: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    started_date: Optional[str] = None
    built_with_tags: Optional[List[str]] = None
    hackathon_name: Optional[str] = None
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None
    winner: Optional[bool] = None
    award_texts: Optional[List[str]] = None
    creators: Optional[List[dict]] = None
    similarity: float  # fused "same-idea" similarity
    semantic_similarity: Optional[float] = None
    rare_overlap: Optional[float] = None


class CheckResponse(BaseModel):
    score_all: int
    score_recent: int
    label_all: str
    label_recent: str
    trend_label: str
    trend_note: str
    neighbors_all: List[Neighbor] = Field(default_factory=list)
    neighbors_recent: List[Neighbor] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ScoreResponse(BaseModel):
    score_all: int
    score_recent: int
    label_all: str
    label_recent: str
    trend_label: str
    trend_note: str