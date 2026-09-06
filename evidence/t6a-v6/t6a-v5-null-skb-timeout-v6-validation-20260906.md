# T6A v5 NULL-SKB timeout root cause and v6 validation

Date: 2026-09-06 (Asia/Tokyo)

## Root cause

The AArch64 ABI assigns the first two C arguments to `x0` and `x1`.
Therefore the `ndo_start_xmit(struct sk_buff *skb, struct net_device *net)`
entry is:

```text
x0 = skb
x1 = net_device
```

The v5 `eth_start_xmit` symbol begins at `0x35c`.  The pstore PC
`eth_start_xmit+0x294` is consequently `0x5f0`:

```text
0x368  add x21, x1, #0x8c0       // private eth_dev from net_device
0x370  mov x19, x1                // preserve net_device
0x374  mov x20, x0                // preserve entry skb (NULL on timeout)
...
0x5e4  ldr x0, [x19, #0x380]      // v5 obsolete net_device TX pointer
0x5e8  adrp x1, jiffies
0x5ec  ldr x2, [x1]
0x5f0  ldr x3, [x0, #0x88]        // exact faulting instruction
```

The fault VA `0x88` and pstore `x0=0` therefore prove:

```text
FAULT_BASE_REGISTER=x0
FAULT_FIELD_OFFSET=0x88
```

They do **not** prove a dereference of `skb + 0x88`: the incoming skb is
preserved in `x20`, while `x0` has been overwritten by the `net+0x380` load.
The fault is the old `net_device` TX pointer layout being used as though it
were the active `net_device->_tx` pointer.  The active/vendor layout is
`_tx=0x3c0`; its `netdev_queue::trans_start` is `0x88`.

```text
NCM_TIMEOUT_NULL_SKB_PATH=PROVEN
ETH_START_XMIT_FAULT_INSTRUCTION=ldr x3, [x0, #0x88] @ v5 0x5f0 (+0x294)
FAULT_BASE_REGISTER=x0
FAULT_FIELD_OFFSET=0x88
V5_ROOT_CAUSE=PROVEN: net+0x380 obsolete TX pointer -> NULL + netdev_queue trans_start
```

## Timeout and NULL-SKB path comparison

Vendor `usb_net` and Linux 5.4.238 `f_ncm.c` both implement the timeout as:

```c
if (!ncm->timer_stopping && ncm->skb_tx_data) {
        ncm->timer_force_tx = true;
        ncm->netdev->netdev_ops->ndo_start_xmit(NULL, ncm->netdev);
        ncm->timer_force_tx = false;
}
```

This is intentional flush behavior.  In `eth_start_xmit`, the NULL argument
is accepted through the initial filter checks and passed to `dev->wrap`.
`ncm_wrap_ntb` takes the `else if (ncm->skb_tx_data && timer_force_tx)` path,
calls `package_for_tx(ncm)`, and returns the completed NTB.  Thus the pending
NTB is submitted; a bare `if (!skb) return` would incorrectly suppress it.

On this path, incoming `skb` accesses are unreachable: `skb->data`,
`skb->len`, `skb_put*`, and `dev_consume_skb_any(skb)` occur only after a
non-NULL skb has entered the normal wrapping path.  The error cleanup also
guards the incoming skb before `dev_kfree_skb_any(skb)`.  The reachable
timeout flush operates on `ncm->skb_tx_data` / `skb_tx_ndp` and the USB request
queue, under the existing lock/endpoint state; no `skb_*`, `length/data/head/tail`,
or free operation on the NULL incoming skb is reachable.

## v5 -> v6 change

The only functional change is the TX timestamp access in `u_ether.c`:

```diff
-       netif_trans_update(net);
+       t6a_netif_trans_update(net);
```

The v6 helper derives the queue from the proven active layout:

```text
base = *(net + 0x3c0)
queue = base + index * 0x140
queue->trans_start = queue + 0x88
```

The v6 final ELF confirms `ldr x0, [x19, #0x3c0]` followed by the
`[x0, #0x88]` timestamp access, with no executable `#0x380` reference in
the final disassembly.  The timeout call remains NULL-SKB flush semantics.

## Validation

The v6 module was clean-built twice with the same Linux 5.4.238-ax88179
output/config, AArch64 cross compiler, and vendor symbol map:

```text
build 1 SHA256 = 8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799
build 2 SHA256 = 8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799
```

The final artifact described by this public baseline is:

```text
path=candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.ko
sha256=8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799
vermagic=5.4.238 SMP mod_unload modversions aarch64
```

```text
NULL_SKB_TIMEOUT_PATH_GATE=PASS
TX_DATAPATH_FINAL_ELF_GATE=PASS
UNCONTROLLED_TX_DATAPATH_ACCESS_COUNT=0
FINAL_ELF_VALIDATION=PASS
REPRODUCIBLE_BUILD=PASS
CUSTOM_NCM_V6_READY=yes
LIVE_TEST_READY=yes
LIVE_TEST=NOT_RUN
```

Existing queue compatibility remains independently recorded:

```text
_tx=0x3c0
num_tx_queues=0x3c8
real_num_tx_queues=0x3cc
stride=0x140
state=0x90
```

Evidence inputs: the retained v5 disassembly, the public v6 final
disassembly, the vendor comparison sources, and Linux 5.4.238
gadget-function sources. Private host paths are intentionally omitted.
