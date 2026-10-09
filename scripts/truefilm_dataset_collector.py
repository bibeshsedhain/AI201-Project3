#!/usr/bin/env python3
"""
Build a balanced 225-row r/TrueFilm TakeMeter dataset using the Arctic Shift API.

Outputs:
- labeled_data.csv          -> 225 balanced rows (75/75/75)
- review_queue.csv          -> ambiguous / low-confidence rows to review
- candidate_pool.csv        -> all usable collected candidates
- dataset_summary.txt       -> counts and validation notes

Labels:
- analysis
- opinion
- discussion_question

No Reddit or Arctic Shift API key is required.
"""

import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://arctic-shift.photon-reddit.com/api"
SUBREDDIT = "TrueFilm"

# Smaller date windows make Arctic Shift requests more reliable.
WINDOWS = [
    ("2025-01-01", "2025-04-01"),
    ("2025-04-01", "2025-07-01"),
    ("2025-07-01", "2025-10-01"),
    ("2025-10-01", "2026-01-01"),
    ("2026-01-01", "2026-04-01"),
    ("2026-04-01", "2026-07-01"),
    ("2026-07-01", "2026-10-08"),
]

TARGET_PER_LABEL = 75
TARGET_TOTAL = TARGET_PER_LABEL * 3

MIN_CHARS = 45
MAX_CHARS = 3500

USER_AGENT = "TakeMeter-AI201/1.0"
LABELS = ["analysis", "opinion", "discussion_question"]


def api_get(endpoint, params, timeout=45):
    """
    Make a GET request to Arctic Shift and print useful debugging info
    if the request fails.
    """
    query = urlencode(params)
    url = f"{BASE}{endpoint}?{query}"

    print("Request:", url)

    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP ERROR {e.code}")
        print("Response body:")
        print(body)
        raise

    except URLError as e:
        print("Network error:", e)
        raise


def clean_text(text):
    text = (text or "").replace("\u200b", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def usable(text):
    if not text:
        return False

    low = text.lower().strip()

    if low in {"[deleted]", "[removed]"}:
        return False

    if len(text) < MIN_CHARS:
        return False

    # Filter obvious subreddit boilerplate / recurring admin threads.
    bad_phrases = [
        "casual discussion thread",
        "what have you been watching",
        "please don't downvote opinions",
        "weekly /r/truefilm",
        "subreddit rules",
    ]

    return not any(x in low for x in bad_phrases)


def clip(text):
    if len(text) <= MAX_CHARS:
        return text

    cut = text[:MAX_CHARS]

    last = max(
        cut.rfind(". "),
        cut.rfind("? "),
        cut.rfind("! "),
    )

    if last > MAX_CHARS * 0.65:
        cut = cut[: last + 1]

    return cut.strip()


def normalize(text):
    text = text.lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fingerprint(text):
    return hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()


def post_url(item):
    permalink = item.get("permalink")

    if permalink:
        return "https://www.reddit.com" + permalink

    reddit_id = item.get("id", "")
    return f"https://www.reddit.com/comments/{reddit_id}/"


def comment_url(item):
    permalink = item.get("permalink")

    if permalink:
        return "https://www.reddit.com" + permalink

    link_id = str(item.get("link_id", "")).replace("t3_", "")
    comment_id = item.get("id", "")

    if link_id and comment_id:
        return f"https://www.reddit.com/comments/{link_id}/_/{comment_id}/"

    return ""


def extract_data(obj):
    """
    Arctic Shift responses may return:
      {"data": [...]}
    or occasionally a direct list.

    This helper handles both safely.
    """
    if isinstance(obj, list):
        return obj

    if isinstance(obj, dict):
        data = obj.get("data", [])
        if isinstance(data, list):
            return data

    return []


def collect_posts(after, before):
    rows = []

    obj = api_get(
        "/posts/search",
        {
            "subreddit": SUBREDDIT,
            "after": after,
            "before": before,
            "limit": 100,
            "sort": "desc",
        },
    )

    items = extract_data(obj)

    print(f"  posts returned: {len(items)}")

    for item in items:
        title = clean_text(item.get("title"))
        body = clean_text(item.get("selftext"))

        if body:
            text = f"{title}\n\n{body}" if title else body
        else:
            text = title

        text = clip(text)

        if not usable(text):
            continue

        rows.append(
            {
                "text": text,
                "source_url": post_url(item),
                "source_type": "post",
                "created_utc": item.get("created_utc", ""),
                "score": item.get("score", 0) or 0,
            }
        )

    return rows


def collect_comments(after, before):
    rows = []

    obj = api_get(
        "/comments/search",
        {
            "subreddit": SUBREDDIT,
            "after": after,
            "before": before,
            "limit": 100,
            "sort": "desc",
        },
    )

    items = extract_data(obj)

    print(f"  comments returned: {len(items)}")

    for item in items:
        text = clip(clean_text(item.get("body")))

        if not usable(text):
            continue

        rows.append(
            {
                "text": text,
                "source_url": comment_url(item),
                "source_type": "comment",
                "created_utc": item.get("created_utc", ""),
                "score": item.get("score", 0) or 0,
            }
        )

    return rows


def collect():
    rows = []

    for after, before in WINDOWS:
        print()
        print("=" * 70)
        print(f"Fetching {after} -> {before}")
        print("=" * 70)

        try:
            rows.extend(collect_posts(after, before))
        except Exception as e:
            print("  post query failed:", type(e).__name__, e)

        time.sleep(1)

        try:
            rows.extend(collect_comments(after, before))
        except Exception as e:
            print("  comment query failed:", type(e).__name__, e)

        time.sleep(1)

    # Exact-text dedupe
    seen = set()
    unique = []

    for row in rows:
        fp = fingerprint(row["text"])

        if fp in seen:
            continue

        seen.add(fp)
        unique.append(row)

    return unique


QUESTION_PATTERNS = [
    r"\bwhat do you think\b",
    r"\bwhat are your thoughts\b",
    r"\bwhat(?:'s| is) your\b",
    r"\bwhy (?:do|does|did|is|are|was|were|would|can|could)\b",
    r"\bhow (?:do|does|did|is|are|was|were|would|can|could)\b",
    r"\bdoes anyone\b",
    r"\bcan anyone\b",
    r"\bany recommendations\b",
    r"\brecommend(?: me|ations?)\b",
    r"\bwhat (?:films|movies|directors|actors|performances)\b",
    r"\bwhich (?:films|movies|directors|actors|performances)\b",
    r"\bhas anyone\b",
]

ANALYSIS_CUES = [
    "because",
    "therefore",
    "however",
    "although",
    "whereas",
    "this suggests",
    "this shows",
    "this reinforces",
    "the film uses",
    "the director uses",
    "cinematography",
    "editing",
    "framing",
    "composition",
    "narrative",
    "structure",
    "character arc",
    "theme",
    "thematic",
    "subtext",
    "motif",
    "symbol",
    "symbolism",
    "contrast",
    "parallel",
    "represents",
    "functions as",
    "historical context",
    "adaptation",
    "mise-en-scène",
    "mise en scene",
    "point of view",
    "camera",
    "lighting",
    "sound design",
]

OPINION_CUES = [
    "i think",
    "i feel",
    "i love",
    "i loved",
    "i hate",
    "i hated",
    "i like",
    "i liked",
    "i prefer",
    "my favorite",
    "my favourite",
    "underrated",
    "overrated",
    "masterpiece",
    "best film",
    "worst film",
    "amazing",
    "terrible",
    "boring",
    "enjoyed",
    "disliked",
    "not a fan",
    "not my favorite",
    "not my favourite",
]


def classify(text):
    """
    Heuristic pre-labeling.

    IMPORTANT:
    These are provisional labels only.
    The assignment expects manual review before training.
    """
    low = text.lower()

    q_hits = sum(bool(re.search(pattern, low)) for pattern in QUESTION_PATTERNS)
    q_marks = low.count("?")
    a_hits = sum(cue in low for cue in ANALYSIS_CUES)
    o_hits = sum(cue in low for cue in OPINION_CUES)
    word_count = len(low.split())

    # Discussion question:
    # Don't rely on question mark alone; look for solicitation phrases.
    if q_hits >= 1 and q_marks >= 1:
        if word_count > 250 and a_hits >= 4:
            return (
                "discussion_question",
                0.58,
                "Ambiguous: substantial analysis, but the post ultimately solicits discussion.",
            )

        return (
            "discussion_question",
            min(0.90, 0.72 + 0.04 * q_hits),
            "Primary purpose appears to solicit explanation, comparison, recommendation, or debate.",
        )

    # Analysis:
    analysis_score = a_hits

    if word_count > 180:
        analysis_score += 1

    if word_count > 350:
        analysis_score += 1

    if analysis_score >= 3:
        confidence = min(0.91, 0.62 + 0.05 * analysis_score)

        return (
            "analysis",
            confidence,
            "Reasoning or interpretation is the main substance of the text.",
        )

    # Opinion:
    if o_hits >= 1 and analysis_score <= 2:
        confidence = 0.76 if word_count < 170 else 0.65

        return (
            "opinion",
            confidence,
            "Primarily expresses a judgment, preference, or evaluation with limited development.",
        )

    # Fallbacks
    if word_count >= 210:
        return (
            "analysis",
            0.55,
            "Low-confidence fallback: extended film discussion appears more analytical than purely evaluative.",
        )

    if q_marks >= 1:
        return (
            "discussion_question",
            0.54,
            "Low-confidence fallback: contains a question but purpose should be manually checked.",
        )

    return (
        "opinion",
        0.52,
        "Low-confidence fallback: brief non-question film commentary.",
    )


def prelabel(rows):
    labeled = []

    for row in rows:
        label, confidence, note = classify(row["text"])

        item = dict(row)

        item["label"] = label
        item["confidence"] = round(confidence, 3)
        item["notes"] = note
        item["manual_review"] = "YES" if confidence < 0.70 else ""

        labeled.append(item)

    return labeled


def choose_balanced(rows):
    groups = defaultdict(list)

    for row in rows:
        groups[row["label"]].append(row)

    for label in LABELS:
        groups[label].sort(
            key=lambda r: (
                float(r["confidence"]),
                min(int(r.get("score") or 0), 500),
            ),
            reverse=True,
        )

    print()
    print("Candidate counts:")
    for label in LABELS:
        print(f"  {label}: {len(groups[label])}")

    for label in LABELS:
        if len(groups[label]) < TARGET_PER_LABEL:
            raise RuntimeError(
                f"Only {len(groups[label])} '{label}' candidates found. "
                f"Need {TARGET_PER_LABEL}. "
                "Add more date windows or collect more results."
            )

    chosen = []

    for label in LABELS:
        chosen.extend(groups[label][:TARGET_PER_LABEL])

    return chosen


def validate(rows):
    if len(rows) != TARGET_TOTAL:
        raise ValueError(f"Expected {TARGET_TOTAL} rows, got {len(rows)}")

    counts = Counter(row["label"] for row in rows)

    for label in LABELS:
        if counts[label] != TARGET_PER_LABEL:
            raise ValueError(
                f"Expected {TARGET_PER_LABEL} rows for {label}, "
                f"got {counts[label]}"
            )

    if any(not row["text"].strip() for row in rows):
        raise ValueError("Found empty text row.")

    fingerprints = [fingerprint(row["text"]) for row in rows]

    if len(set(fingerprints)) != len(fingerprints):
        raise ValueError("Duplicate text found in final dataset.")

    return counts


def save_csv(path, rows):
    fields = [
        "text",
        "label",
        "notes",
        "source_url",
        "source_type",
        "confidence",
        "manual_review",
        "created_utc",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)

        writer.writeheader()

        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def main():
    print("Collecting r/TrueFilm data from Arctic Shift...")

    raw = collect()

    print()
    print(f"Unique usable candidates: {len(raw)}")

    if len(raw) < TARGET_TOTAL:
        raise RuntimeError(
            f"Only collected {len(raw)} usable examples. "
            f"Need at least {TARGET_TOTAL}."
        )

    labeled = prelabel(raw)

    print(
        "Candidate label distribution:",
        Counter(row["label"] for row in labeled),
    )

    # Save all candidates first.
    save_csv("candidate_pool.csv", labeled)

    chosen = choose_balanced(labeled)

    counts = validate(chosen)

    save_csv("labeled_data.csv", chosen)

    review_rows = [
        row for row in chosen
        if row["manual_review"] == "YES"
    ]

    save_csv("review_queue.csv", review_rows)

    source_counts = Counter(row["source_type"] for row in chosen)

    summary = f"""TakeMeter / r/TrueFilm dataset
================================

Source:
Arctic Shift public Reddit archive

Subreddit:
r/TrueFilm

Final rows:
{len(chosen)}

Label counts:
analysis: {counts['analysis']}
opinion: {counts['opinion']}
discussion_question: {counts['discussion_question']}

Source types:
posts: {source_counts['post']}
comments: {source_counts['comment']}

Rows flagged for manual review:
{len(review_rows)}

Files created:
- labeled_data.csv
- review_queue.csv
- candidate_pool.csv
- dataset_summary.txt

IMPORTANT:
These are automated preliminary labels.
Manually review the dataset before training.
Keep at least 3 genuinely difficult examples for your README.
"""

    with open("dataset_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    print()
    print(summary)

    print("Done.")


if __name__ == "__main__":
    main()
