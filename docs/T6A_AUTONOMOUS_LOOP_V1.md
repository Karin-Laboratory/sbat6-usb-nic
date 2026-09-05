# T6A autonomous research loop v1

RESET STONE 1でSolが提案した運用契約。candidate labelは証拠の代用にしない。

## Gates

0. final `.ko` SHA、source/header/config、preprocessed TU、`.cmd`、object、
   mod.c、link command、vendor baseline hashを同一manifestへ固定。
1. vendor lineageのfunction boundary、allocation、callback、relocation、
   critical call graphを再構成。
2. boot slot/Image hashと、多点相関によるactive VA-to-Image mappingを証明。
3. candidate direct accessとkernel-consumed fieldsを分離して全列挙。
4. standalone probeではなくactual TUのassertionで確認。
5. exact final SHAのdisassemblyで全load/store、private-base、allocation、
   callback、critical orderを確認。旧offsetがexecutable sectionにあればFAIL。
6. UND/version、CRC、module_layout、vermagicを構造ABIとは別gateで確認。
7. SolがGates 0–6を独立再監査し、変更点・予測結果・rollbackを明記。

## Live ladder

Windows disconnectedのまま、read-only baseline → hash確認 → owner/refcount確認 →
candidate load → single ConfigFS instance → attribute readback → link lifecycle →
isolated UDC bindの順とする。各段階でpersistent marker、management continuity、
clean logを要求する。fault後の同条件retryは禁止。UDC bind成功後もSolの第三回
監査を通るまでWindowsへ進まない。

## Stop/recovery/escalation

hash/provenance mismatch、unknown required offset、missing evidence、unexpected
owner/refcount、management loss、warning/Oops、UDC timeout、pstore変化、reboot、
descriptor異常で即停止。force unloadはせず、既知のvendor recoveryのみを使い、
pstoreとcandidate SHAを保存してSolへ再投入する。

Sol escalationはcandidate promotion、unknown ABI field、kernel fault、milestone
successで必須。候補名はfull SHAで、promoted artifactは上書きしない。

