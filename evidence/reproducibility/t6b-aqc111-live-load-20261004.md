# AQC111/AQC112 live-load evidence

- Workspace: `aqc111-sbat6b-canonical-20261004`
- Source: Linux 5.4.238, commit `6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6`
- Target: SBA6D, ARM64
- Hardware: no AQC111U/AQC112U attached

Exact Build A hashes copied to the target and verified there:

```text
cc1f7a590358d2804d49d279bd8275fb59c0f289f84da9dabff0c9241aa27cdb  mii.ko
f7f26db2018dbf350745498a815e5ee373933fc76d230719d8199592fba77b89  usbnet.ko
92f3e2040fa2963ed5effcafffd19044e38599c1c0e6312b5152d5e890fc2ab4  aqc111.ko
```

Load order was `mii`, `usbnet`, `aqc111`; all `insmod` calls returned 0. Six
10-second observations passed with unchanged boot_id, working SSH/ping, and no
AQC-related WARN/Oops/panic. A direct load before dependencies failed as
expected with missing `usbnet_*`; the dependency sequence resolved it. No probe,
bind, link, or traffic result is claimed for either hardware target.

