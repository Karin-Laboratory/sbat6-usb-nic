# T6A checkpoint: independent Image mapping and register_netdevice provenance — 2026-09-05

Read-only offline evidence. No module load, ConfigFS, UDC bind, reboot, flash,
or other live operation was performed.

Inputs are the hash-pinned active `boot_b` Image
(`de3a1bee91314be0a65bd79f60a954d928f2c31cc4861d41f2e90b948d650082`) and raw
kallsyms (`992040c1b0c8a94bf1b2eac4def82098219af9b77683712bfa74aa86bfb5ada1`).

## Independent mapping gates

The raw Image was mapped with:

```text
image_offset = runtime_va - CURRENT_RUNTIME_STEXT + 0xd80000
CURRENT_RUNTIME_STEXT = 0xffffffc010e80000
```

This is a relative-coordinate mapping; no absolute KASLR slide is claimed.

1. Head crosscheck: independent AArch64 immediate decoding of Image `+0x0`
   (`0x14360000`) gives `B +0xd80000`; GNU `aarch64-linux-gnu-objdump`
   agrees. Image `+0xd80000` begins with `bl +0x20`, and the projected
   `preserve_boot_args` is exactly `Image+0xd80020`.
2. `_stext` crosscheck: `CURRENT_RUNTIME__STEXT=0xffffffc010100800`
   projects to `Image+0x800`; the bytes there are aligned executable text in
   the expected main text region. `_text` is absent and was not substituted.

The 13-sample set is independently consistent: all projections are aligned,
13/13 symbol-to-symbol distances match, and the `register_netdev` projection
contains a direct `bl` to projected `register_netdevice`.

```text
INDEPENDENT_MAPPING_CROSSCHECK_COUNT=2
STEXT_PRESERVE_BOOT_ARGS_CROSSCHECK=PASS
_STEXT_RELATIVE_CROSSCHECK=PASS
VA_IMAGE_MAPPING_SAMPLE_COUNT=13
VA_IMAGE_MAPPING_CONFLICT_COUNT=0
SYMBOL_DISTANCE_MATCH_COUNT=13
BRANCH_EDGE_MATCH_COUNT=1
HEAD_BRANCH_STEXT_OFFSET=PROVEN
HEAD_RELATIVE_MAPPING_CROSSCHECK=PASS
VA_IMAGE_MAPPING=PASS
CURRENT_BOOT_KASLR_SLIDE=UNPROVEN
```

## Actual `register_netdevice` window

The actual Image window `Image+0x6d62e0..0x6d6330` was decoded by both the
independent AArch64 decoder and GNU objdump. Machine-readable rows are in
`t6a-register-netdevice-window-20260905.json`.

```text
REGISTER_NETDEVICE_RUNTIME=0xffffffc0107d6260
REGISTER_NETDEVICE_IMAGE_OFFSET=0x6d6260
REGISTER_NETDEVICE_B4_IMAGE_OFFSET=0x6d6314
REGISTER_NETDEVICE_B4_OPCODE=0xf9400001
REGISTER_NETDEVICE_B4_OPCODE_PROVEN=yes
```

The exact dataflow is:

```asm
register_netdevice entry x0 = struct net_device *dev
0x6d626c: mov  x19, x0
0x6d6310: ldr  x0, [x19, #0x1f8]
0x6d6314: ldr  x1, [x0]
0x6d6318: cbz  x1, ...
0x6d6320: blr  x1                 // called with x0 = dev
```

Thus `ENTRY_X0_IS_DEV=PROVEN`, `DEV_BASE_REGISTER=x19`, and the faulting
operation is a load through `dev + 0x1f8`. The pstore state independently
reports `pc=register_netdevice+0xb4`, `lr=+0xa8`, and `x0=0`, so the fault is
the `ldr x1,[x0]` at the mapped Image offset.

## Field semantics and root-cause disposition

The target-lineage 5.4.238 `include/linux/netdevice.h` defines the first
`struct net_device_ops` member as `ndo_init`. The actual control flow is the
standard registration early phase: load `dev->netdev_ops`, test its first
callback, and call it with `dev`.

```text
FAULTING_REGISTER=x0
FAULTING_POINTER_VALUE=0
FAULTING_OPERATION=load [x0]
SOURCE_OBJECT=net_device
SOURCE_FIELD_OFFSET=0x1f8
NETDEV_OPS_0X1F8_STATUS=PROVEN
REGISTER_NETDEVICE_EXACT_FAULT=PROVEN
```

The candidate artifact `052318` stored its callback pair at `0x218/0x220`,
while the vendor producer evidence and active consumer now agree on
`0x1f8/0x200`. Therefore the corrected root-cause statement is:

```text
ROOT_CAUSE=PROVEN_CANDIDATE
candidate netdev_ops layout was placed at the wrong offset, leaving the
vendor-expected +0x1f8 slot NULL; register_netdevice dereferenced it
```

This is not a claim that the complete replacement header is reconstructed.
All other direct-access gates remain separate and live admission remains
closed. No callable Sol provider is available in this environment, so the
requested hostile review is recorded as pending rather than fabricated:

```text
SOL_NETDEVICE_ROOT_CAUSE_READY=no
NEXT_LIVE_TEST_READY=no
LIVE_OPERATION=FORBIDDEN
EVIDENCE_STATUS=PROVEN
```
