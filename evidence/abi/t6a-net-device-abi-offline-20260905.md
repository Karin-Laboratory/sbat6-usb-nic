# T6A `struct net_device` ABI offline investigation — 2026-09-05

## Scope and safety

This investigation is offline only. No candidate was inserted into T6A, no
UDC bind was attempted, and no Windows connection was made.

## Oops and exact fault

Candidate artifact:

`candidate/20260905-mtk-fi-compat/artifacts/usb_f_ncm-extended.ko`

SHA256: `1fb49fd6cf347e2676327d92a22808ee0d767792dcbc52261d2d41b81b0afc06`

At `gether_register_netdev+0x2c`, the candidate instruction is:

```text
1c04: b9000023  str w3, [x1]
```

The preceding instructions are:

```text
1be8: ldr x1, [x0, #1296]
1bec: cbz x1, 1c5c
1bf0: ldr x1, [x0, #744]
1bf4: mov x19, x0
1bf8: ldrh w2, [x0, #2356]
1bfc: add x22, x0, #0x930
1c00: ldr w3, [x0, #2352]
1c04: str w3, [x1]
1c08: strh w2, [x1, #4]
```

The pstore register dump has `x0=ffffff805d9ee000` and `x1=0`, with
`WnR=1` and fault address zero. Therefore `net` is non-NULL and the fault is
the write through a NULL `net->dev_addr` pointer. It is not the
`net->dev.parent` check and not `dev->gadget`.

The source mapping is `u_ether.c:965`, the first operation of:

```c
memcpy(net->dev_addr, dev->dev_mac, ETH_ALEN);
```

This is exact proof of the faulting operation, while the ABI mismatch remains
the root-cause classification until the vendor layout is fully reproduced.

## Generic 5.4.238 probe

The probe was compiled against the candidate build headers. `NETDEV_ALIGN` is
32 and `netdev_priv()` is `net + ALIGN(sizeof(struct net_device), 32)`.

| member | generic offset |
|---|---:|
| `sizeof(struct net_device)` | `0x880` (2176) |
| `features` | `0x0d0` |
| `flags` | `0x208` |
| `mtu` | `0x218` |
| `addr_assign_type` | `0x24e` |
| `dev` | `0x4d0` |
| `ethtool_ops` | `0x1f0` |
| `netdev_ops` | `0x1e8` |
| `dev_addr` | `0x2e8` |
| `netdev_priv` offset | `0x880` |

With `CONFIG_WIRELESS_EXT` forced in an isolated probe, the symbol contributes
16 bytes to the post-wireless fields (`netdev_ops`, `ethtool_ops`, flags,
mtu, addr_assign_type, and dev_addr), but the overall size remains `0x880`
because tail padding absorbs the displacement.

## Vendor ELF evidence

Vendor artifact:

`candidate/20260905-mtk-fi-compat/vendor/usb_net.ko`

SHA256: `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f`

The unstripped vendor ELF gives these direct facts:

| operation | vendor instruction/evidence |
|---|---:|
| `gether_set_gadget`: store gadget | `net + 0x8d8` |
| `gether_set_gadget`: store `net->dev.parent` | `net + 0x550` |
| `gether_register_netdev`: parent check | load `net + 0x550` |
| `gether_setup_name_default`: `alloc_etherdev_mqs` private size | `0x298` |
| vendor `netdev_priv` start | `net + 0x8c0` |
| vendor `gether_register_netdev` | `gether_register_netdev+0x0` at `.text+0x714` |

The generic parent field is at `net + 0x510` (struct device base `0x4d0` plus
parent offset `0x40`); vendor is `0x550`, exactly +64. Vendor private data
starts at `0x8c0`, versus generic `0x880`, also +64. The vendor register path
does not directly dereference `net->dev_addr`; it calls `dev_set_mac_address`
using its private `dev_mac` at `net + 0xa7f`. Thus vendor `dev_addr` is an
inferred, not directly observed, field offset.

The coherent layout model is:

| member | generic | T6A vendor model | displacement |
|---|---:|---:|---:|
| `netdev_ops` | `0x1e8` | `0x218` | +48 |
| `ethtool_ops` | `0x1f0` | `0x220` | +48 |
| `dev_addr` | `0x2e8` | `0x318` | +48 (inferred) |
| `dev` | `0x4d0` | `0x510` | +64 (directly inferred from parent) |
| `netdev_priv` | `0x880` | `0x8c0` | +64 (direct) |
| `sizeof(net_device)` | `0x880` | `0x8c0` | +64 (layout model) |

An isolated header probe with `CONFIG_WIRELESS_EXT` (+16) and an explicitly
named `T6A vendor private 32-byte region` before `netdev_ops` produces exactly
`sizeof=0x8c0`, `netdev_priv=0x8c0`, `dev_addr=0x318`, `netdev_ops=0x218`, and
`dev=0x510`. This is a reproducible compatibility model, not a claim that
the vendor's private field names have been recovered.

## Config and hypothesis classification

The preserved candidate/kernel `.config` has no `CONFIG_WIRELESS_EXT=y` and no
saved T6A `/proc/config.gz` or config hash is present in this workspace.
`CONFIG_HW_NAT` is likewise not independently present in the saved config
evidence. Therefore the statement that T6A enabled WEXT is **NOT_CONFIRMED**;
the +16 contribution is compiler-probe confirmed as a mechanism.

The zzz hypothesis is **PARTIALLY_CONFIRMED**: +16 WEXT and a 32-byte isolated
vendor region reproduce the observed +48 early-field displacement, while the
vendor ELF independently proves a +64 later-field/priv displacement. The
semantic identity and exact `dev_addr` vendor access are not directly proven.
The `dev_addr`-immediately-before-private-region claim is **NOT_CONFIRMED**.

## Compatibility candidate

An offline header-level candidate was built from an isolated kernel-source
view. It enables the WEXT layout branch and adds only the explicitly named
`T6A vendor private 32-byte region`; no upstream source tree was changed and
no offset hack was added to `u_ether.c`.

Artifact:

`candidate/20260905-netdev-abi-compat/usb_f_ncm-netdev-abi.ko`

SHA256: `54f5039d3497d28d9af20429564ee478f1410fc1e7a9eec69f2aec08e992434c`

Its `gether_register_netdev` disassembly uses parent `0x550`, dev_addr
`0x318`, and source `dev_mac` `0x970` (the latter moves with the enlarged
`eth_dev`/candidate source layout). It is audit-only.

## Gates and readiness

The candidate code compiles, but the static ABI gate is **FAIL**: final ELF
audit reports 81 undefined symbols and 82 generated version lines (actual
import/version coverage is not exact), so the mandatory 74/74 kernel CRC gate
is not met. Telemetry CRC exactness was not promoted to PASS for this new
diagnostic artifact. No evidence supports claiming `module_layout exact` for
this candidate gate. The existing MTK function-instance compatibility,
telemetry, and vermagic results belong to the prior candidate and are not
silently reused here.

```text
NET_DEVICE_ABI_GATE=FAIL
NEXT_LIVE_TEST_READY=no
ROOT_CAUSE=NET_DEVICE_ABI_MISMATCH (leading, exact fault proven; full vendor layout not final-proof)
LIVE_TEST=FORBIDDEN
```

No GitHub commit has been created yet for this offline investigation.
