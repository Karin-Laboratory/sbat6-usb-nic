# Current research status

Updated: 2026-09-05

This note records the current evidence boundary for the T6A vendor module ABI.
It is a research checkpoint, not a success report.

## Confirmed

```text
TARGET_KERNEL=Linux 5.4.238 / aarch64
VENDOR_MODULE_CORPUS=157 scanned
VENDOR_VALID_THIS_MODULE_SAMPLES=156
VENDOR_THIS_MODULE_SIZE=0x340
VENDOR_MODULE_NAME_OFFSET=0x18
VENDOR_MODULE_NAME_OFFSET_MATCH=156/156
VENDOR_INIT_RELOCATION=0x150
VENDOR_CLEANUP_RELOCATION=0x328
RUNTIME_THIS_MODULE_SECTION_ADDRESSES=157 loaded modules observed
BTF=unavailable
PROC_KCORE=unavailable
```

The runtime sysfs collection proves section placement addresses, not the bytes
of the pointed-to `struct module`. The offline corpus and runtime oracle are
therefore kept as separate kinds of evidence.

## Comparison

```text
UPSTREAM_LINUX_5.4.238_THIS_MODULE=0x280
MEDIATEK_ANDROID_LINEAGE_THIS_MODULE=0x2c0 or offset-incompatible
```

Neither candidate reproduces the vendor observations. The lineage compiler
oracle also misses the observed cleanup offset; matching the size by enabling
all currently known conditionals moves earlier fields and is not accepted as
a vendor layout proof.

## Current blocker

Only two useful relocation anchors were recovered: `init` at `0x150` and
`cleanup` at `0x328`. The module-name field at `0x18` is independently
consistent across all 156 valid vendor modules. This is not yet sufficient to
prove the unknown vendor-specific `struct module` regions.

The following are intentionally not done:

```text
No guessed padding
No ELF patching
No live module test
STRUCT_MODULE_HOLDOUT_PASS=NOT_RUN
VENDOR_OPAQUE_BLOCK_PROVEN=NO
STRUCT_MODULE_LOADER_ABI_PROVEN=no
CUSTOM_NCM_MODULE_LOAD=NOT_RUN
LIVE_TEST_AUTHORIZED=no
```

The previous candidate's kernel crash/Oops experience is why this fail-closed
policy is mandatory. A candidate is not loaded merely because
size/init/cleanup happen to match. Live testing is allowed only after
independent ABI evidence converges.

## Relationship to the net_device work

The current blocker is the `struct module` / module-loader ABI, not the
`net_device` investigation. The existing net-device evidence retains these
vendor observations:

```text
CONFIG_WIRELESS_EXT=y
CONFIG_HW_NAT=y
netdev_ops  = 0x1f8
ethtool_ops = 0x200
min_mtu     = 0x22c
max_mtu     = 0x230
dev_addr    = 0x318
embedded device = 0x510
netdev_priv = 0x8c0
```

Those values remain subject to separate source, TU, final-ELF, modversion, and
artifact-identity gates. They do not establish the module-loader layout.

## Next admissible work

The safe continuation path is offline-only: align the valid vendor corpus,
classify additional relocation/data signatures without treating opaque bytes
as fields, apply 16-byte constraints and source/config archaeology, then use a
compiler oracle and held-out validation. Until those gates converge, no
candidate generation or device load is allowed.
