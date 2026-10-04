# AQC111U / AQC112U: `aqc111`

Status: **LIVE LOAD VALIDATED / AQC HARDWARE PENDING**

## Hardware targets and one artifact

Two hardware targets are covered by one Linux driver implementation and one
published `aqc111.ko`; the binary is not duplicated:

- AQC111U / 5GbE class
- AQC112U / 2.5GbE class

Source is the official Linux 5.4.238 in-tree driver at commit
`6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6`. The source contains both
`SPEED_2500`/`2500baseT_Full` and `SPEED_5000`/`5000baseT_Full` paths and USB IDs
`2eca:c101`, `0b95:2790`, `0b95:2791`, `20f4:e05a`, and `1c04:0015`.

## Compatibility recipe

The directory contains the Linux driver sources, saved ARM64 config, ABI patch,
vendor-image `Module.symvers`, assertions, and `build.sh`. Build against a clean
Linux 5.4.238 checkout at the commit above:

```sh
export KERNEL_SRC=/path/to/linux-5.4.238
export CROSS_COMPILE=aarch64-linux-gnu-
export OUTPUT=$PWD/out-aqc111
sh build.sh
```

The canonical flags include the AQC111/USBNET/MII module options, WEXT, tracing,
and module-tree lookup. Dependency order is `mii -> usbnet -> aqc111`; all three
are built in one external-module universe and the generated `Module.symvers` is
fed into the metadata audit. The final ELF has `struct module=0x340`, init
`0x150`, cleanup `0x328`, `netdev_ops=0x1f8`, `ethtool_ops=0x200`,
`dev_addr=0x318`, and no old `0x2e8` access. Metadata result is MATCH and no
finished-ELF CRC patching was used.

## Exact tested artifacts

The exact Build A modules copied to SBA6D and hash-verified are:

- [`artifacts/mii.ko`](../../artifacts/mii.ko) — `cc1f7a590358d2804d49d279bd8275fb59c0f289f84da9dabff0c9241aa27cdb`
- [`artifacts/usbnet.ko`](../../artifacts/usbnet.ko) — `f7f26db2018dbf350745498a815e5ee373933fc76d230719d8199592fba77b89`
- [`artifacts/aqc111.ko`](../../artifacts/aqc111.ko) — `92f3e2040fa2963ed5effcafffd19044e38599c1c0e6312b5152d5e890fc2ab4`

The live sequence was `insmod mii.ko`, `insmod usbnet.ko`, `insmod aqc111.ko`,
all RC 0. The module remained loaded for six 10-second observations, SSH/ping
remained available, boot_id was unchanged, and no AQC-related WARN/Oops/panic
occurred. No AQC111U or AQC112U device was attached, so hardware probe, link,
and traffic are explicitly unverified. Details:
[`evidence/reproducibility/t6b-aqc111-live-load-20261004.md`](../../evidence/reproducibility/t6b-aqc111-live-load-20261004.md).

