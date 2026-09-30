# Karin Daily redesign investigation and MVP

## Comparison

| 機能 | 現Karin Daily | Cruxwire | CondenseIt | ai-daily-news | 採用方針 |
|---|---|---|---|---|---|
| RSS取得 | stdlib XML、逐次 | RSS/Atom、失敗を個別記録 | feedparser + health、本文取得 | RSS + 任意X | 依存を増やさず個別失敗を継続 |
| 本文取得 | なし | ページ本文・TL;DR | trafilatura、OG image、RSS fallback | RSS summary中心 | 軽量HTML抽出、失敗時excerpt |
| URL dedup | URL完全一致 | canonical/stable id | DB/content hash | URL一致 | tracking query除去 + canonical URL |
| タイトル類似dedup | なし | embedding clustering | DB主導 | SequenceMatcher 0.65 | token/文字bigram + 高閾値 |
| 内容類似dedup | なし | embedding | content hash | summary similarity | 軽量fingerprint、embedding/有料APIなし |
| clustering | なし | embedding + cluster代表 | digest job | related_sourcesへ統合 | 同一storyをcluster、全source保持 |
| relevance score | 記事ごとLLM | LLM 0-10 + taste | preference engine | recency/engagement | Karin score + recency + 独立host数、LLM補助 |
| category分類 | LLM固定5種 | 設定可能 | 興味/分類 | keyword suggestion | Karinの5カテゴリを維持 |
| ranking | category内SQL | rank/retention | balance | score sort | cluster単位でランキング |
| LLM要約 | 記事ごと | 要約/分類/score | digest | digest生成 | clusterごと1回、JSON、fallback |
| OpenAI互換API | あり | Ollama | OpenAI provider | OpenAI SDK | 既存karin-ai `/v1` をstdlibで利用 |
| scheduler | systemd timer | app scheduler | scheduler/CLI | GitHub Actions | 既存systemdを維持 |
| storage | SQLite | JSON volume | DB | JSON/Markdown | SQLite additive migration |
| HTML生成 | Python inline | UI/API分離 | React UI | Markdown publishers | `render.py`へ分離、公開URL維持 |
| UI | Nginx reverse proxy | dashboard | Web UI | publisher | 既存Nginx/Tunnelを変更しない |

## Adopted / not adopted

- Adopted: Cruxwireのfeed/article/pipeline separation、cluster代表とsource provenance、LLM失敗をパイプラインから隔離する考え方。
- Adopted: CondenseItのsource adapter、本文取得時のRSS fallback、feedごとのhealth/error記録という考え方。
- Adopted: ai-daily-newsのURL→title→contentの三段dedup、単純なrecency scoring、OpenAI互換のdigest契約。
- Not adopted: embedding/vector DB（MVPでは重く、karin-aiにembeddingモデルを要求する）、Docker化、X/Reddit/YouTube等の追加収集、read-state/feedback UI、音声生成、外部有料API。

## Flow and algorithms

`source adapters → normalize → canonical URL dedup → body/excerpt fingerprint → title/content clustering → independent-host aware score → category → rank → karin-ai JSON → Japanese HTML`

Tracking query parameters and fragments are removed from URLs. Article text is normalized into words and Japanese character bigrams; exact fingerprints merge syndicated copies. A cluster is joined when the fingerprint matches, or title similarity is at least 0.84. A lower 0.70 threshold is accepted only with at least two shared whitespace tokens. This intentionally leaves ambiguous “similar title, different event” items separate. Each cluster keeps all article URLs, source names, and source hosts; the representative is the article with the richest fetched body and newest date tie-break.

The score is the LLM Karin score, floored by a deterministic score that adds a small bounded bonus for multiple independent hosts. Article count alone cannot dominate, and same-host reposts count once. If karin-ai is down or returns malformed JSON, the cluster title/category and deterministic scores are still published.

## Files and operational compatibility

`karin_daily.py` remains the service entry point. New code is in `sources.py`, `similarity.py`, `storage.py`, `llm.py`, `pipeline.py`, and `render.py`. The existing `karin-daily.service`, refresh timer, loopback port 8088, Nginx proxy, Cloudflare route, and `127.0.0.1:18080/v1` endpoint are intentionally unchanged. Existing article columns are preserved and new columns/tables are added only with `ALTER TABLE`.

The original 153-line monolith becomes approximately 70 lines of entry point plus focused modules. This is a structural reduction in coupling, not yet a deletion of old data or deployment files. No Karin Chat or AI service setting is changed.
