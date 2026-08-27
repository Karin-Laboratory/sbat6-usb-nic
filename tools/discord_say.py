#!/usr/bin/env python3

import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = Path.home() / ".config" / "butlerx" / "discord.token"
STATE_FILE = ROOT / "state" / "discord.json"

API = "https://discord.com/api/v10"
GUILD_NAME = "ButlerX"
CHANNEL_NAME = "くろこちゃん"


def request(method, path, token, body=None):
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
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Discord API HTTP {e.code}: {body}") from e


def main():
    import sys
    message_text = " ".join(sys.argv[1:]).strip()
    if not message_text:
        message_text = "旦那さま。聞こえますか。"
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    if not token:
        raise SystemExit("Discord token is empty")

    me = request("GET", "/users/@me", token)

    print("===== BOT =====")
    print(f"name: {me.get('username')}")
    print(f"id:   {me.get('id')}")

    guilds = request("GET", "/users/@me/guilds", token)

    guild = next(
        (g for g in guilds if g.get("name") == GUILD_NAME),
        None,
    )

    if guild is None:
        print()
        print("参加中サーバー:")
        for g in guilds:
            print(f"  {g.get('name')}  id={g.get('id')}")
        raise SystemExit(f"Server '{GUILD_NAME}' not found")

    print()
    print("===== SERVER =====")
    print(f"name: {guild['name']}")
    print(f"id:   {guild['id']}")

    channels = request(
        "GET",
        f"/guilds/{guild['id']}/channels",
        token,
    )

    channel = next(
        (
            c for c in channels
            if c.get("name") == CHANNEL_NAME
            and c.get("type") == 0
        ),
        None,
    )

    if channel is None:
        print()
        print("見えているテキストチャンネル:")
        for c in channels:
            if c.get("type") == 0:
                print(f"  #{c.get('name')}  id={c.get('id')}")
        raise SystemExit(f"Channel '#{CHANNEL_NAME}' not found")

    print()
    print("===== CHANNEL =====")
    print(f"name: #{channel['name']}")
    print(f"id:   {channel['id']}")

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(
            {
                "guild_id": guild["id"],
                "guild_name": guild["name"],
                "channel_id": channel["id"],
                "channel_name": channel["name"],
                "bot_user_id": me["id"],
                "bot_username": me["username"],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    message = request(
        "POST",
        f"/channels/{channel['id']}/messages",
        token,
        {
            "content": message_text
        },
    )

    print()
    print("===== MESSAGE SENT =====")
    print(message.get("content"))
    print(f"message id: {message.get('id')}")


if __name__ == "__main__":
    main()
