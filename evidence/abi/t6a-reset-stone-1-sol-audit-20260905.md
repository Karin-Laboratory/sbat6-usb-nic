# T6A RESET STONE 1 — Sol zero-based audit

日時: 2026-09-05 16:15 JST  
Solによる再監査の公開用要約。完全なprompt/responseやprivate runtime stateは公開しない。

```text
SOL_RESET_REVIEW_1=COMPLETE
CURRENT_CANDIDATE=NONE
LIVE_TEST_AUTHORIZED=no
SELECTED_ARCHITECTURE=B_VENDOR_SOURCE_LINEAGE
VALIDATION_STRATEGY=E_INCREMENTAL_MINIMAL_FUNCTION
CUSTOM_USB_NCM_COMPLETE=no
```

Solは候補label・static PASS・CRC一致を安全性の証明として採用しなかった。
`052318...` はlive-bannedを維持する。

## Reclassified conclusions

- `usb_function_instance` mismatchと初期ConfigFS fault、および修正後の狭い
  ConfigFS PASSは強い証拠。ただし全lifecycleの証明ではない。
- `dev_addr=0x318`、`dev=0x510`、private base `0x8c0` はartifactごとの
  codegenアンカーであり、全struct一致の証明ではない。
- vendor binaryのpaired callback store `netdev_ops/ethtool_ops = 0x1f8/0x200`
  は強いproducer evidence。ただしactive Imageの `register_netdevice+0xb4`
  命令としては、多点VA相関が未完了のため未証明。
- CRC、module_layout、vermagic、UND/versionはloader互換性を示すが、private
  struct、inline、macro、lifetime、callback semanticsを示さない。
- `052318...` の保存済み `modcrc.tsv` はvendor値と矛盾し、artifact単独での
  MODVERSIONS PASSは再現不能。候補は昇格対象外。

## Required next work

1. active boot slot、Image hash、kallsymsを一つのmanifestへ固定。
2. 複数runtime symbolをraw Imageの命令・文字列・call graphへ相関し、単一の
   VA/file mappingを証明する。失敗時はopcodeを採用しない。
3. vendor source lineageと `usb_net.ko` のallocation、callback、relocation、
   critical call orderを再構成する。
4. actual TUの全candidate direct accessを列挙し、unknown vendor offsetを
   paddingや推測値で埋めない。
5. source/TU/final-ELFの三重gateとloader gateを別々に通す。

再監査完了まで、rebuild・candidate promotion・T6A live load・UDC bindは行わない。
