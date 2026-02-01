import json
from pathlib import Path

OUT = Path("data/projects.jsonl")

def make_text(title: str, description: str, tags):
    return f"Title: {title}\nDescription: {description}\nTags: {' '.join(tags)}".strip()

def main():
    projects = [
        {
            "id": "demo:1",
            "source": "demo",
            "title": "Receipt Carbon Estimator",
            "description": "Estimate carbon impact from grocery receipts and suggest alternatives.",
            "tags": ["sustainability", "nlp"],
            "url": None,
            "created_at": None,
        },
        {
            "id": "demo:2",
            "source": "demo",
            "title": "Shift Handoff Summarizer",
            "description": "Summarize shift handoffs for nurses with structured action items.",
            "tags": ["healthcare", "summarization"],
            "url": None,
            "created_at": None,
        },
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for p in projects:
            p["text"] = make_text(p["title"], p["description"], p["tags"])
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()