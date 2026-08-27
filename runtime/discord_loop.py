#!/usr/bin/env python3

import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOKEN_FILE = Path.home() / ".config" / "butlerx" / "discord.token"
DISCORD_STATE = ROOT / "state" / "discord.json"
LOOP_STATE = ROOT / "state" / "discord_loop.json"

INBOX = ROOT / "inbox" / "discord.jsonl"
OUTBOX = ROOT / "outbox" / "discord.jsonl"

LAST_REPLY = ROOT / "state" / "last_discord_reply.txt"

API = "https://discord.com/api/v10"
POLL_SECONDS = 5


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


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(record, ensure_ascii=False)
            + "\n"
        )


def discord_request(method, path, token, body=None):
    while True:
        data = None

        headers = {
            "Authorization": f"Bot {token}",
            "User-Agent": "ButlerX-alpha/0.1",
        }

        if body is not None:
            data = json.dumps(
                body,
                ensure_ascii=False,
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            API + path,
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
                return json.loads(raw) if raw else None

        except urllib.error.HTTPError as e:
            text = e.read().decode(
                "utf-8",
                errors="replace",
            )

            if e.code == 429:
                try:
                    info = json.loads(text)
                    retry = float(
                        info.get("retry_after", 2)
                    )
                except Exception:
                    retry = 2

                print(
                    f"Discord rate limit: "
                    f"{retry:.1f}秒待ちます"
                )
                time.sleep(retry + 0.2)
                continue

            raise RuntimeError(
                f"Discord API HTTP {e.code}: {text}"
            ) from e


def recent_conversation(channel_id, token, bot_user_id):
    msgs = discord_request(
        "GET",
        f"/channels/{channel_id}/messages?limit=12",
        token,
    )

    msgs = sorted(
        msgs or [],
        key=lambda x: int(x["id"]),
    )

    lines = []

    for msg in msgs:
        content = msg.get("content", "").strip()
        if not content:
            continue

        author = msg.get("author", {})

        if author.get("id") == bot_user_id:
            name = "くろこちゃん"
        else:
            name = (
                msg.get("member", {}).get("nick")
                or author.get("global_name")
                or author.get("username")
                or "旦那さま"
            )

        lines.append(f"{name}: {content}")

    return "\n".join(lines[-10:])


def ask_luna(author, content, conversation):
    prompt = f"""
Discordで旦那さまから新しい発言が届きました。

現在の発言者表示名:
{author}

新しい発言:
{content}

直近の会話:
---
{conversation}
---

AGENTS.mdに定義されたButlerXとして自然に応答してください。

これは専用の私的なDiscordチャンネルでの普段の会話です。

必要に応じて、このButlerXプロジェクト内の記憶や設計資料を
読んでも構いません。ただし、単純な会話なら無理に調査しないでください。

今回はまだDiscord会話経路のα試験なので、
外部ホストへのSSHや設定変更、削除などの実作業は行わないでください。

返答について:
- 日本語
- 長さは話題に応じて自然に決める
- 旦那さまが短く話せば短く返してよい
- 必要なら「旦那さま」と呼んでよい
- くろこちゃん自身の言葉として返す
- 返答本文だけを最終回答にする
""".strip()

    if LAST_REPLY.exists():
        LAST_REPLY.unlink()

    cmd = [
        "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C",
        str(ROOT),
        "-m",
        "gpt-5.6-luna",
        "-s",
        "read-only",
        "--color",
        "never",
        "-o",
        str(LAST_REPLY),
        "-",
    ]

    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Codex exited with {result.returncode}"
        )

    reply = LAST_REPLY.read_text(
        encoding="utf-8"
    ).strip()

    if not reply:
        raise RuntimeError("Luna returned empty reply")

    # Discord 1メッセージの上限に余裕を持たせる
    if len(reply) > 1900:
        reply = reply[:1890] + "\n…"

    return reply


def main():
    token = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()

    discord = load_json(DISCORD_STATE)

    channel_id = discord["channel_id"]
    bot_user_id = discord["bot_user_id"]

    state = load_json(LOOP_STATE)

    # 初回は現在地点を基準にして、
    # 過去メッセージへ突然返信しない。
    if not state.get("last_message_id"):
        latest = discord_request(
            "GET",
            f"/channels/{channel_id}/messages?limit=1",
            token,
        )

        if latest:
            state["last_message_id"] = latest[0]["id"]

        state["started_at"] = now_iso()
        save_json(LOOP_STATE, state)

    print()
    print("======================================")
    print(" ButlerX Discord conversation started")
    print(" #くろこちゃん を聞いています")
    print(" Ctrl+C で停止")
    print("======================================")
    print()

    while True:
        try:
            last_id = state.get("last_message_id")

            msgs = discord_request(
                "GET",
                (
                    f"/channels/{channel_id}/messages"
                    f"?limit=50&after={last_id}"
                ),
                token,
            )

            msgs = sorted(
                msgs or [],
                key=lambda x: int(x["id"]),
            )

            for msg in msgs:
                # 取得した時点で位置を進める。
                # AI失敗時の無限再応答を防ぐ。
                state["last_message_id"] = msg["id"]
                state["last_poll_at"] = now_iso()
                save_json(LOOP_STATE, state)

                author_data = msg.get("author", {})

                # 自分や他Botは無視
                if author_data.get("bot"):
                    continue

                content = msg.get("content", "").strip()

                if not content:
                    continue

                author = (
                    msg.get("member", {}).get("nick")
                    or author_data.get("global_name")
                    or author_data.get("username")
                    or "旦那さま"
                )

                print(
                    f"聞こえました: "
                    f"{author}: {content}"
                )

                append_jsonl(
                    INBOX,
                    {
                        "received_at": now_iso(),
                        "discord_message_id": msg["id"],
                        "channel_id": channel_id,
                        "author_id": author_data.get("id"),
                        "author_name": author,
                        "content": content,
                        "status": "received",
                    },
                )

                conversation = recent_conversation(
                    channel_id,
                    token,
                    bot_user_id,
                )

                print("Lunaが考えています...")

                try:
                    reply = ask_luna(
                        author,
                        content,
                        conversation,
                    )
                except Exception as e:
                    print(f"Luna error: {e}")
                    continue

                sent = discord_request(
                    "POST",
                    f"/channels/{channel_id}/messages",
                    token,
                    {
                        "content": reply,
                        "message_reference": {
                            "message_id": msg["id"]
                        },
                        "allowed_mentions": {
                            "replied_user": False
                        },
                    },
                )

                append_jsonl(
                    OUTBOX,
                    {
                        "sent_at": now_iso(),
                        "discord_message_id": sent.get("id"),
                        "in_reply_to": msg["id"],
                        "content": reply,
                        "model": "gpt-5.6-luna",
                    },
                )

                print(f"返事しました: {reply}")
                print()

            state["last_poll_at"] = now_iso()
            save_json(LOOP_STATE, state)

            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:
            print()
            print("ButlerX Discord conversation stopped.")
            break

        except Exception as e:
            print(f"loop error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
