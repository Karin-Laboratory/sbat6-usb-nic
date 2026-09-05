# T6A research status — 2026-09-05

The highest-priority blocker is `ACTIVE_KERNEL_VA_TO_IMAGE_MAPPING`.

```text
ACTUAL_VENDOR_KERNEL_TEXT=UNPROVEN
REGISTER_NETDEVICE_EXACT_FAULT=UNPROVEN
ROOT_CAUSE=UNPROVEN
VA_IMAGE_MAPPING=FAIL
CURRENT_BOOT_KASLR_SLIDE=UNPROVEN
CRASH_BOOT_KASLR_SLIDE=0x80000
STRUCT_MODULE_PRIORITY=SECONDARY
STRUCT_MODULE_LIVE_GATE=RETAINED
LIVE_OPERATION=PROHIBITED
```

The vendor module's producer observations remain useful but are not current
kernel consumer proof:

| field | value | classification | evidence type |
|---|---:|---|---|
| `netdev_ops` | `0x1f8` | OBSERVED | vendor ELF producer anchor |
| `ethtool_ops` | `0x200` | OBSERVED | vendor ELF producer anchor |
| `dev_addr` | `0x318` | OBSERVED | vendor ELF access |
| embedded `dev` | `0x510` | OBSERVED | vendor ELF access |
| `min_mtu` | `0x22c` | CORROBORATED | vendor paired store; source/TU proof missing |
| `max_mtu` | `0x230` | CORROBORATED | vendor paired store; source/TU proof missing |

No value above is sufficient to assert `register_netdevice+0xb4` dataflow or
root cause. The exact corresponding Linux 5.4.238 source, vendor patches,
configuration, and reproducible build provenance remain open.

The mapping audit and machine-readable model are linked from
[the evidence audit](../../evidence/abi/t6a-va-image-mapping-audit-20260905.md).
