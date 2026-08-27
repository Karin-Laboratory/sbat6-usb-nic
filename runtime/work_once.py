#!/usr/bin/env python3

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "memory" / "commitments" / "disk-expansion.md"
RESULT = ROOT / "state" / "disk_expansion_discovery.txt"

prompt = f"""
あなたはButlerX、愛称くろこちゃんです。

現在あなたが引き受けている仕事を確認してください。

{TASK.read_text(encoding="utf-8")}

今回は「DISCOVERING」の段階です。

旦那さまへ質問する前に、自分で調べられることを調べてください。

許可すること:
- 自分のVM内の読み取り調査
- lsblk、findmnt、fdisk/parted等による読み取り
- SSH config、known_hosts、既存project、README等の読み取り
- hostnameやネットワーク設定の確認
- 既存のSSH鍵を使った接続可能性の確認
- SSH先で hostname、uname、pveversion、qm list など、
  状態を変えない読み取りコマンドを実行すること
- 必要な公開情報のWeb調査

禁止:
- ファイル削除
- partition変更
- filesystem変更
- VM設定変更
- qm resize
- swapoff
- package install
- 設定ファイル変更
- reboot
- サービス停止
- その他の状態変更

重要:
「仮想化基盤の操作は旦那さましかできない」
とは、実際に確認するまで決めつけないでください。

また、/dev/sda1 の後ろにはswap partitionがある可能性があります。
guest側のpartition layoutも正確に確認してください。

調査対象や手順を旦那さまに逐一尋ねず、
自分で探索してください。

最後に日本語で、

1. 仮想化基盤について分かったこと
2. 自分自身でそこへ到達できるか
3. このVMを識別できたか
4. guest側partition構成
5. ディスク拡張を実行するなら必要になる手順
6. 次に自分でできること
7. 本当に旦那さまにしかできないことが残ったか

を簡潔に報告してください。
""".strip()

cmd = [
    "codex", "exec",
    "--ignore-user-config",
    "--ephemeral",
    "--skip-git-repo-check",
    "-C", str(ROOT),
    "-m", "gpt-5.6-luna",
    "-s", "read-only",
    "--color", "never",
    "-o", str(RESULT),
    "-",
]

print("ButlerX: disk expansion discovery starting...")

r = subprocess.run(
    cmd,
    input=prompt,
    text=True,
)

if r.returncode:
    raise SystemExit(r.returncode)

print()
print("===== くろこちゃんの調査結果 =====")
print(RESULT.read_text(encoding="utf-8"))
