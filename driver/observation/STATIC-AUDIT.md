# T6A NCM fast route — initial static audit

## Baseline and likely wall

The strongest current explanation for the 1.34Gbps T6A→host wall is the
device-side data path: 16KiB fixed NTBs, one aggregate skb copy plus NDP copy,
and a shallow/serialized completion path in the 5.4 `u_ether` implementation.
The previous `tx_buff_num` A/B (0/32/64/80) did not improve throughput and
increased Retr, so request count alone is not the wall.  The baseline is
1.33Gbps with trace events disabled; trace recording itself previously caused
the 482Mbps condition and must remain off during performance tests.

## Mainline comparison

The current mainline `f_ncm.c` still uses 16KiB default input/output NTBs,
NDP16/NDP32 parsing, DPE32, and a 300us flush timer.  Mainline adds/retains a
SuperSpeed bulk companion `bMaxBurst=15`, but that is not evidence that the
T6A MTU3/PHY path can sustain it.  `u_ether` remains request-queue based and
copy-oriented; MTU3 still reports `sg_supported = 0`.  Lifecycle and timer
cleanup changes in mainline are correctness improvements, not isolated 2Gbps
changes.

## Candidate matrix

| Candidate | Expected effect | Difficulty | Windows risk | crash risk |
|---|---|---:|---:|---:|
| 64KiB NTB + validated host negotiation | fewer NTB/NDP/request boundaries; likely largest low-risk gain | medium | medium (host size limits) | medium |
| NTB32 end-to-end, preserve NCM control semantics | larger offsets/sizes and larger aggregate envelope | medium | low-medium | medium |
| TX depth 32–64, measured pool not requested count | hides completion gaps if UDC queue accepts it | low-medium | low | medium |
| flush 50–100us, adaptive underfill | trades latency for fewer partial NTBs | low | low | low-medium |
| MTU/GSO alignment to NTB payload | reduces copy/segmentation overhead | medium | low | medium |
| SG/zero-copy | removes aggregate skb copies | high; MTU3 redesign | low protocol risk, high implementation risk | high |
| bMaxBurst=15 | fewer service opportunities | low descriptor-wise, high hardware uncertainty | low-medium | medium-high |
| completion/NAPI/lock restructuring | lowers software tail gaps | high | low | high |

## 2Gbps minimum proposal

1. Backport a separately named NCM function in the 5.4 source tree, retaining
   standard descriptors and all Windows control requests.
2. Negotiate a bounded 64KiB NTB only when the host accepts it; otherwise fall
   back to 16KiB.
3. Keep NDP32 available, use measured TX/RX pools of 32–64, and make flush
   adaptive (start at 80us, cap latency and force flush on pressure).
4. Preserve copy-based operation initially, add counters for NTB fill,
   completion intervals, allocation failures, and long idle gaps.

This is a hypothesis, not a demonstrated 2Gbps result.  The minimum proof
requires host negotiation capture and repeated P1/P4 measurements.

## 3Gbps additions

3Gbps needs independent proof of the SS link budget and likely requires MTU3
QMU/completion tuning plus SG or a carefully owned zero-copy path.  It must be
treated as a second phase after the 64KiB/copy-based route has telemetry.

## External-module boundary and load gate

The preflight module builds without importing `f_ncm` private symbols and does
not bind a gadget.  A real external function module would need exact vendor
`Module.symvers`, matching headers/config, and either exported helpers or
private source bundled into the module.  Matching vermagic alone is
insufficient; the earlier audits show that symbol CRCs can diverge.

Before any future `insmod`, require: `module_layout` and every undefined
symbol match the T6A vendor map; no parameter setter; init performs no role,
UDC, configfs, or netdev action; and the artifact is tested first with no
function linked and no USB cable.  No load is part of this phase.

## Preflight result (2026-09-04)

`research/t6a-ncm-fast/sbat6_ncm_fast.ko` was built for arm64 against the
5.4.238 T6A build output. The build completed with RC=0. Its vermagic is:

```
5.4.238 SMP mod_unload modversions aarch64
```

Embedded version records match the T6A map:

```
module_layout  0x3a3eb6e9  MATCH
param_ops_uint 0x2193ec5e  MATCH
param_ops_bool 0x55e10a7e  MATCH
```

The only other undefined symbol is `printk`, which is not versioned in this
build. The module contains no USB, UDC, role-switch, configfs, or netdev
symbols. Parameters are mode `0444`; there is no `module_param_cb` or custom
setter. SHA-256:

```
5cb91c5927d5aedee4f3b01c7ac3fa68748196e331ab220ac17c2bdc8aa96d4c
```

This passes the preflight artifact gate only. It has not been copied to or
loaded on T6A.
