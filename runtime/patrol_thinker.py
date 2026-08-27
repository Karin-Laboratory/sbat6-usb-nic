#!/usr/bin/env python3

import fcntl
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/masataka/projects/butlerx")
STATE = ROOT / "state"
QUEUE = STATE / "patrol_queue"
LOG = ROOT / "logs" / "patrol_thinker.log"
IDEAS = ROOT / "memory" / "ideas"
LOCK = STATE / "patrol_thinker.lock"

CODEX = "/home/masataka/.local/bin/codex"
MODEL = "gpt-5.6-luna"


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def log(text):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{now_iso()} {text}\n")


def think(event):
    event_type = event.get("event_type", "change")

    if event_type == "idle_curiosity":
        mission = """
今回は異常対応ではありません。

屋敷が静かなため、自分から一つだけ
「まだ知らないこと」を選んで調べる自由探索です。

対象は現在のところ agent-101-vm と
ButlerXプロジェクト自身に限定します。

state、memory、設定、サービス、プロセス、
OS、ネットワークのローカル状態、ログなどから、
今後屋敷を管理するうえで役立ちそうな未知を一つ選んでください。

重要:
- まず既存memoryを見て、既に分かっていることの反復を避ける
- memory/ideas の最新の巡回記録も確認する
- 前回の「次につながる疑問」が未解決なら、原則としてそこから探索を続ける
- ただし、もっと重要な未知や新しい変化を見つけた場合はそちらを優先してよい
- 一件だけ選ぶ
- 実際に読み取り専用コマンドで調査する
- 推測だけで終わらない
- 過去ログに異常があっても、現在も異常か確認する
- sandbox、namespace、systemd bus、network等の制約で観測できない場合がある
- 「workerから見えない」と「実際に存在しない」を混同しない
- 観測不能なら、その制約自体を明記する
- memory/estate に確認済みの現在構成があれば、それも証拠として扱う
- 設定変更、削除、再起動、サービス操作はしない
- 無理に問題を発見しなくてよい
- 関係ない過去案件を混ぜない

最後に、

探索対象:
なぜ気になった:
調べたこと:
分かったこと:
次につながる疑問:
旦那さまへ知らせる価値:

の形式でまとめてください。
"""
    else:
        mission = """
巡回中に変化を検出しました。

この変化について、

1. 重要か、些細か
2. 何が起きた可能性があるか
3. 追加で調べる価値があるか
4. 必要なら読み取り専用で現在状態を実際に調べる
5. 旦那さまへ知らせるほどか

を判断してください。

重要:
- 過去ログに失敗があっても、現在状態を確認してから結論を出す
- 推測と確認済み事実を区別する
- 関係ない過去案件を混ぜない
- 変更操作はしない

最後に、

重要度:
判断:
確認した現在状態:
次に知りたいこと:
旦那さまへの通知:

の形式でまとめてください。
"""

    prompt = f"""
あなたは ButlerX、人格名「くろこちゃん」です。

あなたは屋敷を常時巡回している女性の執事です。
将来は屋敷全体を取り仕切るメイド頭へ成長します。

今回の巡回イベント:

{json.dumps(event, ensure_ascii=False, indent=2)}

{mission}

ButlerXプロジェクト内のmemory、state、設計資料は
必要に応じて読んで構いません。

今回は観察・調査・思考だけです。
読み取り専用の調査は自分で実行してください。
"""

    cmd = [
        CODEX,
        "exec",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "-C", str(ROOT),
        "-m", MODEL,
        "-s", "read-only",
        "-",
    ]

    p = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=300,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"codex rc={p.returncode}: "
            f"{p.stderr[-2000:]}"
        )

    answer = p.stdout.strip()
    if not answer:
        answer = p.stderr.strip()

    return answer


def process_event(path):
    event = json.loads(path.read_text(encoding="utf-8"))

    log(f"thinking about {path.name}")

    answer = think(event)

    result = {
        "thought_at": now_iso(),
        "event": event,
        "answer": answer,
        "model": MODEL,
    }

    atomic_json(
        STATE / "last_patrol_thought.json",
        result,
    )

    IDEAS.mkdir(parents=True, exist_ok=True)
    day = datetime.now().astimezone().strftime("%Y-%m-%d")
    idea_file = IDEAS / f"{day}-patrol.md"

    with idea_file.open("a", encoding="utf-8") as f:
        f.write(
            f"\n## {now_iso()} 巡回中の気づき\n\n"
            f"{answer}\n"
        )

    done = QUEUE / "done"
    done.mkdir(parents=True, exist_ok=True)
    path.replace(done / path.name)

    log(f"done {path.name}")


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    QUEUE.mkdir(parents=True, exist_ok=True)

    lock = LOCK.open("w")

    try:
        fcntl.flock(
            lock.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        # 既存の思考プロセスがキューを処理する
        return

    while True:
        jobs = sorted(QUEUE.glob("*.json"))
        if not jobs:
            return

        path = jobs[0]

        try:
            process_event(path)
        except Exception as e:
            log(f"ERROR {path.name}: {e!r}")

            failed = QUEUE / "failed"
            failed.mkdir(parents=True, exist_ok=True)
            path.replace(failed / path.name)


if __name__ == "__main__":
    main()
