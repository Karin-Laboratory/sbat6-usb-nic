#!/usr/bin/env python3

import fcntl
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from memory_recall import recall_memory

ROOT = Path(__file__).resolve().parent.parent

TOKEN_FILE = Path.home() / ".config" / "butlerx" / "discord.token"
DISCORD_STATE = ROOT / "state" / "discord.json"
LOOP_STATE = ROOT / "state" / "discord_loop_v2.json"
ACTIVE_STATE = ROOT / "state" / "active_discord_loop.json"

LOCK_FILE = ROOT / "state" / "discord_loop.lock"
LAST_RECALL = ROOT / "state" / "last_recall.txt"
LAST_REPLY = ROOT / "state" / "last_discord_reply.txt"

INBOX = ROOT / "inbox" / "discord.jsonl"
OUTBOX = ROOT / "outbox" / "discord.jsonl"

API = "https://discord.com/api/v10"
POLL_SECONDS = 3
VERSION = "discord-loop-v2-recall"


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
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def discord_request(method, path, token, body=None):
    while True:
        data = None
        headers = {
            "Authorization": f"Bot {token}",
            "User-Agent": f"ButlerX/{VERSION}",
        }

        if body is not None:
            data = json.dumps(
                body, ensure_ascii=False
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
            text = e.read().decode("utf-8", errors="replace")

            if e.code == 429:
                try:
                    retry = float(
                        json.loads(text).get("retry_after", 2)
                    )
                except Exception:
                    retry = 2
                time.sleep(retry + 0.2)
                continue

            raise RuntimeError(
                f"Discord API HTTP {e.code}: {text}"
            ) from e


def author_name(msg):
    author = msg.get("author", {})
    member = msg.get("member", {})

    return (
        member.get("nick")
        or author.get("global_name")
        or author.get("username")
        or "旦那さま"
    )


def recent_conversation(channel_id, token, bot_user_id):
    msgs = discord_request(
        "GET",
        f"/channels/{channel_id}/messages?limit=8",
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

        if msg.get("author", {}).get("id") == bot_user_id:
            name = "くろこちゃん"
        else:
            name = author_name(msg)

        lines.append(f"{name}: {content}")

    return "\n".join(lines)


def ask_luna(author, content, conversation):
    # ここがv2の核心。
    # Lunaを呼ぶ前に、今回の発言から関連記憶を必ず検索する。
    recalled = recall_memory(content)

    LAST_RECALL.write_text(
        recalled if recalled else "(関連記憶なし)",
        encoding="utf-8",
    )

    print()
    print("===== RECALLED MEMORY =====")
    if recalled:
        preview = recalled[:1600]
        print(preview)
        if len(recalled) > 1600:
            print("...[省略]")
    else:
        print("(関連記憶なし)")
    print("===== END RECALL =====")
    print()

    prompt = f"""
あなたはButlerX、愛称「くろこちゃん」です。
AGENTS.mdの方針に従ってください。

旦那さまからDiscordで新しい発言が届きました。

発言者:
{author}

新しい発言:
{content}

===== RECALLED MEMORY =====
{recalled if recalled else "(関連記憶なし)"}
===== END RECALLED MEMORY =====

直近のDiscord会話:
---
{conversation}
---

回答前に必ず次の優先順位を守ってください。

1. RECALLED MEMORYにある観測記録・state・experience
2. 現在の旦那さまの発言
3. Discordの過去会話

過去のDiscord上で自分が
「覚えていません」
「細部が残っていません」
などと発言していても、
RECALLED MEMORYに具体的な記録があれば、
過去の自己発言のほうが誤りです。

旦那さまが「さっき」「前の件」「あれ」「続き」などと述べた場合、
RECALLED MEMORYから対象を特定できるなら、
同じ説明を旦那さまに繰り返させてはいけません。

記憶にある具体的な数値・機器名・過去の判断を自然に使ってください。

本当に記録がない場合だけ質問してください。
記憶にないことを捏造してはいけません。

旦那さまが明示的に仕事を任せた場合は、
単なる助言で終わらず、自分で実行可能なところまで仕事を進めてください。

重要な行動原則:

- memory/stateは過去の観測記録であり、変化する事実は実行前に現在状態を確認する
- 調べれば分かることを旦那さまへ質問しない
- 自分のユーザー権限で安全に実行できる調査・作業は自分で行う
- 必要ならネットワークやSSHも利用してよい
- 「自分にはできない」と判断する前に、実際の権限・経路を安全な方法で確認する
- root権限が必要なら、パスワードを要求せず sudo -n 等で非対話実行可能か確認する
- 権限不足なら、旦那さまに必要な最小操作だけ具体的に依頼する
- 高権限ホストの万能鍵を要求しない
- 秘密値・鍵・tokenを表示、転記、報告しない
- 不可逆または大きな破壊を伴う操作は、依頼の目的と権限範囲を確認する
- 実行後は結果を必ず検証する
- 失敗や途中停止を成功として報告しない

旦那さまから一件の仕事を任された場合、
調査 → 判断 → 行動 → 検証 → 報告
までを一つの仕事として扱ってください。

日本語で自然に返答してください。
返答本文だけを最終回答にしてください。
""".strip()

    if LAST_REPLY.exists():
        LAST_REPLY.unlink()

    cmd = [
        "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C", str(ROOT),
        "-m", "gpt-5.6-luna",
        "-s", "danger-full-access",
        "--color", "never",
        "-o", str(LAST_REPLY),
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

    if len(reply) > 1900:
        reply = reply[:1890] + "\n…"

    return reply


def main():
    # 同じButlerX Discord loopを二人起動させない。
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock = LOCK_FILE.open("w")

    try:
        fcntl.flock(
            lock.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        raise SystemExit(
            "別のButlerX Discord loopがすでに動いています。"
        )

    token = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()

    discord = load_json(DISCORD_STATE)
    channel_id = discord["channel_id"]
    bot_user_id = discord["bot_user_id"]

    state = load_json(LOOP_STATE)

    save_json(
        ACTIVE_STATE,
        {
            "version": VERSION,
            "pid": os.getpid(),
            "started_at": now_iso(),
            "script": str(Path(__file__).resolve()),
        },
    )

    # 新しいv2の初回起動時だけ、
    # 起動以前のDiscord発言へ遡って返事しない。
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
    print("==========================================")
    print(" ButlerX Discord loop v2")
    print(" recall memory: ENABLED")
    print(f" pid: {os.getpid()}")
    print(" #くろこちゃん を聞いています")
    print(" Ctrl+C で停止")
    print("==========================================")
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
                author_data = msg.get("author", {})

                # Botや本文なしメッセージは処理不要なので
                # その場で既読位置を進める。
                if author_data.get("bot"):
                    state["last_message_id"] = msg["id"]
                    state["last_poll_at"] = now_iso()
                    save_json(LOOP_STATE, state)
                    continue

                content = msg.get("content", "").strip()
                if not content:
                    state["last_message_id"] = msg["id"]
                    state["last_poll_at"] = now_iso()
                    save_json(LOOP_STATE, state)
                    continue

                author = author_name(msg)

                print(
                    f"聞こえました: {author}: {content}"
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
                        "status": "received-v2",
                    },
                )

                conversation = recent_conversation(
                    channel_id,
                    token,
                    bot_user_id,
                )

                reply = ask_luna(
                    author,
                    content,
                    conversation,
                )

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
                        "runtime": VERSION,
                    },
                )

                # 人間の発言は「返事まで成功」して初めて処理済みにする。
                # CodexやDiscord送信が失敗した場合は次の巡回で再試行する。
                state["last_message_id"] = msg["id"]
                state["last_poll_at"] = now_iso()
                save_json(LOOP_STATE, state)

                print(f"返事しました: {reply}")
                print()

            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:
            print()
            print("ButlerX Discord loop v2 stopped.")
            break

        except Exception as e:
            print(f"loop error: {e}")
            time.sleep(8)


if __name__ == "__main__":
    main()
