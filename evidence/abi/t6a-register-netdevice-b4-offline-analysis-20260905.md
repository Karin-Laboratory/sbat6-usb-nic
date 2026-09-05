# T6A `register_netdevice+0xb4` offline analysis — 2026-09-05

## Decision

```text
REGISTER_NETDEVICE_EXACT_FAULT=UNPROVEN
ROOT_CAUSE=UNPROVEN
NEW_CANDIDATE_SHA256=
NEXT_LIVE_TEST_READY=no
LIVE_TEST=FORBIDDEN
```

The bbd228 candidate remains live-banned. No T6A, UDC, ConfigFS, module,
reboot, or Windows operation was performed in this analysis.

## Exact Oops and full register evidence

Source:
`/home/masataka/projects/sbat6-usb-nic/evidence/butlerx-live-evidence-20260905/pre-recovery-console-ramoops-0`

```text
[  512.861250] Unable to handle kernel NULL pointer dereference at virtual address 0000000000000000
[  512.875657] ESR = 0x96000006
[  512.899252] ISV = 0, ISS = 0x00000006
[  512.904318] CM = 0, WnR = 0
[  512.984012] pc : register_netdevice+0xb4/0x37c
[  512.989662] lr : register_netdevice+0xa8/0x37c
[  513.195983] register_netdevice+0xb4/0x37c
[  513.201283] register_netdev+0x20/0x40
[  513.206247] gether_register_netdev+0x34/0x88 [usb_f_ncm]
[  513.212851] ncm_bind+0x8c/0x2d4 [usb_f_ncm]
[  513.218329] usb_add_function+0xec/0x10c
[  513.223459] configfs_composite_bind+0x2b0/0x30c
[  513.229281] udc_bind_to_driver+0x5c/0xf8
```

Full register set preserved in the source evidence:

```text
x29 ffffffc022003b30  x28 ffffff806756b488  x27 ffffff806756b000
x26 ffffff8054629eb0  x25 ffffff806dc24150  x24 ffffff8054628198
x23 ffffff806dc24120  x22 ffffff805d5c5930  x21 ffffffc0111688c0
x20 0000000000000000  x19 ffffff805d5c5000  x18 0000000000000000
x17 0000000000000000  x16 0000000000000000  x15 0000000000000000
x14 0000000000000000  x13 0000000000000020  x12 0000000000000020
x11 0101010101010101  x10 ffffff7f7f7f7f7f  x9  fefefdff2f617274
x8  ffffffffffffffff  x7  fefefefefefefefe  x6  ffffff805d5c5004
x5  0000000000000000  x4  ffffffffffffffff  x3  0000000030627375
x2  0000000000000004  x1  6416b1ffd1a41e00  x0  0000000000000000
```

`x0=0` is therefore a fact about the faulting instruction's live register
state. It does not by itself identify the original `net_device` pointer or a
field offset.

## T6A kernel disassembly status

The only local `vmlinux` is:

```text
/home/masataka/projects/sbair6-rce/work/build/out-linux-5.4.238-air6-upstream/vmlinux
Build-ID: 6eeb49f89fc8edfef75ba4b9259ce00f369e2ef6
```

Its `System.map` has `register_netdevice` at `ffffffc0105a5c94`, but the
preserved build record explicitly says the isolated object build had no
vendor `vmlinux` during modpost. No T6A vendor Image/vmlinux/kallsyms proving
that address and instruction stream is present in this workspace. The local
file is consequently not promoted as T6A exact-kernel evidence.

For reference only, the local generic/reconstructed vmlinux decodes:

```text
register_netdevice+0xa8: f940f660  ldr x0, [x19, #488]
                         ; #488 = 0x1e8
register_netdevice+0xac: f9400001  ldr x1, [x0]
register_netdevice+0xb0: b40001a1  cbz x1, ...
```

This reference stream would make the `+0xac` load, not `+0xb4`, the
NULL-dereferencing load. It cannot be used to label the T6A `+0xb4` field.
The apparent mismatch is exactly why the vendor kernel binary is required.

## Data-flow conclusion

The Oops proves only:

```text
T6A register_netdevice+0xb4 executed a read from virtual address 0
faulting register x0 was 0
```

The following are not proven from the available T6A evidence:

```text
faulting base register source       UNPROVEN
original base was net_device        UNPROVEN
net_device offsetof used            UNPROVEN
NULL field value                    UNPROVEN
```

In particular, `net == NULL` is not inferred. The call chain proves that the
candidate reached the vendor kernel registration path, but not which member
the vendor kernel accessed at its `+0xb4`.

## Candidate final ELF accesses

Artifact and SHA256:

```text
/home/masataka/projects/sbat6-usb-nic/candidate/20260905-module-layout-provenance-v2/usb_f_ncm.ko
bbd228debf2c49a55a68729b1a09eff3e8bba34bb6bb0cb7c085b0158ae88e3c
```

Final ELF `gether_setup_name_default` contains:

```text
2060: mov w0, #0xb8                  ; alloc_etherdev_mqs private size
2124: a91e8660  stp x0, x1, [x19,#488]
                                    ; netdev_ops/ethtool_ops at 0x1e8/0x1f0
```

Its `gether_register_netdev` contains:

```text
1be8: f9428801  ldr x1, [x0,#1296]   ; net->dev base 0x510
1bec: b4000381  cbz x1, ...
1bf0: 79526801  ldrh w1, [x0,#2356]
1bf8: b9493002  ldr w2, [x0,#2352]
1c00: b9031802  str w2, [x0,#792]     ; dev_addr 0x318
1c04: 79063801  strh w1, [x0,#796]
1c08: bl register_netdev
```

Thus the candidate's own final ELF uses the intended corrected `dev_addr`
offset and reaches `register_netdev`; it does not prove the vendor kernel's
corresponding `netdev_ops` offset.

## Candidate source field inventory

The source directly touches these real fields (including macro/inline paths):

```text
name, stats, netdev_ops, addr_assign_type, dev_addr (compat helper),
min_mtu, max_mtu, dev, netdev_ops; netdev_ops is also dereferenced in f_ncm.c
```

The remaining state used by `u_ether.c` is `struct eth_dev`, not
`struct net_device`: `gadget`, `dev_mac`, `host_mac`, `net`, `qmult`, `zlp`,
`no_skb_reserve`, `header_len`, `wrap`, `unwrap`, `lock`, `req_lock`,
`tx_reqs`, `rx_reqs`, `rx_frames`, `tx_qlen`, `work`, `port_usb`, and `todo`.
No invented `net_device` fields are added to the audit.

Known candidate layout gates remain:

```text
sizeof(net_device) 0x8c0
netdev_priv        0x8c0
dev_addr           0x318
dev                0x510
```

The generic header's netdev callback offsets are `netdev_ops=0x1e8` and
`ethtool_ops=0x1f0`. The candidate's final ELF stores those values at those
offsets. The vendor module's setup path also shows a direct store pair at
`[x19,#0x1e8]`, but that is module evidence, not proof of the T6A kernel's
`register_netdevice` access at `+0xb4`.

## Vendor/candidate offset table

| field/purpose | candidate final ELF | vendor usb_net.ko | T6A kernel read at +0xb4 | status |
|---|---:|---:|---:|---|
| `netdev_ops` | store `0x1e8` | setup store `0x1e8` observed | unavailable | T6A fault field unproven |
| `ethtool_ops` | `0x1f0` source/code model | not independently mapped | unavailable | unproven |
| `dev_addr` | store `0x318` | private `dev_mac` `0xa7f`; no direct net->dev_addr access | unavailable | not fault candidate |
| `struct device` / parent | `0x510` base | parent path `0x550` observed | unavailable | vendor private/layout difference |
| `netdev_priv` | `0x8c0` gate | `0x8c0` observed | n/a | PASS as prior static gate |
| `sizeof(net_device)` | `0x8c0` gate | allocation-compatible evidence | n/a | PASS as prior static gate |

The decisive `candidate writes FIELD at A / vendor kernel reads FIELD at B`
comparison cannot be completed without the T6A vendor kernel binary. No
padding patch is justified.

## Config audit

The preserved build `.config` proves neither `CONFIG_WIRELESS_EXT` nor
`CONFIG_HW_NAT` enabled. It proves `CONFIG_NET_NS`, `CONFIG_NET_SCHED`,
`CONFIG_NET_CLS_ACT`, `CONFIG_XPS`, and `CONFIG_SYSFS` in the reconstructed
build. No T6A `config.gz` or vendor generated autoconf hash is preserved.

Therefore the earlier WEXT-plus-32-byte compatibility model remains a layout
reproduction hypothesis, not a T6A config fact. `TRACEPOINTS/TRACING` and
`CONFIG_HW_NAT` are not promoted.

## Sol escalation record

No callable Sol channel is available in this offline agent context. Required
fields are nevertheless preserved without fabricating a response:

```text
SOL_ESCALATION_TIME=2026-09-05T00:00:00+09:00 (offline review start)
SOL_INPUT_SUMMARY=bbd228 Oops, full registers, call trace, candidate/vendor ELF, reconstructed kernel evidence
SOL_DIAGNOSIS=unavailable; exact T6A +0xb4 instruction and field cannot be verified from preserved vendor-kernel evidence
SOL_ROOT_CAUSE_HYPOTHESIS=vendor net_device ABI/layout mismatch remains plausible; netdev_ops/dev_addr field is not proven
SOL_ROOT_CAUSE_CONFIDENCE=low for this fault; high only that registration reached vendor kernel
SOL_RECOMMENDED_ANALYSIS=obtain exact T6A Image/vmlinux/kallsyms; disassemble register_netdevice +/-0x70..0x100; map +0xb4 data flow
SOL_RECOMMENDED_PATCH=none until exact field/offset is proven
SOL_NEXT_LIVE_TEST_READY=no
```

The escalation text required by the request is recorded as the analysis
constraint: the old `gether_register_netdev` NULL dereference is not reused;
`x0=0` is not interpreted alone; the exact vendor instruction must be mapped
first.

## Final classification

```text
REGISTER_NETDEVICE_EXACT_FAULT=UNPROVEN
ROOT_CAUSE=UNPROVEN
ROOT_CAUSE_PATCH=none
NEW_REGISTER_NETDEVICE_FIELD_GATE=NOT_APPLICABLE
NEW_CANDIDATE_SHA256=
NEXT_LIVE_TEST_READY=no
```

Required next offline artifact is the actual T6A vendor kernel `vmlinux` or
equivalent exact text/kallsyms pair. Until then, creating a changed-condition
candidate would be speculation and is prohibited by the requested gates.
