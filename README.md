# sbat6-usb-nic

SoftBank Air Terminal 6 / SBA6Dを、USB CDC-NCM gadgetとしてWindows/Linuxへ直結し、USB NICとして利用するための実機一次資料、再現手順、telemetry、kernel driver実験の記録です。

## Current status (2026-09-05)

The USB NCM driver investigation is still in progress. The `net_device` ABI is
substantially characterized and the USB function-instance path has live
evidence, but the vendor `struct module` / module-loader ABI is **not proven**.
There is currently no approved custom module and no live module test.

Vendor `__this_module` corpus observations:

```text
Linux 5.4.238 / aarch64 target
157 vendor modules scanned
156 valid .gnu.linkonce.this_module samples
sizeof-like section size  0x340
module name offset        0x18 (156/156)
init relocation           0x150
cleanup relocation        0x328
```

Upstream Linux 5.4.238 predicts `.this_module = 0x280`; a MediaTek Android
lineage candidate predicts `0x2c0` or otherwise has incompatible offsets.
Neither reproduces the T6A vendor ABI. Only two useful relocation anchors
were recovered, so the vendor-specific opaque regions remain unproven.

Runtime collection confirmed the `.gnu.linkonce.this_module` section address
for 157 loaded modules. BTF and `/proc/kcore` were unavailable, so raw runtime
`struct module` bytes could not be obtained.

The investigation is fail-closed: a candidate is not loaded merely because
size/init/cleanup happen to match. Live testing is allowed only after
independent ABI evidence converges. Therefore there is no guessed padding, ELF
patching, or live custom-module test at this checkpoint. See
[the current research status](docs/research/current-status.md) and the
[`struct module` ABI note](docs/research/struct-module-abi.md).

## Confirmed result

Vendor純正NCMの現在の実機baselineは次のとおりです。

```text
T6A → Windows
1.392 / 1.375 / 1.378 Gbit/s

Windows → T6A
1.01 / 1.01 / 1.01 Gbit/s

TCP Retr = 0
```

## Confirmed USB state

```text
mode=3
xHCI ABSENT
GPIO322 LOW
VBUS 0V
f5 -> ncm.gs8
UDC configured
current_speed=super-speed
ncm0 LOWER_UP
```

`mode=3`は、一般的なLinux enumからの推測ではなく、T6A実機のvendor mode nodeでDEVICE成功状態として確認した値です。

## Windows

```text
UsbNcm Host Device
UsbNcm.sys
VID:PID = 2C7C:7006
T6A     test-net.77.1/24
Windows test-net.77.2/24
```

## Repository policy

GitHubがこのプロジェクトのSystem of Recordです。成功、失敗、NO_IMPROVEMENT、rollback、未検証事項を同じ粒度で記録します。性能変更は原則として1 commit / 1 variableとし、commit・benchmark・evidence・rollbackを対応させます。

管理LANはUSB data planeと分離します。ADB、force rmmod、不可逆なeFuse/security設定は本プロジェクトの通常手順に含めません。

## Layout

- `docs/` — 再現手順、設計、Windows、recovery、安全方針
- `driver/` — observation candidateと将来のvendor-tree patch
- `telemetry/` — observation-only counter sinkと設計
- `scripts/` — activate/recover/audit/benchmark用の再現可能な補助
- `evidence/` — 実験・hardware・baselineの要約済み一次資料
- `known-non-working/` — 再使用禁止または効果なしの正式記録

## Status

The single current truth is [STATUS.md](STATUS.md). The project is at
`RESET_STONE_1_COMPLETE`: vendor lineage reconstruction plus staged minimal
implementation. No candidate is approved for live testing.

## Current evidence

The public summaries below are the authoritative route through the current
investigation. Sol prompt/response text, credentials, and private runtime
state are intentionally excluded.

- [function_instance ABI](candidate/20260905-mtk-fi-compat/ABI-REVIEW.md)
- [net_device static gate and mismatch](evidence/abi/t6a-net-device-static-gate-reaudit-20260905.md)
- [bbd228 exact ELF re-audit](evidence/abi/t6a-bbd228-exact-elf-provenance-reaudit-20260905.md)
- [netdev_priv final codegen audit](evidence/abi/t6a-netdev-priv-final-codegen-fix-20260905.md)
- [netdev_ops / register_netdevice analysis](evidence/abi/t6a-net-device-complete-reconstruction-20260905.md)
- [active Image text correlation](evidence/abi/t6a-actual-kernel-text-register-netdevice-20260905.md)
- [active kernel identity manifest](evidence/manifests/t6a-active-kernel-identity-20260905.json)
- [052318 live Oops](evidence/experiments/t6a-netdev-final-live-oops-20260905.md)
- [RESET STONE 1 Sol audit](evidence/abi/t6a-reset-stone-1-sol-audit-20260905.md)
- [autonomous loop v1](docs/T6A_AUTONOMOUS_LOOP_V1.md)

## License

Kernel/module source is GPL-2.0-only. Documentation and experiment records are CC BY 4.0 unless a file states otherwise. See `LICENSE`.
