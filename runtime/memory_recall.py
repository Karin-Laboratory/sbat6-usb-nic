#!/usr/bin/env python3

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MEMORY = ROOT / "memory"
STATE = ROOT / "state"

MAX_FILE_BYTES = 200_000
MAX_RECALL_CHARS = 14_000

IGNORE_STATE = {
    "discord.json",
    "discord_ear.json",
    "discord_loop.json",
    "discord_brain.json",
    "runtime.json",
    "last_discord_reply.txt",
    "last_recall.txt",
}

TEMPORAL_WORDS = (
    "さっき",
    "この前",
    "前の",
    "以前",
    "あれ",
    "続き",
    "覚えて",
    "どうなった",
)


def read_text(path):
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return ""


def candidates():
    result = []

    for path in MEMORY.rglob("*"):
        if not path.is_file():
            continue
        if path.name == "README.md":
            continue
        if path.suffix not in {".md", ".txt", ".json"}:
            continue
        result.append(path)

    if STATE.exists():
        for path in STATE.iterdir():
            if not path.is_file():
                continue
            if path.name in IGNORE_STATE:
                continue
            if path.suffix not in {".md", ".txt", ".json"}:
                continue
            result.append(path)

    return result


def query_fragments(query):
    """
    日本語の形態素解析ライブラリを入れずに、
    queryから2〜8文字程度の部分文字列を作る。

    「さっきのディスクの件」なら
    「ディスク」などが記録側と一致する。
    """
    chunks = re.findall(
        r"[A-Za-z0-9_.:/+-]{2,}|[ぁ-んァ-ヶ一-龠々ー]{2,}",
        query,
    )

    stop = {
        "さっき",
        "この前",
        "覚えてる",
        "覚えて",
        "ください",
        "どうする",
        "どうなった",
        "について",
        "の件",
    }

    fragments = set()

    for chunk in chunks:
        if chunk in stop:
            continue

        # 長い日本語文を部分文字列へ分ける
        if re.search(r"[ぁ-んァ-ヶ一-龠々ー]", chunk):
            for length in range(2, min(8, len(chunk)) + 1):
                for i in range(len(chunk) - length + 1):
                    frag = chunk[i:i + length]
                    if frag not in stop:
                        fragments.add(frag)
        else:
            fragments.add(chunk.lower())

    return fragments


def score_document(query, text, path):
    score = 0
    lowered = text.lower()

    for frag in query_fragments(query):
        f = frag.lower()

        if f in lowered:
            # 長い一致ほど強く評価
            score += len(f) * len(f)

            # 複数出現も少し評価
            score += min(lowered.count(f), 5) * len(f)

        if f in path.name.lower():
            score += len(f) * len(f) * 3

    # 「さっき」「前の件」系なら最近の記録も候補へ
    if any(word in query for word in TEMPORAL_WORDS):
        try:
            age_hours = (
                __import__("time").time() - path.stat().st_mtime
            ) / 3600

            if age_hours < 1:
                score += 30
            elif age_hours < 24:
                score += 15
        except Exception:
            pass

    # stateは現在案件の作業記憶なので少し優先
    try:
        if path.parent == STATE:
            score += 8
    except Exception:
        pass

    return score


def recall_memory(query, max_files=5):
    ranked = []

    for path in candidates():
        text = read_text(path)

        if not text:
            continue

        score = score_document(query, text, path)

        if score > 0:
            ranked.append(
                (score, path.stat().st_mtime, path, text)
            )

    ranked.sort(
        key=lambda x: (x[0], x[1]),
        reverse=True,
    )

    sections = []

    for score, _, path, text in ranked[:max_files]:
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path

        # 巨大な文書は末尾中心
        if len(text) > 6000:
            text = "[前半省略]\n" + text[-6000:]

        sections.append(
            f"--- {rel} (relevance={score}) ---\n"
            f"{text.strip()}"
        )

    result = "\n\n".join(sections)

    if len(result) > MAX_RECALL_CHARS:
        result = (
            "[関連記憶の一部を省略]\n"
            + result[-MAX_RECALL_CHARS:]
        )

    return result


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "さっきのディスクの件"
    print(recall_memory(query))
