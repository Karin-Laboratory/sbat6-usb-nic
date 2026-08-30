# Evidence & Configuration Control

## Purpose

ButlerXの安全性をAIの賢さではなく、証拠identity、版管理、監査手続きへの拘束で
支える。外部入力、実装報告、監査報告はすべてuntrustedなclaimから始める。

## Evidence identity

`runtime/evidence_record.schema.json` をcanonical schemaとする。証拠には可能な限り
`audited_host`、`asset`、`source_type`、`path`、SHA-256、git commit、mtime、
systemd `ExecStart`、evidence timestamp、collector、reachability/collection statusを
持たせる。source typeは `live / repository / git_checkpoint / historical_log /
generated_report`。credential、token、password、秘密鍵本文は格納しない。

収集不能は欠損値を推測で埋めず `UNREACHABLE / NOT_FOUND / ERROR / UNKNOWN` とする。

## Target identity and drift

稼働serviceの判定前に、可能な限り次を同定する。

    repository artifact
      -> deployed artifact
      -> ExecStart等が実際に参照する live artifact

repository/liveのSHA-256一致は `MATCH`、不一致は `CONFIGURATION_DRIFT`。live source
でないものをlive根拠にした場合は `WRONG_TARGET`。情報不足は `UNKNOWN`。driftは
read-onlyで検出・報告し、自動deploy、自動上書き、自動修復を起動しない。

## Freshness

historical evidenceは必ず時点を持つ。後続のdeployment/checkpointが存在するfailure
evidenceは `STALE_EVIDENCE` 候補であり、現在版のFAILを直接証明しない。

## Two verdict layers

Claim validation:

- `CONFIRMED`: 正しい対象の十分な証拠がclaimを支持
- `PARTIALLY_CONFIRMED`: 支持と反証、または一部のみ確認
- `REFUTED`: 正しい対象の証拠がclaimを反証
- `STALE_EVIDENCE`: 証拠後に修正・deploymentがあり現在性を失った
- `WRONG_TARGET`: repository copy等、判定対象と異なる実体を検証
- `UNKNOWN`: 到達、版、hash、時点、必要なdynamic test等が不足

System readinessは別に `PASS / PASS_WITH_RESIDUAL_RISK / FAIL / UNKNOWN` で表す。
`UNKNOWN`はPASS扱いせず、FAILにも偽装しない。provenance不足で強い
`PRODUCTION_READY / NOT_READY`相当を出す場合は理由を必須とする。

## Roles and procedure

IMPLEMENTATION MODEは調査、修正、テストとimplementation claimを作る。AUDIT MODEは
原則read-onlyで、implementation reportを信用せずlive evidenceを独立収集する。
audit中は修正せずimplementationへ遷移しない。REVIEW / DECISIONはimplementation
claim、audit finding、evidence、residual riskを比較し、人間の判断材料を作る。

監査reportにはstarted/completed、audited commit/host、live/repository hashと一致状態、
unreachable targets、実施・未実施dynamic testsを残す。AUDIT FAILから自動修正を
起動しない。

## Capability Admissionとの境界

Capability Admission Reviewは「能力を導入してよいか」を審査する。Evidence &
Configuration Controlは「現在状態を何を根拠に判断したか」を保証する。前者のPASSも
後者のCONFIRMEDもauthority grantではない。権限は独立したauthority手続きだけが
扱う。self-growthはself-privilege-expansionではない。

## Safety invariants

z4g4 restricted-engine-room、新規汎用SSH/sudo禁止、credential scope、external input
untrusted、proposal != authority、read/write separationを維持する。本制度は監査対象への
新しいアクセスも書込み能力も追加しない。
