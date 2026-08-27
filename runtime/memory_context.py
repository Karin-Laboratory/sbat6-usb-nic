#!/usr/bin/env python3

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MEMORY = ROOT / "memory"
STATE = ROOT / "state"

MAX_CONTEXT_CHARS = 18000


def read_text(path, limit=6000):
    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        if len(text) > limit:
            text = text[-limit:]
            text = "[...前半省略...]\n" + text
        return text.strip()
    except Exception:
        return ""


def add_section(parts, title, text):
    if not text:
        return

    parts.append(
        f"===== {title} =====\n{text}"
    )


def latest_experience():
    directory = MEMORY / "experience"

    files = sorted(
        [
            p for p in directory.glob("*.md")
            if p.name != "README.md"
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not files:
        return ""

    return read_text(files[0], 7000)


def collect_memory_dir(name, per_file=3000, max_files=4):
    directory = MEMORY / name

    if not directory.exists():
        return ""

    files = sorted(
        directory.glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:max_files]

    result = []

    for path in files:
        text = read_text(path, per_file)

        if text:
            result.append(
                f"--- {path.name} ---\n{text}"
            )

    return "\n\n".join(result)


def recent_state():
    """
    Discordの配送状態などではなく、
    ButlerXが考える材料になりそうなstateを拾う。
    """

    if not STATE.exists():
        return ""

    ignore = {
        "discord.json",
        "discord_ear.json",
        "discord_loop.json",
        "discord_brain.json",
        "runtime.json",
        "last_discord_reply.txt",
    }

    candidates = []

    for path in STATE.iterdir():
        if not path.is_file():
            continue

        if path.name in ignore:
            continue

        if path.suffix not in {
            ".txt",
            ".json",
            ".md",
        }:
            continue

        try:
            if path.stat().st_size > 100_000:
                continue
        except OSError:
            continue

        candidates.append(path)

    candidates.sort(
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    result = []

    for path in candidates[:8]:
        text = read_text(path, 4000)

        if text:
            result.append(
                f"--- state/{path.name} ---\n{text}"
            )

    return "\n\n".join(result)


def build_memory_context(user_text=""):
    """
    α版のworking memory。

    現段階では高度な検索をしすぎず、
    最近の経験と重要な長期記憶、
    最近の作業状態をLunaへ渡す。

    将来ここを意味検索・記憶圧縮へ発展させる。
    """

    parts = []

    add_section(
        parts,
        "最近の経験日記",
        latest_experience(),
    )

    add_section(
        parts,
        "学んだこと",
        collect_memory_dir("lessons"),
    )

    add_section(
        parts,
        "現在の担当",
        collect_memory_dir("commitments"),
    )

    add_section(
        parts,
        "未解決事項",
        collect_memory_dir("unresolved"),
    )

    add_section(
        parts,
        "最近の作業状態",
        recent_state(),
    )

    text = "\n\n".join(parts)

    if len(text) > MAX_CONTEXT_CHARS:
        text = (
            "[古い記憶の一部を省略]\n"
            + text[-MAX_CONTEXT_CHARS:]
        )

    return text


if __name__ == "__main__":
    print(build_memory_context())
