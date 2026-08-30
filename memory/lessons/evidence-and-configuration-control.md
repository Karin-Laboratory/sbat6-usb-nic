# Evidence and configuration control

Zen3 GNSSの独立監査は実在するsender race等を発見した一方、repositoryの古いcopy、
raspi2のlive版、historical failure、現在実装を混同し、一部の現在版FAILを誤って
主張した。技術査読は報告全体をMIXEDとした。

再利用する原則:

- repository copy != live running version
- historical failure evidenceを現在版FAILへ自動転用しない
- liveへ到達できなければFAILでなくUNKNOWN
- 証拠は対象、版、時刻、収集状態を明示する
- implementation reportもaudit reportもauthorityではなくclaim
- claimはevidenceで検証する
- audit itself can be wrong

次回から注意力だけに依存せず、`runtime/evidence_control.py` と
`runtime/evidence_record.schema.json` を使い、target identity、freshness、claim validation、
system readiness、authorityを分離する。
