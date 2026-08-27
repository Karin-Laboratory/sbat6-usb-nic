#!/usr/bin/env python3

import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOKEN_FILE = Path.home() / ".config" / "butlerx" / "discord.token"
INBOX = ROOT / "inbox" / "discord.jsonl"
OUTBOX = ROOT / "outbox" / "discord.jsonl"
STATE = ROOT / "state" / "discord_brain.json"
LAST_REPLY = Path("/tmp/butlerx_last_reply.txt")

API = "https://discord.com/api/v10"


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def api_post(path, token, body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        API + path,
        data=data,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "ButlerX-alpha/0.1",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Discord API HTTP {e.code}: {text}"
        ) from e


def read_inbox():
    rows = []

    if not INBOX.exists():
        return rows

    for line in INBOX.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    return rows


def append_outbox(record):
    OUTBOX.parent.mkdir(parents=True, exist_ok=True)

    with OUTBOX.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    brain = load_json(STATE)
    processed = set(brain.get("processed_message_ids", []))

    candidates = [
        row for row in read_inbox()
        if row.get("discord_message_id") not in processed
    ]

    if not candidates:
        print("未処理のメッセージはありません。")
        return

    # 今回は最も古い未処理メッセージを1通だけ扱う
    msg = candidates[0]

    author = msg.get("author_name", "旦那さま")
    content = msg.get("content", "")

    prompt = f"""
あなたはButlerX、愛称「くろこちゃん」です。

この屋敷に仕え始めたばかりの、頭がよく好奇心の強い若い執事です。
普段は簡潔で落ち着いています。
過度にへりくだらず、必要なら相手を「旦那さま」と呼びます。

今はDiscordで旦那さまとの会話経路を初めて試しています。

相手のDiscord表示名:
{author}

相手の発言:
{content}

この発言へ自然に返事してください。

条件:
- 日本語
- 1〜3文程度
- 技術説明は求められていなければ不要
- システムやテストの裏側を長々説明しない
- 「私はAIです」のような説明はしない
- 今回はファイル、Web、SSH、外部ツールを調べる必要はない
- 返答本文だけを出力する
""".strip()

    if LAST_REPLY.exists():
        LAST_REPLY.unlink()

    cmd = [
        "codex", "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C", "/tmp",
        "-m", "gpt-5.6-luna",
        "-s", "read-only",
        "--color", "never",
        "-o", str(LAST_REPLY),
        "-"
    ]

    print("===== LUNA =====")

    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"Codex failed: returncode={result.returncode}"
        )

    reply = LAST_REPLY.read_text(
        encoding="utf-8"
    ).strip()

    if not reply:
        raise SystemExit("Luna returned an empty reply")

    token = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()

    sent = api_post(
        f"/channels/{msg['channel_id']}/messages",
        token,
        {
            "content": reply,
            "message_reference": {
                "message_id": msg["discord_message_id"]
            },
            "allowed_mentions": {
                "replied_user": False
            }
        },
    )

    append_outbox({
        "sent_at": now_iso(),
        "discord_message_id": sent.get("id"),
        "in_reply_to": msg["discord_message_id"],
        "content": reply,
        "model": "gpt-5.6-luna",
    })

    processed.add(msg["discord_message_id"])

    brain["processed_message_ids"] = list(processed)[-1000:]
    brain["last_processed_at"] = now_iso()

    save_json(STATE, brain)

    print()
    print("===== くろこちゃんの返事 =====")
    print(reply)


if __name__ == "__main__":
    main()
