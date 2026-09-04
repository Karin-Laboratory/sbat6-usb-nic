# sbat6-usb-nic

SoftBank Air Terminal 6 / SBA6Dを、USB CDC-NCM gadgetとしてWindows/Linuxへ直結し、USB NICとして利用するための実機一次資料、再現手順、telemetry、kernel driver実験の記録です。

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

管理LAN（`test-net.3.0/24`）はUSB data planeと分離します。ADB、force rmmod、不可逆なeFuse/security設定は本プロジェクトの通常手順に含めません。

## Layout

- `docs/` — 再現手順、設計、Windows、recovery、安全方針
- `driver/` — observation candidateと将来のvendor-tree patch
- `telemetry/` — observation-only counter sinkと設計
- `scripts/` — activate/recover/audit/benchmark用の再現可能な補助
- `evidence/` — 実験・hardware・baselineの要約済み一次資料
- `known-non-working/` — 再使用禁止または効果なしの正式記録

## Status

Telemetry sinkはsourceから再ビルド可能なcandidateですが、vendor NCM data pathへの統合は未完了です。2026-09-04のcandidate ConfigFS再構成では管理経路を失い、Windows再列挙・iperf・telemetry測定は未実施でした。詳細は`evidence/experiments/`を参照してください。

## License

Kernel/module source is GPL-2.0-only. Documentation and experiment records are CC BY 4.0 unless a file states otherwise. See `LICENSE`.
