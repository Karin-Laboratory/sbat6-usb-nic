# `addr_assign_type` vendor-offset audit — 2026-09-05

Offline/read-only audit. No candidate was loaded or used in a live test.

```text
FIELD=addr_assign_type
GENERIC_OFFSET=0x24f
CURRENT_TU_OFFSET=0x24f
VENDOR_OFFSET=UNKNOWN
DELTA=UNKNOWN
EVIDENCE=vendor usb_net.ko gether_setup_name/gether_setup_name_default disassembly
CONFIDENCE=not-proven
```

The generic/current TU value comes from the retained layout probe (`591`, or
`0x24f`). The vendor producer binary proves callback stores at `net+0x1f8`
and `net+0x200`, and the existing dev-address evidence at `net+0x318`, but
its setup functions contain no identifiable store to `addr_assign_type`. The
vendor default path relies on allocator/kernel setup for the initial random
address state; that is not a vendor producer-side offset proof.

The retained `netdev-layout-vendor.tsv` value (`639`, `0x27f`) is therefore
classified as a header/probe artifact, not authoritative vendor evidence. It
must not be promoted. No piecewise delta is recorded for this field.

```text
PIECEWISE_NET_DEVICE_MAP=INSUFFICIENT
REGISTER_NETDEVICE_B4_DATAFLOW=UNPROVEN
VENDOR_PRODUCER_NETDEV_OPS_OFFSET=PROVEN
```
