# ButlerX current truth — T6A custom NCM

Updated 2026-09-06 JST after Sol hostile review. This is a snapshot; it does
not reuse keys as a historical log. Scope changes use scoped key names.

## Root-cause checkpoint

The active Image mapping and the `register_netdevice+0xb4` consumer are proven
in relative coordinates. The direct fault is proven; this does not prove the
complete vendor `struct net_device` layout or authorize a new module.

### PROVEN

- active Image mapping, `x0=dev`, `net+0x1f8` load, and exact fault window — [checkpoint evidence](evidence/abi/t6a-checkpoint-mapping-and-register-netdevice-20260905.md)

```text
VA_IMAGE_MAPPING=PASS
NETDEV_OPS_0X1F8_STATUS=PROVEN
REGISTER_NETDEVICE_VENDOR_TEXT=PROVEN
REGISTER_NETDEVICE_EXACT_FAULT=PROVEN
ROOT_CAUSE=PROVEN
SOL_NETDEVICE_ROOT_CAUSE_READY=yes
ACTUAL_VENDOR_KERNEL_TEXT_COMPLETE=UNPROVEN
COMPLETE_VENDOR_NET_DEVICE_LAYOUT_PROVEN=no
```

`REGISTER_NETDEVICE_VENDOR_TEXT` is scoped to the recovered
`register_netdevice` function and must not be read as proof of all kernel text.

## Offline gates

```text
DIRECT_ACCESS_ABI_AUDIT=FAIL_INCOMPLETE
DIRECT_ACCESS_MISMATCH_COUNT=UNKNOWN
NET_DEVICE_FINAL_ELF_GATE=NOT_RUN
FINAL_ELF_VALIDATION=NOT_RUN
STRUCT_MODULE_MODEL_GENERATED_COUNT=32768
STRUCT_MODULE_MODEL_EVALUATED_COUNT=1
STRUCT_MODULE_MODEL_SURVIVOR_COUNT=UNKNOWN
STRUCT_MODULE_BACKGROUND_STATUS=RESULT_INCOMPLETE_NO_CHECKPOINT
STRUCT_MODULE_LOADER_ABI_PROVEN=no
REPRODUCIBLE_BUILD=NOT_PROVEN
PUBLIC_SANITIZATION=NOT_RUN
T6A_TOOLKIT_V0_1_READY=no
```

The structural solver generated all 32768 conditional assignments but only
evaluated one generic compiler-oracle model and ended with `NO_LAYOUT_ENGINE`.
No usable resume checkpoint or completed result file was found; it may be
restarted under the same offline conditions with periodic state persistence.

Minimum corrected-candidate anchors, each requiring its own evidence class:

```text
NETDEV_OPS_OFFSET=0x1f8 PROVEN
ETHTOOL_OPS_OFFSET=0x200 PROVEN
DEV_ADDR_OFFSET=0x318 PROVEN
EMBEDDED_DEV_OFFSET=0x510 PROVEN
NETDEV_PRIV_OFFSET=0x8c0 PROVEN
MIN_MTU_OFFSET=0x22c PROVEN
MAX_MTU_OFFSET=0x230 PROVEN
```

These anchors are not a complete layout. Unknown direct fields keep the
candidate and live gates closed. No build, load, ConfigFS mutation, UDC bind,
reboot, or hardware test is authorized by this checkpoint.

## Public toolkit gate

The compatibility toolkit is an offline scaffold only. Headers that depend on
unproven vendor offsets remain explicitly unstable and are not public stable
API. v0.1 publication is blocked until the three ABI proofs, reproducible
build, final ELF validation, status consistency, evidence sync, and public
sanitization all pass.

```text
USB_FUNCTION_INSTANCE_ABI_PROVEN=UNKNOWN
NET_DEVICE_REQUIRED_ABI_PROVEN=no
STATUS_INTERNAL_CONSISTENCY=PASS
STATUS_EVIDENCE_SYNC=PASS
NEXT_LIVE_TEST_READY=NO
CURRENT_CANDIDATE=NONE
GITHUB_POLICY=BRANCH_ONLY_FORCE_PUSH_FORBIDDEN
```
