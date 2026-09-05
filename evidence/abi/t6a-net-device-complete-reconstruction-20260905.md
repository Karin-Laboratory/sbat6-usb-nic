# T6A `struct net_device` complete ABI reconstruction — 2026-09-05

## Decision

```text
KNOWN_STATIC_GATES=PASS
NET_DEVICE_LAYOUT_RECONSTRUCTION=FAIL (incomplete)
DIRECT_ACCESS_ABI_AUDIT=FAIL (incomplete)
NEW_CANDIDATE_SHA256=
SOL_LIVE_TEST_READY=no
LIVE_TEST=FORBIDDEN
```

Candidate `052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f`
is permanently live-banned. No module load, UDC operation, reboot, or
candidate rebuild was performed by this audit.

## Sol record

以下はSol監査の公開用要約である。完全なprompt/response、session ID、request
recordなどのprivate runtime stateは公開しない。

```text
SOL_INVOCATION_ID=t6a-new-register-netdevice-oops-audit-20260905
SOL_DIAGNOSIS=register_netdevice+0xb0 loads [net+0x1f8]; +0xb4 dereferences it; candidate left that slot NULL
SOL_LIVE_TEST_READY=no
```

The result below uses the confirmed `+0x1f8` fact and the audit summary, not the
superseded `UNPROVEN` report.

## Provenance and structural explanation

Actual translation units are:

```text
./source/u_ether.c
./source/f_ncm.c
```

The header used by the provenance tree is:

```text
../vendor-workspace/work/isolated/t6a-netdev-provenance-20260905/linux-5.4.238-ax88179/include/linux/netdevice.h
```

It contains this conditional block immediately before `netdev_ops`:

```c
#ifdef CONFIG_T6A_VENDOR_NETDEV_COMPAT
        unsigned char t6a_vendor_private[32];
#endif
        const struct net_device_ops *netdev_ops;
```

Removing that block changes the callback pointer from the observed candidate
`+0x218` to `+0x1f8`, which exactly matches the confirmed vendor consumer.
This is structural evidence for the delta, but it is not by itself a valid
patch: the same conditional changes every following member until another
proven insertion/deletion cancels it. The existing known values
`dev_addr=0x318`, `dev=0x510`, and `sizeof=0x8c0` must be re-proven after the
whole conditional layout is resolved.

The available `.config` proves `CONFIG_NET_NS`, `CONFIG_NET_SCHED`,
`CONFIG_NET_CLS_ACT`, `CONFIG_XPS`, and `CONFIG_SYSFS`; it does not prove
`CONFIG_WIRELESS_EXT`, `CONFIG_HW_NAT`, or a tracing-related layout block.
Those options remain hypotheses and are not enabled by inference.

## Direct-access field map

Offsets below are only promoted where the current evidence proves them. A
blank vendor offset is intentional; it prevents a guessed candidate.

| field | generic/current TU | current candidate ELF | vendor expected | evidence | status |
|---|---:|---:|---:|---|---|
| `name` | header-defined | direct `snprintf(net->name,...)` | unproven | actual `u_ether.c:861,934` | BLOCKED |
| `netdev_ops` | `0x218` with compat block | store `0x218` | `0x1f8` | exact Sol/Image + current header | MISMATCH PROVEN |
| `ethtool_ops` | follows `netdev_ops` | candidate-derived | unproven | actual setup writes it | BLOCKED |
| `dev_addr` | `0x318` gate | `0x318` | `0x318` | prior final-ELF audit | PASS, must recheck |
| `addr_assign_type` | header-defined | direct writes | unproven | actual `u_ether.c:864,868,1005` | BLOCKED |
| `min_mtu` | header-defined | direct writes | unproven | actual `u_ether.c:882,947` | BLOCKED |
| `max_mtu` | header-defined | direct writes | unproven | actual `u_ether.c:883,948` | BLOCKED |
| `dev` / `dev.parent` | `0x510` gate | `0x510` | `0x510` | prior final-ELF audit | PASS, must recheck |
| `stats` | header-defined | accessed through `net->stats` | unproven | `u_ether.c`, `f_ncm.c` | BLOCKED |
| `mtu` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |
| `type` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |
| `flags` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |
| `features` / `hw_features` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |
| `priv_flags` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |
| `watchdog_timeo` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |
| `header_ops` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |
| `needs_free_netdev` | header-defined | no direct initialization proven | unproven | source scan | NOT DIRECTLY INITIALIZED |

The private `struct eth_dev` fields are a separate ABI and must not be
mislabelled as `net_device` members. They include `gadget`, `dev_mac`,
`host_mac`, `net`, queue/list/work fields, and callbacks. The known private
base is `netdev_priv=0x8c0`; its absolute offsets must be rechecked after the
net_device layout change.

## Register path map

Confirmed before notifier registration:

```text
register_netdev -> register_netdevice
+0xb0: ldr x0, [x19, #0x1f8]
+0xb4: ldr x1, [x0]
```

Thus the first proven consumer is `netdev_ops` at `+0x1f8`. The following
consumer fields are not yet proven from the exact vendor function window and
remain required extraction targets: `name`, namespace (`nd_net`), `reg_state`,
ifindex/list state, `dev`/parent, feature/MTU state, and notifier-related
address lists. The old generic `vmlinux` disassembly is not valid T6A evidence.

## Required reconstruction

1. Freeze the actual compiler command, generated `autoconf.h`/`auto.conf`,
   `netdevice.h`, preprocessed `u_ether.i` and `f_ncm.i`; reject probe-only
   headers.
2. Enumerate all conditional members from `name` through `dev`, and compare
   intervals as `before / vendor delta / after`. The 32-byte compat block is a
   confirmed explanation of the callback delta, not proof of later offsets.
3. Disassemble the exact active Image `register_netdevice` window and map all
   accesses through the notifier boundary.
4. Rebuild a header from source/config provenance only, then add assertions:

```c
BUILD_BUG_ON(sizeof(struct net_device) != 0x8c0);
BUILD_BUG_ON(ALIGN(sizeof(struct net_device), NETDEV_ALIGN) != 0x8c0);
BUILD_BUG_ON(offsetof(struct net_device, netdev_ops) != 0x1f8);
BUILD_BUG_ON(offsetof(struct net_device, dev_addr) != 0x318);
BUILD_BUG_ON(offsetof(struct net_device, dev) != 0x510);
```

   Add each further direct-access and kernel-consumed field only after its
   vendor offset is independently proven.
5. Audit final ELF machine code for every store/load, retaining MODVERSIONS
   (`module_layout=0x3a3eb6e9`, exact UND/version set, CRCs, and vermagic) as
   separate gates.

## Gate outcome

```text
SOURCE_OFFSET_GATE=FAIL (netdev_ops mismatch; remaining vendor offsets incomplete)
TU_ASSERT_GATE=FAIL (0x1f8 assertion not yet in actual TU)
FINAL_ELF_CODEGEN_GATE=FAIL (no changed candidate)
DIRECT_ACCESS_ABI_AUDIT=FAIL
FUNCTION_INSTANCE_GATE=KNOWN PASS, not sufficient
MODVERSIONS_GATE=KNOWN PASS, not sufficient
NET_DEVICE_LAYOUT_RECONSTRUCTION=FAIL
SOL_LIVE_TEST_READY=no
```

No SHA is emitted and no live test is authorized. The next valid action is a
changed-condition offline reconstruction followed by a full static audit.
