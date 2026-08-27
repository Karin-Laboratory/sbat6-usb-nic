#!/usr/bin/env python3

import fcntl
import json
import os
import queue
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

# v2のDiscord API・記憶・Luna呼び出しを再利用する
from discord_loop_v2 import (
    ROOT,
    TOKEN_FILE,
    DISCORD_STATE,
    LOCK_FILE,
    INBOX,
    OUTBOX,
    now_iso,
    load_json,
    save_json,
    append_jsonl,
    discord_request,
    author_name,
    recent_conversation,
    ask_luna,
)

VERSION = "discord-loop-v3-async-ear"

LOOP_STATE = ROOT / "state" / "discord_loop_v3.json"
OLD_LOOP_STATE = ROOT / "state" / "discord_loop_v2.json"
ACTIVE_STATE = ROOT / "state" / "active_discord_loop.json"
JOB_DIR = ROOT / "state" / "discord_jobs"

POLL_SECONDS = 3


TEXT_ATTACHMENT_EXTS = {
    ".txt", ".md", ".log", ".json", ".yaml", ".yml",
    ".csv", ".ini", ".conf", ".cfg", ".sh",
    ".py", ".js", ".ts",
}

MAX_ATTACHMENT_BYTES = 512 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 1024 * 1024


def attachment_text(msg):
    attachments = msg.get("attachments") or []
    if not attachments:
        return ""

    parts = []
    total = 0

    for item in attachments:
        filename = item.get("filename") or "attachment"
        suffix = Path(filename).suffix.lower()

        if suffix not in TEXT_ATTACHMENT_EXTS:
            parts.append(
                f"[添付ファイル: {filename} / "
                f"未対応形式のため本文は読み込んでいません]"
            )
            continue

        size = int(item.get("size") or 0)

        if size > MAX_ATTACHMENT_BYTES:
            parts.append(
                f"[添付ファイル: {filename} / "
                f"サイズ上限を超えたため読み込んでいません]"
            )
            continue

        if total + size > MAX_TOTAL_ATTACHMENT_BYTES:
            parts.append(
                f"[添付ファイル: {filename} / "
                f"添付合計サイズ上限のため読み込んでいません]"
            )
            continue

        url = item.get("url")
        if not url:
            parts.append(
                f"[添付ファイル: {filename} / URL取得失敗]"
            )
            continue

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "ButlerX/discord-attachment-reader"
                },
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read(MAX_ATTACHMENT_BYTES + 1)

            if len(raw) > MAX_ATTACHMENT_BYTES:
                parts.append(
                    f"[添付ファイル: {filename} / "
                    f"サイズ上限を超えたため読み込んでいません]"
                )
                continue

            total += len(raw)

            text = raw.decode("utf-8", errors="replace")

            parts.append(
                f"[添付ファイル: {filename}]\n"
                f"----- 添付本文ここから -----\n"
                f"{text}\n"
                f"----- 添付本文ここまで -----"
            )

        except Exception as e:
            parts.append(
                f"[添付ファイル: {filename} / "
                f"読み込み失敗: {type(e).__name__}]"
            )

    return "\n\n".join(parts)


TASK_WORDS = (
    "お願い",
    "任せ",
    "続けて",
    "進めて",
    "調べて",
    "確認して",
    "直して",
    "やって",
    "作って",
    "変更して",
    "対応して",
    "修正して",
    "拡張して",
    "残して",
    "保存して",
    "更新して",
    "整理して",
    "覚えておいて",
    "まとめておいて",
)


def needs_immediate_ack(content):
    # 長いだけの質問には二重返答しない。
    # 実行・調査・記録など、時間を要し得る依頼だけ即時受領する。
    return any(word in content for word in TASK_WORDS)


def job_path(message_id):
    return JOB_DIR / f"{message_id}.json"


def save_job(job):
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    save_json(job_path(job["discord_message_id"]), job)



def ask_ack_luna(author, content, conversation, message_id):
    """ACKの要否と短い文面だけをLunaに判断させる。"""

    out_dir = ROOT / "state" / "ack_replies"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{message_id}.txt"

    if out.exists():
        out.unlink()

    prompt = f"""
あなたは ButlerX、愛称「くろこちゃん」です。

Discordで旦那さまから発言が届きました。
この時点では仕事そのものを解決してはいけません。

あなたの仕事はただ一つです。

「最終回答まで少し時間がかかりそうなので、
先に短い受領返事をした方が自然か」
を判断してください。

発言者:
{author}

新しい発言:
{content}

直近の会話:
---
{conversation[-2500:]}
---

判断基準:

- 調査、確認、設定、作成、変更、修正、整理、記録など、
  作業を任された場合は原則ACKする。
- すぐには終わらない質問や、複数段階の仕事もACKする。
- 単なる雑談、感想、相づち、短く即答できる質問なら
  原則ACKしない。
- ACKでは仕事の結果を答えない。
- 完了したふりをしない。
- 質問を返さない。
- 1文だけ、短く自然にする。
- 「承知しました、旦那さま。少々お待ちください。」
  だけに固定しない。
- 内容に合わせて、
  「確認します、旦那さま。」
  「承知しました。こちらで調べます。」
  「お任せください。確認してきます。」
  「分かりました。こちらで進めます。」
  など自然に変化させる。
- 直近の会話で使ったACKと同じ表現は、できれば避ける。
- 丁寧だが芝居がかりすぎない。

出力形式は厳守してください。

ACKが不要:
NO_ACK

ACKが必要:
ACK: <短い受領返事>

これ以外は出力しないでください。
""".strip()

    cmd = [
        "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C", str(ROOT),
        "-m", "gpt-5.6-luna",
        "-s", "read-only",
        "--color", "never",
        "-o", str(out),
        "-",
    ]

    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=45,
    )

    if result.returncode != 0 or not out.exists():
        raise RuntimeError(
            "ACK Luna failed: "
            + (result.stderr.strip() or f"rc={result.returncode}")
        )

    answer = out.read_text(encoding="utf-8").strip()
    out.unlink(missing_ok=True)

    if answer == "NO_ACK":
        return None

    if answer.startswith("ACK:"):
        ack = answer[4:].strip()
        if ack:
            # Discordで巨大ACKにならないための最後の柵
            return ack[:120]

    raise RuntimeError(f"invalid ACK Luna answer: {answer!r}")


def ack_worker_loop(
    ack_queue,
    work_queue,
    token,
    channel_id,
    bot_user_id,
):
    while True:
        job = ack_queue.get()

        try:
            # crash復帰などで既にACK済みなら重複させない。
            if not job.get("acknowledged_at"):
                conversation = recent_conversation(
                    channel_id,
                    token,
                    bot_user_id,
                )

                ack = ask_ack_luna(
                    job["author_name"],
                    job["content"],
                    conversation,
                    job["discord_message_id"],
                )

                if ack:
                    sent = discord_request(
                        "POST",
                        f"/channels/{channel_id}/messages",
                        token,
                        {
                            "content": ack,
                            "message_reference": {
                                "message_id":
                                    job["discord_message_id"]
                            },
                            "allowed_mentions": {
                                "replied_user": False
                            },
                        },
                    )

                    job["acknowledged_at"] = now_iso()
                    job["ack_message_id"] = sent.get("id")
                    job["ack_content"] = ack
                    save_job(job)

                    append_jsonl(
                        OUTBOX,
                        {
                            "sent_at": now_iso(),
                            "discord_message_id":
                                sent.get("id"),
                            "in_reply_to":
                                job["discord_message_id"],
                            "content": ack,
                            "runtime": VERSION,
                            "kind": "ack-luna",
                        },
                    )

            # ACK判断が終わってから本処理へ。
            work_queue.put(job)

        except Exception as e:
            # ACKの失敗だけで本仕事まで失わせない。
            job["ack_error_at"] = now_iso()
            job["ack_error"] = repr(e)
            save_job(job)

            print(
                f"ack worker error: {e}",
                flush=True,
            )

            work_queue.put(job)

        finally:
            ack_queue.task_done()


def worker_loop(work_queue, token, channel_id, bot_user_id):
    while True:
        job = work_queue.get()

        try:
            job["status"] = "running"
            job["started_at"] = now_iso()
            save_job(job)

            conversation = recent_conversation(
                channel_id,
                token,
                bot_user_id,
            )

            reply = ask_luna(
                job["author_name"],
                job["content"],
                conversation,
            )

            sent = discord_request(
                "POST",
                f"/channels/{channel_id}/messages",
                token,
                {
                    "content": reply,
                    "message_reference": {
                        "message_id":
                            job["discord_message_id"]
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
                    "in_reply_to":
                        job["discord_message_id"],
                    "content": reply,
                    "model": "gpt-5.6-luna",
                    "runtime": VERSION,
                    "kind": "final",
                },
            )

            job["status"] = "done"
            job["finished_at"] = now_iso()
            job["reply_message_id"] = sent.get("id")
            save_job(job)

            print(
                f"仕事完了: "
                f"{job['author_name']}: {reply}",
                flush=True,
            )

        except Exception as e:
            # 実作業を含む可能性があるので、
            # 同じ仕事を勝手に自動再実行しない。
            job["status"] = "error"
            job["error_at"] = now_iso()
            job["error"] = repr(e)
            save_job(job)

            print(
                f"worker error: {e}",
                flush=True,
            )

            try:
                discord_request(
                    "POST",
                    f"/channels/{channel_id}/messages",
                    token,
                    {
                        "content":
                            "作業中に問題が起きました。"
                            "途中状態を記録しました。"
                            "同じ操作は勝手に再実行していません。",
                        "message_reference": {
                            "message_id":
                                job["discord_message_id"]
                        },
                        "allowed_mentions": {
                            "replied_user": False
                        },
                    },
                )
            except Exception:
                pass

        finally:
            work_queue.task_done()


def main():
    LOCK_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lock = LOCK_FILE.open("w")

    try:
        fcntl.flock(
            lock.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        raise SystemExit(
            "別のButlerX Discord loopが動いています。"
        )

    token = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()

    discord = load_json(DISCORD_STATE)
    channel_id = discord["channel_id"]
    bot_user_id = discord["bot_user_id"]

    state = load_json(LOOP_STATE)

    # v2から初回だけ受信位置を継承する。
    if not state.get("last_message_id"):
        old = load_json(OLD_LOOP_STATE)

        if old.get("last_message_id"):
            state["last_message_id"] = \
                old["last_message_id"]
        else:
            latest = discord_request(
                "GET",
                f"/channels/{channel_id}/messages?limit=1",
                token,
            )
            if latest:
                state["last_message_id"] = latest[0]["id"]

        state["started_at"] = now_iso()
        save_json(LOOP_STATE, state)

    save_json(
        ACTIVE_STATE,
        {
            "version": VERSION,
            "pid": os.getpid(),
            "started_at": now_iso(),
            "script": str(Path(__file__).resolve()),
            "architecture":
                "ear-main-thread + serial-worker",
        },
    )

    ack_queue = queue.Queue()
    work_queue = queue.Queue()

    ack_worker = threading.Thread(
        target=ack_worker_loop,
        args=(
            ack_queue,
            work_queue,
            token,
            channel_id,
            bot_user_id,
        ),
        daemon=True,
        name="butlerx-ack-worker",
    )

    worker = threading.Thread(
        target=worker_loop,
        args=(
            work_queue,
            token,
            channel_id,
            bot_user_id,
        ),
        daemon=True,
        name="butlerx-worker",
    )

    ack_worker.start()
    worker.start()

    # crash前にqueuedだった仕事だけ復元。
    # runningだったものは重複実行防止のため勝手に再開しない。
    JOB_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(JOB_DIR.glob("*.json")):
        job = load_json(path)
        if job.get("status") == "queued":
            ack_queue.put(job)

    print()
    print("==========================================")
    print(" ButlerX Discord loop v3")
    print(" ear: ALWAYS LISTENING")
    print(" acknowledgement: LUNA TRIAGE")
    print(" worker: SERIAL")
    print(f" pid: {os.getpid()}")
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

            # メッセージが無い時も「耳が生きている」ことを記録する。
            state["last_poll_at"] = now_iso()
            state["worker_alive"] = worker.is_alive()
            state["ack_worker_alive"] = ack_worker.is_alive()
            state["ack_queue_depth"] = ack_queue.qsize()
            state["queue_depth"] = work_queue.qsize()
            save_json(LOOP_STATE, state)

            for msg in msgs:
                author_data = msg.get("author", {})

                # bot発言は読み飛ばす
                if author_data.get("bot"):
                    state["last_message_id"] = msg["id"]
                    state["last_poll_at"] = now_iso()
                    save_json(LOOP_STATE, state)
                    continue

                content = msg.get("content", "").strip()
                attached = attachment_text(msg)

                if attached:
                    if content:
                        content = content + "\n\n" + attached
                    else:
                        content = attached

                if not content:
                    state["last_message_id"] = msg["id"]
                    save_json(LOOP_STATE, state)
                    continue

                author = author_name(msg)

                print(
                    f"聞こえました: {author}: {content}",
                    flush=True,
                )

                job = {
                    "discord_message_id": msg["id"],
                    "channel_id": channel_id,
                    "author_id": author_data.get("id"),
                    "author_name": author,
                    "content": content,
                    "received_at": now_iso(),
                    "status": "queued",
                }

                # 仕事を永続キューへ保存してから既読位置を進める。
                save_job(job)

                append_jsonl(
                    INBOX,
                    {
                        **job,
                        "runtime": VERSION,
                    },
                )

                # ACKの要否・文面は専用Lunaに渡す。
                # 耳は待たず、すぐDiscord監視へ戻る。
                ack_queue.put(job)

                state["last_message_id"] = msg["id"]
                state["last_poll_at"] = now_iso()
                save_json(LOOP_STATE, state)

            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:
            break

        except Exception as e:
            print(
                f"ear loop error: {e}",
                flush=True,
            )
            time.sleep(5)


if __name__ == "__main__":
    main()
