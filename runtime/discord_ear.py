#!/usr/bin/env python3

import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOKEN_FILE = Path.home() / ".config" / "butlerx" / "discord.token"
DISCORD_STATE = ROOT / "state" / "discord.json"
EAR_STATE = ROOT / "state" / "discord_ear.json"
INBOX = ROOT / "inbox" / "discord.jsonl"

API = "https://discord.com/api/v10"
POLL_SECONDS = 3


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


def api_request(method, path, token, body=None):
    data = None
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "ButlerX-alpha/0.1",
    }

    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        API + path,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Discord API HTTP {e.code}: {text}"
        ) from e


def append_inbox(record):
    INBOX.parent.mkdir(parents=True, exist_ok=True)

    with INBOX.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(record, ensure_ascii=False)
            + "\n"
        )


def main():
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    discord = load_json(DISCORD_STATE)

    channel_id = discord["channel_id"]
    bot_user_id = discord["bot_user_id"]

    state = load_json(EAR_STATE)

    # 初回起動時は過去ログを大量に取り込まず、
    # 現在の最新メッセージを基準点にする。
    if not state.get("last_message_id"):
        msgs = api_request(
            "GET",
            f"/channels/{channel_id}/messages?limit=1",
            token,
        )

        if msgs:
            state["last_message_id"] = msgs[0]["id"]

        state["started_at"] = now_iso()
        save_json(EAR_STATE, state)

        print("ButlerX ear initialized.")
        print("これ以降に #くろこちゃん へ書かれた発言を聞きます。")

    print("ButlerX ear listening... Ctrl-C to stop.")

    while True:
        try:
            last_id = state.get("last_message_id")

            path = (
                f"/channels/{channel_id}/messages"
                f"?limit=50&after={last_id}"
            )

            msgs = api_request("GET", path, token)

            # Discordは新しい順になる場合があるため、
            # snowflake IDで昇順に処理
            msgs = sorted(
                msgs or [],
                key=lambda x: int(x["id"]),
            )

            for msg in msgs:
                state["last_message_id"] = msg["id"]

                author = msg.get("author", {})

                # 自分の発言は耳に入れない
                if author.get("id") == bot_user_id:
                    continue

                # 他Botの発言もα版では無視
                if author.get("bot"):
                    continue

                content = msg.get("content", "").strip()

                if not content:
                    continue

                record = {
                    "received_at": now_iso(),
                    "discord_message_id": msg["id"],
                    "channel_id": channel_id,
                    "author_id": author.get("id"),
                    "author_name": author.get(
                        "global_name"
                    ) or author.get("username"),
                    "content": content,
                    "status": "new",
                }

                append_inbox(record)

                print()
                print("===== 聞こえました =====")
                print(
                    f"{record['author_name']}: "
                    f"{record['content']}"
                )

            state["last_poll_at"] = now_iso()
            save_json(EAR_STATE, state)

            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:
            print()
            print("ButlerX ear stopped.")
            break

        except Exception as e:
            print(f"ear error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
