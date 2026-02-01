import os, time, json, base64, re, random
from pathlib import Path
from datetime import date
import requests
from dotenv import load_dotenv
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError

load_dotenv()

OUT = Path("data/projects.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

STATE = Path("data/harvest_state.json")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "X-GitHub-Api-Version": "2022-11-28",
}

POS_README = [
    r"\bdevpost\b", r"\bmlh\b", r"\bbuilt for\b", r"\bsubmission\b", r"\bsubmitted\b",
    r"\bdemo\b", r"\bpitch\b", r"\bvideo\b", r"\bjudg(e|ing)\b", r"\bchallenge\b"
]
NEG_PLATFORM = [
    r"\bsponsors?\b", r"\bmentors?\b", r"\bregistration\b", r"\bagenda\b", r"\bschedule\b",
    r"\bcode of conduct\b", r"\btracks?\b", r"\bvenue\b", r"\battendee\b", r"\bvolunteer\b"
]
NEG_TEMPLATE = [r"\btemplate\b", r"\bboilerplate\b", r"\bstarter\b", r"\bscaffold\b"]
NEG_LIST = [r"\bawesome\b", r"\blist of\b", r"\bcurated\b", r"\bcollection\b"]

GENERIC_TITLE = {
    "hackathon", "hackathons", "hackathon-project", "hackathon project", "project"
}

# Throttling + scanning controls
MAX_PAGES_PER_QUERY = 2
SLEEP_BETWEEN_SEARCH_CALLS = 1.2
SLEEP_BETWEEN_READMES = 0.6

LOW_YIELD_MONTH_NEW_REPOS = 10
LOW_YIELD_MONTH_STREAK_STOP = 6

_BACKOFF = 0  # secondary rate-limit backoff


def load_state():
    """
    Resume scanning from last saved (year, month).
    If missing, start from a recent baseline (change if you want deeper history).
    """
    if not STATE.exists():
        return {"last_year": 2024, "last_month": 1}
    try:
        s = json.loads(STATE.read_text(encoding="utf-8"))
        return {"last_year": int(s.get("last_year", 2024)), "last_month": int(s.get("last_month", 1))}
    except Exception:
        return {"last_year": 2024, "last_month": 1}


def save_state(next_year: int, next_month: int):
    STATE.write_text(json.dumps({"last_year": next_year, "last_month": next_month}), encoding="utf-8")


def gh_get(url, params=None, *, timeout=45, max_retries=6):
    """
    GitHub GET with:
      - network retry (timeouts, connection reset)
      - primary rate limit (remaining==0 -> sleep to reset)
      - secondary rate limit (retry-after or exponential backoff)
      - 5xx retries
    """
    global _BACKOFF

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        except (ReadTimeout, ConnectTimeout, ConnectionError) as e:
            sleep_s = min(120, int(2 ** attempt)) + random.randint(0, 5)
            print(f"[net] {type(e).__name__} attempt {attempt}/{max_retries}; sleeping {sleep_s}s ...")
            time.sleep(sleep_s)
            continue

        if r.status_code in (403, 429):
            remaining = r.headers.get("X-RateLimit-Remaining")
            reset = r.headers.get("X-RateLimit-Reset")
            retry_after = r.headers.get("Retry-After")

            # Primary rate limit
            if remaining == "0" and reset:
                sleep_s = max(5, int(reset) - int(time.time()) + 2)
                print(f"[rate-limit] remaining=0; sleeping {sleep_s}s ...")
                time.sleep(sleep_s)
                _BACKOFF = 0
                continue

            # Secondary limit
            if retry_after:
                sleep_s = int(retry_after) + random.randint(0, 3)
                print(f"[secondary-limit] retry-after={retry_after}; sleeping {sleep_s}s ...")
                time.sleep(sleep_s)
                _BACKOFF = min(120, max(_BACKOFF, 15))
                continue

            _BACKOFF = 15 if _BACKOFF == 0 else min(120, int(_BACKOFF * 1.8))
            sleep_s = _BACKOFF + random.randint(0, 6)
            print(f"[secondary-limit] sleeping {sleep_s}s (backoff={_BACKOFF}) ...")
            time.sleep(sleep_s)
            continue

        # Retry transient server errors
        if 500 <= r.status_code < 600:
            sleep_s = min(120, int(2 ** attempt)) + random.randint(0, 5)
            print(f"[server] {r.status_code} attempt {attempt}/{max_retries}; sleeping {sleep_s}s ...")
            time.sleep(sleep_s)
            continue

        r.raise_for_status()
        _BACKOFF = 0
        return r.json(), r.headers

    raise RuntimeError(f"Failed to fetch {url} after {max_retries} retries")


def search_repos(query, page=1, per_page=100):
    url = "https://api.github.com/search/repositories"
    data, _ = gh_get(
        url,
        params={"q": query, "sort": "updated", "order": "desc", "page": page, "per_page": per_page},
        timeout=60,
    )
    return data.get("items", [])


def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    try:
        data, _ = gh_get(url, timeout=45)
        content = data.get("content", "")
        if content:
            return base64.b64decode(content).decode("utf-8", errors="ignore")
    except Exception:
        return ""
    return ""


def clean_markdown(md: str) -> str:
    """Remove README boilerplate that hurts embedding quality."""
    if not md:
        return ""
    md = re.sub(r"```.*?```", " ", md, flags=re.S)            # fenced code blocks
    md = re.sub(r"`[^`]+`", " ", md)                          # inline code
# Remove images: ![alt](url)
    md = re.sub(r"!\[[^\]]*\]\([^\)]*\)", " ", md)

# Replace links: [text](url) -> text
    md = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", md)
    md = re.sub(r"<[^>]+>", " ", md)                          # html tags
    md = re.sub(r"^#{1,6}\s*", "", md, flags=re.M)            # headings
    md = re.sub(r"^\s*[-*>]\s+", "", md, flags=re.M)          # bullets/quotes
    md = re.sub(r"\s+", " ", md).strip()
    return md


def build_search_text(title: str, desc: str, topics: list[str]) -> str:
    topics = topics or []
    tag_str = " ".join([t for t in topics if isinstance(t, str)])
    parts = [f"Title: {title.strip()}"]
    if desc:
        parts.append(f"Description: {desc.strip()}")
    if tag_str:
        parts.append(f"Tags: {tag_str}")
    return "\n".join(parts).strip()


def build_explain_text(title: str, desc: str, topics: list[str], readme_clean: str) -> str:
    readme_clean = (readme_clean or "")[:3500]
    parts = [
        f"Title: {title}",
        f"Description: {desc}" if desc else "",
        f"Tags: {' '.join(topics)}" if topics else "",
        f"README: {readme_clean}" if readme_clean else "",
    ]
    return "\n".join([p for p in parts if p]).strip()


def score_and_type(title: str, desc: str, readme_clean: str, topics: list[str]) -> tuple[float, str]:
    t = (title or "").lower().strip()
    d = (desc or "").lower().strip()
    r = (readme_clean or "").lower()
    tags = " ".join([str(x).lower() for x in (topics or [])])
    text = " ".join([t, d, r, tags])

    score = 0.0

    for pat in POS_README:
        if re.search(pat, text):
            score += 1.0

    if any(k in text for k in ["frontend", "backend", "react", "fastapi", "flask", "django", "nextjs", "api", "mobile", "ios", "android"]):
        score += 0.5
    if any(k in text for k in ["features", "how it works", "architecture", "pipeline"]):
        score += 0.5

    platform_hits = sum(1 for pat in NEG_PLATFORM if re.search(pat, text))
    template_hits = sum(1 for pat in NEG_TEMPLATE if re.search(pat, text))
    list_hits = sum(1 for pat in NEG_LIST if re.search(pat, text))

    if t in GENERIC_TITLE:
        score -= 1.5

    score -= 0.6 * platform_hits
    score -= 0.8 * template_hits
    score -= 0.8 * list_hits

    if template_hits >= 1 or "template" in t:
        typ = "template"
    elif list_hits >= 1:
        typ = "list"
    elif platform_hits >= 2 or any(k in text for k in ["registration", "sponsors", "code of conduct", "attendee"]):
        typ = "platform"
    else:
        typ = "project"

    score = max(0.0, min(10.0, score + 2.0))
    return score, typ


def month_range(start_year: int, start_month: int, end_year: int, end_month: int):
    import calendar
    y, m = start_year, start_month
    while (y < end_year) or (y == end_year and m <= end_month):
        last_day = calendar.monthrange(y, m)[1]
        yield (y, m, date(y, m, 1).isoformat(), date(y, m, last_day).isoformat())
        m += 1
        if m == 13:
            m = 1
            y += 1


def load_seen_ids():
    seen = set()
    if not OUT.exists():
        return seen
    with OUT.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rid = obj.get("id")
                if rid:
                    seen.add(rid)
            except Exception:
                continue
    return seen


def main(
    target_new: int = 15000,
    end_year: int = 2026,
    end_month: int = 1,
    stars_min: int = 0,
    readme_stars_min: int = 10,
):
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN not set. You will hit rate limits quickly.")

    base_queries = [
        f"topic:hackathon stars:>={stars_min}",
        f"topic:hackathon-project stars:>={stars_min}",
        f"topic:mlh-hackathon stars:>={stars_min}",
        f'hackathon "built for" in:readme stars:>={stars_min}',
        f"devpost in:readme stars:>={stars_min}",
    ]

    state = load_state()
    start_year = int(state.get("last_year", 2024))
    start_month = int(state.get("last_month", 1))

    seen_ids = load_seen_ids()
    print(f"Existing records: {len(seen_ids)}")
    print(f"[state] starting from {start_year}-{start_month:02d} through {end_year}-{end_month:02d}")

    new_count = 0
    low_yield_streak = 0

    with OUT.open("a", encoding="utf-8") as out:
        for (y, m, d1, d2) in month_range(start_year, start_month, end_year, end_month):
            month_new = 0

            for base in base_queries:
                q = f"{base} created:{d1}..{d2}"
                page = 1

                while new_count < target_new and page <= MAX_PAGES_PER_QUERY:
                    items = search_repos(q, page=page, per_page=100)
                    time.sleep(SLEEP_BETWEEN_SEARCH_CALLS)

                    if not items:
                        break

                    for it in items:
                        full = it["full_name"]
                        rid = f"github:{full}"

                        if rid in seen_ids:
                            continue
                        if it.get("fork") or it.get("archived"):
                            continue

                        owner, repo = full.split("/", 1)
                        topics = it.get("topics") or []
                        stars = it.get("stargazers_count", 0)
                        lang = it.get("language")

                        title = it.get("name", "") or ""
                        desc = it.get("description") or ""

                        # Pre-score without README to decide whether to fetch it
                        pre_score, pre_type = score_and_type(title, desc, "", topics)

                        readme = ""
                        if stars >= readme_stars_min and pre_type == "project" and pre_score >= 1.0:
                            readme = get_readme(owner, repo)
                            time.sleep(SLEEP_BETWEEN_READMES)

                        readme_clean = clean_markdown(readme)
                        submission_score, type_label = score_and_type(title, desc, readme_clean, topics)

                        search_text = build_search_text(title, desc, topics)
                        explain_text = build_explain_text(title, desc, topics, readme_clean)

                        if len(search_text) < 60:
                            continue

                        rec = {
                            "id": rid,
                            "source": "github",
                            "title": title,
                            "description": desc,
                            "tags": topics,
                            "url": it.get("html_url"),
                            "created_at": it.get("created_at"),
                            "pushed_at": it.get("pushed_at"),
                            "stars": stars,
                            "language": lang,
                            "submission_score": submission_score,
                            "type_label": type_label,
                            "search_text": search_text,
                            "text": explain_text,
                            "explain_text": explain_text,
                        }

                        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        seen_ids.add(rid)
                        new_count += 1
                        month_new += 1

                        if new_count % 200 == 0:
                            print(f"[progress] added {new_count} new repos (total now {len(seen_ids)})")

                        if new_count >= target_new:
                            break

                    page += 1

                if new_count >= target_new:
                    break

            # Save progress AFTER finishing a month: next run starts at next month
            ny, nm = y, m + 1
            if nm == 13:
                nm = 1
                ny += 1
            save_state(ny, nm)

            print(f"[month] {y}-{m:02d}: added {month_new} repos (total new={new_count})")

            # Low-yield streak is only meaningful in recent years
            if month_new <= LOW_YIELD_MONTH_NEW_REPOS:
                low_yield_streak += 1
            else:
                low_yield_streak = 0

            if y >= 2024 and low_yield_streak >= LOW_YIELD_MONTH_STREAK_STOP:
                print(f"[stop] low-yield streak={low_yield_streak} in {y}. Stopping early to save rate limit.")
                break

            if new_count >= target_new:
                break

    print(f"Added {new_count} new repos. Total records now: {len(seen_ids)}")
    print(f"Output: {OUT}")
    print(f"State: {STATE}")


if __name__ == "__main__":
    main()