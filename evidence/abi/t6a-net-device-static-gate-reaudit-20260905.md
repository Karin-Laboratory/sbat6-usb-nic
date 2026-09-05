# T6A net_device candidate static gate re-audit — 2026-09-05

## Scope

Offline only. No T6A connection, file transfer, module load, ConfigFS,
UDC bind, reboot, or live test was performed. The candidate source was not
semantically changed. `f_ncm.c` and `u_ether.c` are byte-identical to the
20260905 MTK compatibility candidate.

The rebuild used:

```text
vendor map: candidate/20260905-mtk-fi-compat/abi/vendor-kimage-extended.Module.symvers
vendor map SHA256: b259e638ada0a638c3b0142e1bb7ee604b9e5d718dd944615175f2c9d74a041a
telemetry map: ./research/t6a-ncm-telemetry/Module.symvers
isolated O=: .tmp-netdev-kernel-out-rebuild
vmlinux: absent from isolated O= during modpost
```

## Result

```text
rebuilt artifact SHA256 = c1f460614f5d198adc0b51818b5c20746054a6b4b697cd6b684cc4c23276e75c
actual UND total = 81
__versions total = 82
__versions minus module_layout = 81
actual import set equality = PASS
kernel CRC match = 74/74
telemetry CRC match = 7/7
module_layout = 0x3a3eb6e9
vermagic = PASS
```

The old raw equality test is not used. `aarch64-linux-gnu-nm -u` and
`readelf -Ws` agree on the final ELF UND set. The 81 imports classify as
74 kernel imports and 7 telemetry imports; the additional version record is
`module_layout`.

## ABI gates

The vendor layout probe matches all requested values (probe output is raw
size/offset plus one, hence 2241 = `0x8c0`, 793 = `0x318`, and 1297 =
`0x510`):

```text
net_device sizeof: 0x8c0
netdev_priv:       0x8c0
dev_addr:          0x318
struct device:     0x510
usb_function_instance: f +0xa0, set_inst_name +0xa8, free_func_inst +0xb0
```

The final ELF does not satisfy the codegen gate. Its
`gether_register_netdev` disassembly contains:

```text
1be8: ldr x1, [x0, #1296]   // struct device base 0x510: correct
1bf0: ldr x1, [x0, #744]    // dev_addr access 0x2e8: generic, not 0x318
1c04: str w3, [x1]
```

Therefore the compiler still generated the generic `net->dev_addr` offset.
The layout probe's target values are not sufficient proof that this final
ELF was compiled against the vendor `net_device` layout.

```text
[PASS] actual UND == versioned imports excluding module_layout
[PASS] all kernel imports CRC exact (74/74)
[PASS] all telemetry imports CRC exact (7/7)
[PASS] module_layout exact
[PASS] vermagic exact
[PASS] usb_function_instance MTK ABI
[PASS] net_device sizeof = 0x8c0 (probe)
[PASS] netdev_priv = 0x8c0 (probe)
[PASS] dev_addr = 0x318 (probe)
[PASS] struct device base = 0x510 (probe)
[FAIL] gether_register_netdev uses corrected dev_addr offset 0x318
[PASS] no source semantic change
```

No import symbol failed the presence/version/CRC checks, so there is no
failed-symbol table to enumerate. The failure is the final-ELF ABI codegen
gate, not an import-count or CRC failure.

```text
RESULT=FAIL
NET_DEVICE_ABI_GATE=FAIL
NEXT_LIVE_TEST_READY=no
LIVE_TEST=FORBIDDEN
```

The `CONFIG_WIRELESS_EXT` `+16` explanation remains an unconfirmed layout
reproduction element; no T6A vendor config confirmation is claimed. The
vendor-private 32 bytes remain an unknown layout-compatible region.

Evidence files:

```text
candidate/20260905-netdev-abi-compat/static/gate-result-v2.txt
candidate/20260905-netdev-abi-compat/static/rebuilt-gether-register-netdev.disasm
candidate/20260905-netdev-abi-compat/static/usb_f_ncm-rebuilt.mod.c
candidate/20260905-netdev-abi-compat/usb_f_ncm-netdev-abi-rebuilt.ko
```
