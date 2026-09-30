# Karin Daily

軽量な個人向けニュース一面。RSS/Atomを収集し、URL・タイトル・本文の軽量dedupとstory clusterを行い、cluster単位でkarin-aiに日本語要約させます。

```sh
python3 karin_daily.py --once
python3 karin_daily.py --serve --host 127.0.0.1 --port 8088
```

本番では `/opt/karin-daily` に配置し、`karin-daily.service` と `karin-daily.timer` を使用します。設定は環境変数または `config.json` で変更できます。

## 構造

- `sources.py`: RSS/Atom adapter、本文取得、本文取得失敗時のexcerpt fallback
- `similarity.py`: URL正規化、タイトル類似、content fingerprint
- `pipeline.py`: collect → normalize → dedup → cluster → score → digest
- `llm.py`: `127.0.0.1:18080/v1` OpenAI互換APIとJSON/fallback
- `storage.py`: 既存SQLiteへ追加カラム・clusterテーブルを加える互換migration
- `render.py`: 既存の日本語HTML表示

既存のsystemd、loopback 8088、Nginx、Cloudflare経路は変更しません。`ai_model` が空の場合は `/v1/models` から現在のモデル名を読み、取得できない場合のみ従来の既定名へfallbackします。
