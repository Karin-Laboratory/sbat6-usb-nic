# sbat6-usb-nic

公開済みの SoftBank Air Terminal 6 / SBA6D 向け USB CDC-NCM gadget の再現資料です。対象は T6A の vendor Linux 5.4.238 / ARM64 です。

## まず読む場所

- [安全方針](docs/SAFETY.md)
- [65532 v1導入・ConfigFS・疎通](INSTALL-65532.md)
- [復旧とrollback](docs/RECOVERY.md)
- [性能と測定方向](docs/PERFORMANCE.md)
- [65532 v1 release notes](RELEASE-NOTES-65532.md)
- [65532 v1 reproducibility status](REPRODUCIBILITY-STATUS-65532.md)
- [ビルドと検証](driver/t6a-ncm-65532-ntb-candidate-v1/BUILD.md)

## v1の状態

v1 binary は実機で稼働・疎通・性能確認済みの asset として保持します。対応バイナリは [`artifacts/t6a_usb_ncm_65532_candidate_v1.ko`](artifacts/t6a_usb_ncm_65532_candidate_v1.ko)、SHA256 は `7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1` です。ただし clean build ELF の実行 code に差があるため、v1 は推奨版ではありません。

公開 source は provenance record として保持しますが、公開 binary との対応 source を断定しません。比較の根拠は [再現性ステータス](REPRODUCIBILITY-STATUS-65532.md) と [ELF比較証跡](evidence/reproducibility/v1-elf-comparison-20260907.md)を参照してください。

canonical v6 は再現 baseline として保持しています。v6 は 16 KiB NTB / 32 datagrams / 300 us、v1 は 65532-byte NTB / 64 datagrams / 80 us です。instrumented v5 は runtime 未検証の experimental であり、推奨インストール対象ではありません。

## 達成性能（測定方向を明記）

同一の T6A–Windows 構成での receiver throughput 平均です。T6A→Windows は P1 1.490、P4 1.580、P10 1.656 Gbit/s。Windows→T6A は P4 1.923、P10 1.982 Gbit/s。逆方向P1は不安定で0.893 Gbit/s平均でした。環境依存の測定値であり、他のkernel・hostでの保証値ではありません。

## Quick Start

1. 現在のmodule、ConfigFS、ネットワーク設定をバックアップする。
2. 物理または別経路の管理接続が維持できることを確認する。
3. 対応 kernel、vermagic、SHA256 を [release notes](RELEASE-NOTES-65532.md) と照合する。
4. [65532 v1導入手順](INSTALL-65532.md)に従い、read-only preflight後に手動gateを通してConfigFSを構成する。
5. UDCがconfiguredになり、対象インターフェースの疎通を確認する。

危険な force-unload、UDC driver操作、無条件の再起動、eFuse・Secure Boot・Flash Encryption操作は既定手順に含めません。

## 導入後の扱い

再起動後の自動復元はターゲット固有のinit/ConfigFS設定に依存します。自動復元を前提にせず、起動後にmodule、gadget、UDC、link、疎通を確認します。失敗時は[rollback/recovery](docs/RECOVERY.md)で保存済みのv6または元の構成へ戻します。まずWindows側を切断し、管理経路を確保してください。

## 既知の制約と研究状況

- vendor kernel 5.4.238 の内部ABIに依存し、generic Linuxでは動きません。
- moduleのABI、UDC、ConfigFS topology、USB speedが一致しない場合は導入しないでください。
- v1のP1 reverseは安定しておらず、性能差の原因を断定していません。
- v6は再現baseline、v1は実機検証済みだが source pairing 非断定の asset、v5は未検証実験版です。

## 成果物検証とライセンス

```sh
(cd artifacts && sha256sum -c SHA256SUMS)
(cd driver/t6a-ncm-65532-ntb-candidate-v1/source && sha256sum -c SHA256SUMS)
(cd driver/t6a-ncm-canonical-v6/source && sha256sum -c SHA256SUMS)
```

source/ と module は GPL-2.0-only。文書と実験記録は明記がない限り CC BY 4.0。詳細は [LICENSE](LICENSE) と [LICENSE-DOCS](LICENSE-DOCS) を参照。
