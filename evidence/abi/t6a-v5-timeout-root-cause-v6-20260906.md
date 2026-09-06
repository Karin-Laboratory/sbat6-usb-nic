# T6A v5 TX-timeout root cause and v6 static gate — 2026-09-06

Offline analysis and reproducible build. No module load, ConfigFS mutation,
UDC bind, Windows test, traffic, or live retry was performed.

## Evidence identity

```text
PSTORE_SHA256=073963c94ab7ba30ca781cd5f48ca43cc1858dede9181af89e66e82dffb3f141
V5_SHA256=9c00e3d3517c14868cf0bf991c3a9cc4c5e2b5d5017def3da65fbe800736bd9f
VENDOR_USB_NET_SHA256=271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f
ACTIVE_IMAGE_SHA256=de3a1bee91314be0a65bd79f60a954d928f2c31cc4861d41f2e90b948d650082
KALLSYMS_SHA256=992040c1b0c8a94bf1b2eac4def82098219af9b77683712bfa74aa86bfb5ada1
```

The retained recovery record proves `pc=eth_start_xmit+0x294/0x2f8`,
`ncm_tx_timeout+0x3c/0x50`, and fault VA `0x88`. The raw v5 pstore payload is
not present in the workspace and the target was unreachable from this host
during a read-only retrieval attempt; therefore the crash-time register dump
cannot honestly be reproduced byte-for-byte. The register/dataflow proof below
uses the v5 final ELF plus two independent producer/consumer ABI paths.

## Instruction-level reconstruction

V5 `eth_start_xmit` begins at `0x35c`, so `+0x294 = 0x5f0`:

```asm
0x5e4  ldr x0, [x19, #0x380]     // v5's stale netdev_get_tx_queue base
0x5e8  adrp x1, jiffies
0x5ec  ldr x2, [x1]               // current jiffies
0x5f0  ldr x3, [x0, #0x88]        // fault: x0 == NULL, VA == 0x88
0x5f4  cmp x3, x2
0x5f8  b.eq 0x604
0x5fc  ldr x1, [x1]
0x600  str x1, [x0, #0x88]
```

This is the inline `netif_trans_update(net)` after successful
`usb_ep_queue()`. It is not a queue-state access and is not the v4
`netif_tx_wake_queue` failure.

The timeout function begins at `0x1f08` and the pstore `+0x3c` is `0x1f44`:

```asm
0x1f08  stp x29, x30, [sp, #-32]!
0x1f14  sub x19, x0, #0x190       // f_ncm from task_timer
0x1f18  ldrb w0, [x0, #0x40]      // timer_stopping
0x1f20  ldr x0, [x19, #0x178]     // skb_tx_data
0x1f28  ldr x1, [x19, #0x170]     // netdev
0x1f30  strb w0, [x19, #0x18a]     // timer_force_tx = true
0x1f34  ldr x0, [x1, #0x1f8]      // netdev_ops
0x1f38  ldr x2, [x0, #0x20]       // ndo_start_xmit
0x1f3c  mov x0, #0                 // NULL skb
0x1f40  blr x2
0x1f44  strb wzr, [x19, #0x18a]
```

The call trace is therefore:

```text
ncm_tx_timeout+0x3c
  -> netdev_ops[0x20].ndo_start_xmit(NULL, netdev)
  -> eth_start_xmit+0x294
  -> stale netdev _tx load at net+0x380 yields NULL
  -> netdev_queue::trans_start load at NULL+0x88
```

## Two-path ABI proof

1. Vendor `usb_net.ko` instruction-level cross-check: its corresponding
   transmit paths load the queue base from `[net,#0x3c0]`; the following
   `netdev_queue` transaction timestamp access is `[txq,#0x88]`.
2. Active Image producer/consumer evidence independently closes `_tx=0x3c0`
   and the queue consumer field `trans_start=0x88`; the saved source header
   defines `netif_trans_update()` as `netdev_get_tx_queue(dev,0)` followed by
   `txq->trans_start`.

Thus the NULL-plus-field interpretation is proven:

```text
NULL_BASE=netdev_get_tx_queue(net,0) result caused by stale net+0x380
FIELD_OFFSET=0x88
FIELD=struct netdev_queue::trans_start
WATCHDOG_TIMER_FIELD=not the faulting field
```

## Timeout-path inventory

| object | field / operation | v5 codegen or TU location | disposition |
|---|---|---|---|
| `f_ncm` | `task_timer` container offset `0x190` | `sub x19,x0,#0x190` | proven TU/ELF |
| `f_ncm` | `timer_stopping` | `+0x40` byte load | proven TU/ELF |
| `f_ncm` | `skb_tx_data` | `+0x178` pointer load | proven TU/ELF |
| `f_ncm` | `netdev` | `+0x170` pointer load | proven TU/ELF |
| `f_ncm` | `timer_force_tx` | `+0x18a` byte store/clear | proven TU/ELF |
| `net_device` | `netdev_ops` | `+0x1f8` | active/vendor proven |
| `net_device` | `_tx` queue base | v5 bad `+0x380`; v6 `+0x3c0` | root cause/fix proven |
| `netdev_queue` | `trans_start` | `+0x88` | vendor + header cross-check |
| `eth_dev` | `lock`, `port_usb` | private `+0x0`, `+0x8` | TU/final ELF audited |
| `gether` | `in_ep`, `cdc_filter` | `+0xe0`, `+0xf2` | TU/final ELF audited |
| `eth_dev` | `req_lock`, `tx_reqs` | private `+0x20`, `+0x28` | TU/final ELF audited |
| `usb_request` | list/buf/context/complete/zero/length | request accesses in xmit | TU/final ELF audited |
| `gether` | `is_fixed`, `fixed_in_len`, `supports_multi_frame` | `+0xf8`, `+0x100`, `+0x104` | TU/final ELF audited |
| `eth_dev` | `wrap`, `stats`, `tx_qlen` | private `+0x70`, module-private stats, atomic | stats isolated; no native netdev stats |
| watchdog | `watchdog_timeo`, `watchdog_timer` | no access on fault path | not implicated; not invented |
| work/timer | `eth_dev.work`, `f_ncm.task_timer` | work is separate RX path; hrtimer enters timeout | audited, no uncontrolled TX layout access |

## v6 final ELF

The v6 fix replaces every queue helper and `netif_trans_update()` with audited
opaque accessors. The relevant final instructions are:

```asm
0x5e4  ldr x0, [x19, #0x3c0]
0x5f0  ldr x3, [x0, #0x88]
0x600  str x1, [x0, #0x88]
```

No `net+0x380` load remains in the actual v6 ELF; queue operations also use
the same `+0x3c0` boundary before calling `netif_tx_*_queue()`.

```text
V5_TX_TIMEOUT_ROOT_CAUSE=PROVEN
UNCONTROLLED_TX_DATAPATH_ACCESS_COUNT=0
TX_DATAPATH_FINAL_ELF_GATE=PASS
NET_DEVICE_FINAL_ELF_GATE=PASS (inherited opaque-ABI 9/9 match, rechecked)
NESTED_DIRECT_ACCESS_AUDIT=PASS
STRUCT_MODULE_FINAL_GATE=PASS
MODVERSION_GATE=PASS (76/76 overlap, mismatch 0, missing 0)
VERMAGIC_GATE=PASS (5.4.238 SMP mod_unload modversions aarch64)
REPRODUCIBLE_BUILD=PASS (two identical builds)
CUSTOM_NCM_V6_SHA256=12c3f21ce5f387d0d5c21e42d3e3ca0ee8b9840d09c93a45caa66a6223c80212
CUSTOM_NCM_V6_READY=yes
FINAL_ELF_VALIDATION=PASS
LIVE_TEST_READY=yes
LIVE_TEST=NOT_RUN_BY_INSTRUCTION
```

V5 is recorded as: USB configured, custom UDC bound, netdev created, and TX
datapath/timeout reached, with first packet failed and spontaneous reboot.
