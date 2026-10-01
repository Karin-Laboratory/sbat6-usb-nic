# 公開情報からの新規ドライバ再現（2026-10-01）

## 現在の結論

公開情報だけを使って、任意の新規ドライバを容易な手順で生成し、安全に
ロードできる状態には達していません。NCM **USBデバイス側**の実機成功は、
AX88179 **USBホスト側**や別のドライバのABI適合を保証しません。
T6Aでの結果を、kernel release文字列だけでT6Bへ適用することもできません。

このページは不足を再発見する作業を減らすための入口です。
既存バイナリのハッシュ確認、ビルド再現、構造ABIの確認、実機検証は別の結果です。

## 公開チェックアウトで実行できる最短手順

必要なものは Git、Python 3、GNU binutilsの `readelf`、`sha256sum` です。
ターゲット機への接続は不要です。

```sh
git clone https://github.com/Karin-Laboratory/sbat6-usb-nic.git
cd sbat6-usb-nic
git rev-parse HEAD
(cd artifacts && sha256sum -c SHA256SUMS)
(cd driver/t6a-ncm-canonical-v6/source && sha256sum -c SHA256SUMS)
(cd driver/t6a-ncm-65532-ntb-candidate-v1/source && sha256sum -c SHA256SUMS)
python3 tools/check-module-metadata.py \
  artifacts/t6a_usb_ncm_canonical_v6.ko \
  --symvers repro/t6a-vendor-Module.symvers > metadata.json
```

v6では76レコードの一致が期待されます。終了値0は `metadata_result=MATCH` の意味です。
結果の `load_authorization` は必ず `NOT_ESTABLISHED` です。
未知CRC、不一致、未version化の未定義symbolは終了値1、不正入力は2です。
これはLinux 5.4 ARM64の64-byte `modversion_info` 用です。他のABIへ自動推測しません。
検査は参照表の正当性、実機との対応、構造体、関数の意味、実行コードを証明しません。

任意の候補についても同じコマンドを使えます。新たに生成した依存moduleの
exportは、その同じビルドの `Module.symvers` を追加の `--symvers` に渡します。
同じsymbolのCRCが参照表間で衝突するとエラーになります。
候補から抽出したimport CRCを参照表に流用すると循環検証になるため禁止です。

## ビルド再現が止まる場所

`sh repro/build-65532.sh` は `KERNEL_SRC` 未指定で停止します。
これは設定例の書き忘れだけではありません。現在の公開物には次が不足しています。

| 必要な入力・証拠 | 現在の公開状態 | 補完すべきもの |
|---|---|---|
| 一致するkernel source/build tree | 外部パス指定を要求 | 取得可能な固定commitと完全なpatch series、またはvendorの正規取得先 |
| 対象configと生成環境 | 過去のhashやflagsを記録 | config本体、toolchain固定、生成コマンド、header/output hash検査 |
| vendor export CRC | 1,422行の表を同梱 | 対象Image由来の完全表と抽出器、Image hash・slotとの対応 |
| NCM公開sourceとbinaryの対応 | v1は実行code不一致（B2） | 固定入力から新たにビルドし、最終ELFを比較・再検証 |
| 新規driver固有の構造ABI | NCM固有の調査結果あり | 全直接アクセス、kernelが読むfield、callback、allocation、inline/nested accessの検証 |

`driver/patches/README.md` にもproduction patch未収録と明記されています。
upstream 5.4.238を置いただけでは、この不足を満たしません。
公開sourceとbinaryの対応は [B2報告](../REPRODUCIBILITY-STATUS-65532.md) が優先します。

## zzzzzさんの助言から再利用する方法

2026-09-05の保存済み外部報告では、`/proc/config.gz`、vendor moduleの逆解析、
`alloc_etherdev()` 直後のメモリ観測を突き合わせる方法が示されました。
`net_device` はupstream 5.4.238に `CONFIG_WIRELESS_EXT` の影響と
`dev_addr` 直前の未知32-byte領域を加えるモデルです。
2026-09-06のローカル独立コンパイル記録では次の9点が既知vendor値と一致しました。
これら外部報告・独立検証の要約を本ページで公開します。外部の生メモリや
完全な検証環境は本リポジトリには含まれないため、追試済みの公開証明とは扱いません。

| field / base | offset |
|---|---|
| name | 0x000 |
| netdev_ops | 0x1f8 |
| ethtool_ops | 0x200 |
| min_mtu / max_mtu | 0x22c / 0x230 |
| addr_assign_type | 0x25e |
| dev_addr | 0x318 |
| embedded dev | 0x510 |
| netdev_priv | 0x8c0 |

これはモデルの相関であり、未知領域の意味や任意のfieldを証明しません。
offsetを合わせるためだけのpadding追加は手順ではありません。
`struct module` の別モデルは独立照合2/4で未解決でした。
`module_layout` CRCを書き換えても、その問題は解消しません。

実装に使う工程は [自律検証手順](T6A_AUTONOMOUS_LOOP_V1.md) と
[最終codegen修正記録](../evidence/abi/t6a-netdev-priv-final-codegen-fix-20260905.md)
にあります。再利用時は次の順で証拠を残します。

1. 実機のactive slotとImage hash、config、vendor moduleを固定する。
2. 公開source、patch、toolchain、header、build outputをhash付きmanifestへ固定する。
3. driverと依存moduleの全アクセスを列挙し、vendor ELF・実機証拠に照合する。
4. 実際の翻訳単位に `sizeof` / `offsetof` のassertionを置く。
5. 生成された最終ELFのload/store、private base、callback、確保サイズ・順序を確認する。
6. 最終ELFの全import CRC、vermagic、依存moduleの対応を別途検査する。
7. 実機の管理・復旧経路を確認し、独立レビュー後に段階的にロード・認識・通信を検証する。

独立レビュー担当は特定のAI名に依存しません。既存の手順書の「Sol」は当時の担当名です。
検証対象は候補の完全SHAで識別します。未知の必須fieldが残ればロード段階へ進みません。

## AX88179での適用結果

T6B向けの過去のupstreamビルドは `mii → usbnet → ax88179_178a` の依存関係です。
`net_device` だけでなく、module loader、USB core、URB、SKB、queue、timer/workqueue、
callback table等、実際に横断する境界の確認が必要です。
公開NCM用CRC表にはMIIが使う一部のexportさえ存在せず、公開情報だけの追試は
メタデータの段階でも停止します。

今回の再監査以前に、ローカルImage由来のCRCへ書き換えたmoduleのロード試験で
管理接続が失われ、ユーザーの電源入れ直しが必要になりました。
クラッシュstackを取得できていないため原因の関数・構造体は未特定です。
これは安全性の失敗であり、CRC一致を安全性と扱わない具体的な反例として残します。
今回の公開手順再監査では再ロードしていません。

任意driverの生成を成立させるには、完全な対象vendor build環境の公開・取得が最も
再利用しやすい解決です。それが無い場合、driverごとの構造ABI補完が必要です。
本ページと検査器はその入口の補完であり、汎用の安全なdriver generatorの完成ではありません。
