# T6A bbd228 exact ELF provenance re-audit — 2026-09-05

## Scope and safety

Offline-only audit. No rebuild, relink, candidate creation, module load,
UDC operation, live test, `/proc/kcore` analysis, or T6A access was performed.
The SHA256-matched existing `.ko` files were read only.

## Exact artifact identity

```text
BBD228_ARTIFACT_FOUND=yes
BBD228_SHA256=bbd228debf2c49a55a68729b1a09eff3e8bba34bb6bb0cb7c085b0158ae88e3c
BBD228_SIZE=811680
BBD228_MTIME=2026-09-05 09:37:24.360449019 +0900
```

Matching copies found (all byte-identical by SHA256):

```text
/home/masataka/projects/sbat6-usb-nic/candidate/20260905-module-layout-provenance-v2/source/usb_f_ncm.ko
/home/masataka/projects/sbat6-usb-nic/candidate/20260905-module-layout-provenance-v2/usb_f_ncm.ko
/home/masataka/projects/sbat6-usb-nic/evidence/butlerx-live-evidence-20260905/staging/usb_f_ncm.ko
```

The canonical audit path is the candidate-root copy:
`candidate/20260905-module-layout-provenance-v2/usb_f_ncm.ko`.

## Static gate raw output

The earlier `static-gate.log` was not accepted as final evidence: it used a
stale import parser and reported false failures for symbol/version formatting.
The gate was rerun read-only against the exact ELF and its existing generated
`source/usb_f_ncm.mod.c`; no build action was used.

```text
[PASS] exact ELF exists and SHA256 matches
[PASS] aarch64 nm -u and readelf -Ws UND sets agree (81)
[PASS] __versions contains module_layout (82 records total)
[PASS] actual UND == __versions excluding module_layout (81 == 81)
[PASS] kernel import CRCs match vendor recovered map (74/74)
[PASS] telemetry import CRCs match telemetry map (7/7)
[PASS] module_layout = 0x3a3eb6e9
[PASS] vermagic = 5.4.238 SMP mod_unload modversions aarch64
[PASS] usb_function_instance compatibility assertions: f +0xa0,
       set_inst_name +0xa8, free_func_inst +0xb0
[PASS] final ELF gether_register_netdev dev_addr codegen = 0x318
[PASS] final ELF gether_register_netdev parent codegen = 0x510
BBD228_STATIC_GATE_RESULT=PASS
```

The CRC audit is supporting evidence only; it does not prove the full
`struct net_device` layout.

## Exact final ELF disassembly

Symbol start is `0x1bd8`; the function returns at `0x1c54`.

```text
0000000000001bd8 <gether_register_netdev>:
    1bd8: a9bd7bfd stp x29, x30, [sp, #-48]!
    1bdc: 910003fd mov x29, sp
    1be0: a90153f3 stp x19, x20, [sp, #16]
    1be4: a9025bf5 stp x21, x22, [sp, #32]
    1be8: f9428801 ldr x1, [x0, #1296]
    1bec: b4000361 cbz x1, 1c58 <gether_register_netdev+0x80>
    1bf0: 79526801 ldrh w1, [x0, #2356]
    1bf4: aa0003f3 mov x19, x0
    1bf8: b9493002 ldr w2, [x0, #2352]
    1bfc: 9124c016 add x22, x0, #0x930
    1c00: b9031802 str w2, [x0, #792]
    1c04: 79063801 strh w1, [x0, #796]
    1c08: 94000000 bl 0 <register_netdev>
    1c0c: 2a0003f4 mov w20, w0
    1c10: 37f801a0 tbnz w0, #31, 1c44 <gether_register_netdev+0x6c>
    1c14: f9444a61 ldr x1, [x19, #2192]
    1c18: 9124aa62 add x2, x19, #0x92a
    1c1c: adrp x0, .rodata.str1.1+0x15f
    1c20: add x0, x0, #0
    1c24: bl 0 <printk>
    1c28: f9444a61 ldr x1, [x19, #2192]
    1c2c: aa1603e2 mov x2, x22
    1c30: adrp x0, .rodata.str1.1+0x173
    1c34: add x0, x0, #0
    1c38: bl 0 <printk>
    1c3c: aa1303e0 mov x0, x19
    1c40: bl 0 <netif_carrier_off>
    1c44: 2a1403e0 mov w0, w20
    1c48: a94153f3 ldp x19, x20, [sp, #16]
    1c4c: a9425bf5 ldp x21, x22, [sp, #32]
    1c50: a8c37bfd ldp x29, x30, [sp], #48
    1c54: d65f03c0 ret
    1c58: 128002b4 mov w20, #0xffffffea
    1c5c: 17fffffa b 1c44 <gether_register_netdev+0x6c>
```

Interpretation:

| Operation | Exact evidence | Meaning |
|---|---|---|
| `net->dev.parent` | `ldr x1,[x0,#1296]` | `0x510`; parent check is vendor-targeted |
| `netdev_priv/private` | no separate load; source is folded into absolute accesses | must be checked from all ELF codegen, not source only |
| `dev_mac` source | `ldr w2,[x0,#0x930]`, `ldrh w1,[x0,#0x934]` | six-byte source load at absolute `0x930..0x935` |
| `net->dev_addr` destination | `str w2,[x0,#0x318]`, `strh w1,[x0,#0x31c]` | six-byte destination at `0x318..0x31d`; PASS |
| register call | `bl register_netdev` | actual imported vendor call |
| carrier state | `bl netif_carrier_off` | post-registration path |

```text
BBD228_DEV_ADDR_PROBE=0x318 (raw probe value 793)
BBD228_FINAL_ELF_DEV_ADDR_OFFSET=0x318
BBD228_FINAL_ELF_DEV_ADDR_GATE=PASS
```

## 0x318 versus 0x2e8 and provenance resolution

The public `d0b0ce3` rebuilt artifact (`c1f460...`) contains
`ldr x1,[x0,#744]`, i.e. `0x2e8`, despite its probe reporting `0x318`.
The exact bbd228 artifact instead contains stores to `0x318` and `0x31c`.
Therefore the direct contradiction about `dev_addr` is resolved as a
build/artifact-generation difference:

```text
d0b0ce3 rebuilt ELF: 0x2e8 -> codegen FAIL
bbd228 exact ELF:    0x318 -> codegen PASS
D0B0CE3_CONTRADICTION_RESOLVED=yes
```

This proves bbd228 is later/provenance-fixed for the `dev_addr` operation only.
It does not prove the whole candidate is vendor-layout-safe.

## `dev_mac` / private layout

The existing vendor layout probe records:

```text
BBD228_NETDEV_PRIV_OFFSET=0x8c0 (raw probe 2241)
BBD228_ETH_DEV_DEV_MAC_OFFSET=0xb0 (DWARF/source layout of exact input object)
BBD228_ABSOLUTE_DEV_MAC_OFFSET=0x930 in final ELF
```

The exact input object's DWARF gives `sizeof(struct eth_dev)=0xb8` and
`offsetof(dev_mac)=0xb0`. The final ELF emits `net + 0x930`, which is
`0x880 + 0xb0`, not `0x8c0 + 0x70`. The ELF also emits multiple explicit
`net + 0x880` private-base accesses elsewhere. Thus the exact artifact has a
split result: explicit `dev_addr` is corrected, while ordinary `netdev_priv()`
codegen remains generic (`0x880`).

```text
BBD228_FINAL_ELF_DEV_MAC_ACCESS=absolute net+0x930; consistent with generic
                              netdev_priv 0x880 + eth_dev.dev_mac 0xb0
```

The `+0x930/+0x934` pair is therefore a six-byte `dev_mac` load, not an
unknown `net_device` field. It is source-compatible with `dev->dev_mac`, but
not proof of vendor private-base compatibility.

## Direct-access inventory

The actual linked translation units are `u_ether.c` and `f_ncm.c`.

```text
NET_DEVICE_DIRECT_ACCESS:
  u_ether.c: net->name, net->stats.*, net->addr_assign_type,
             net->netdev_ops, net->ethtool_ops, net->min_mtu, net->max_mtu,
             net->dev.parent (via SET_NETDEV_DEV), explicit dev_addr helper
  f_ncm.c:   ncm->netdev->stats.tx_dropped,
             ncm->netdev->netdev_ops->ndo_start_xmit

ETH_DEV_DIRECT_ACCESS:
  u_ether.c: dev->net, gadget, lock/req_lock, request lists, tx_qlen,
             rx_frames, qmult, header_len, wrap/unwrap, work, todo, zlp,
             no_skb_reserve, host_mac, dev_mac, port_usb

INLINE_OR_MACRO_ACCESS:
  netdev_priv(net); sbat6_net_dev_addr(net); SET_NETDEV_DEV(net,...);
  SET_NETDEV_DEVTYPE(net,...); netif_* and net_device stats/macros

VENDOR_KERNEL_FUNCTION_ONLY_ACCESS:
  register_netdev, free_netdev, unregister_netdev, netif_carrier_off,
  alloc_etherdev_mqs (candidate imports; internal fields are vendor-owned)
```

The source includes compile-time assertions for the explicit net-device
compatibility model and function-instance offsets. However, the final ELF
evidence shows the private-base direct accesses were not equivalently fixed.

```text
DIRECT_ACCESS_ABI_AUDIT=FAIL
```

## MODVERSIONS net_device-related imports

Only symbols actually imported by the exact ELF are listed. `alloc_netdev_mqs`
is not imported; the equivalent actual import is `alloc_etherdev_mqs`.

| Symbol | Candidate CRC | Vendor recovered CRC | Result |
|---|---:|---:|---|
| `register_netdev` | `0xe17e26a0` | `0xe17e26a0` | MATCH |
| `alloc_etherdev_mqs` | `0x224a0869` | `0x224a0869` | MATCH |
| `free_netdev` | `0x216fb39a` | `0x216fb39a` | MATCH |
| `netif_carrier_off` | `0x850b4108` | `0x850b4108` | MATCH |
| `unregister_netdev` | `0x2594d818` | `0x2594d818` | MATCH |

```text
NETDEV_RELATED_CRC_AUDIT=PASS (5/5 actual related imports; all kernel imports 74/74)
```

CRC equality is supporting evidence only and does not prove a complete
`struct net_device` layout.

## Live-fault interpretation and status correction

The retained pstore/live record is a NULL dereference reported at
`gether_register_netdev+0x2c/0x8c` for bbd228. The exact ELF now proves that
the preceding MAC copy targets `0x318`; it does not provide the vendor
`register_netdevice+0xb4` text or prove the fault's field/data flow.

```text
latest live fault: gether_register_netdev+0x2c/0x8c NULL dereference (pstore)
fault provenance: unproven; not established as register_netdevice deep fault
REGISTER_NETDEVICE_DEEP_FAULT_INTERPRETATION=unproven
```

Consequently, the prior statements that `NET_DEVICE_ABI_FIX_LIVE_CONFIRMED`
or that `register_netdevice+0xb4` is a post-dev_addr deep fault are withdrawn.

## Final verdict

```text
BBD228_ARTIFACT_FOUND=yes
BBD228_SHA256=bbd228debf2c49a55a68729b1a09eff3e8bba34bb6bb0cb7c085b0158ae88e3c
BBD228_STATIC_GATE_RESULT=PASS
BBD228_DEV_ADDR_PROBE=0x318
BBD228_FINAL_ELF_DEV_ADDR_OFFSET=0x318
BBD228_FINAL_ELF_DEV_ADDR_GATE=PASS
BBD228_ETH_DEV_DEV_MAC_OFFSET=0xb0
DIRECT_ACCESS_ABI_AUDIT=FAIL
NETDEV_RELATED_CRC_AUDIT=PASS
D0B0CE3_CONTRADICTION_RESOLVED=yes
REGISTER_NETDEVICE_DEEP_FAULT_INTERPRETATION=unproven
NEXT_OFFLINE_ACTION=repair and prove netdev_priv/private codegen for all direct accesses, then rerun exact-ELF audit
NEXT_LIVE_TEST_READY=no
```
