# RTL8157-capable `r8152`

Status: **LIVE LOAD + RTL8156 REGRESSION VALIDATED / RTL8157 HARDWARE PENDING**

This is one driver artifact for the RTL8157 target. The RTL8157 device itself was
not available; support is present in the published Realtek source and the module
was loaded on SBA6D and regression-tested with an RTL8156 at 2500 Mb/s Full.

## Provenance and target

- Source: [Realtek r8152 v2.21.4](https://github.com/wget/realtek-r8152-linux), commit `9ff8b9d961f3927a211a25b187c749daf0769318`
- USB target: RTL8157, `0bda:8157`, 5GbE class
- Kernel: vendor Linux 5.4.238, ARM64, SBA6D
- Firmware: no external firmware identified; the source uses embedded chip tables
- Canonical workspace: `work/r8152-rtl8157-sbat6b-canonical-20261004`

## Reproduction inputs

The directory contains the exact source snapshot used for the module, `kernel.config`,
the `net_device` compatibility patch, vendor-image `Module.symvers`, ABI assertions,
and `build.sh`. Set `KERNEL_GIT` to a checkout containing commit
`6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6` (Linux 5.4.238) and use an AArch64
cross compiler:

```sh
export KERNEL_GIT=/path/to/linux-5.4.238
export CROSS_COMPILE=aarch64-linux-gnu-
export OUTPUT=$PWD/out-r8157
sh build.sh
```

The build uses `ARCH=arm64`, `LOCALVERSION=`, the saved config, vendor
`Module.symvers`, and global KCFLAGS covering `CONFIG_WIRELESS_EXT`, tracing,
module-tree lookup, and the ABI assertion header. Build order is `mii` then
`r8152`; the same-run `Module.symvers` is used for dependency CRCs. No finished-ELF
CRC patching is used. Run `../../tools/check-module-metadata.py` and inspect
`file`, `modinfo`, `readelf -h -S -r` on the result.

The final ELF audit found `.gnu.linkonce.this_module` size `0x340`, init `0x150`,
cleanup `0x328`, `module_layout` CRC `0x3a3eb6e9`, `dev_addr=0x318`,
`netdev_priv=0x8c0`, and no obsolete `dev_addr=0x2e8` access. Build A and B are
section-equivalent; their full hashes differ only in path-bearing debug data.

## Exact tested artifact

Published as [`artifacts/t6b_r8157_r8152_hardware_pending.ko`](../../artifacts/t6b_r8157_r8152_hardware_pending.ko).
This is **Build A**, SHA256
`9f21d3001df750b605877cd092a862e952d7e824527cc9d15c66828bada35c84`. The hash
was verified on-target after transfer, followed by `insmod` with RC 0. The
RTL8156 regression passed bind, interface open, 2500 Mb/s Full, 60/60 ping,
iperf3 P1 2.27 Gbit/s and P4 2.15 Gbit/s, with no retransmissions or errors.

The RTL8157 physical probe, 5GbE negotiation, and 5GbE traffic remain pending
because no RTL8157 hardware is owned. See
[`evidence/reproducibility/t6b-r8157-20261004.md`](../../evidence/reproducibility/t6b-r8157-20261004.md).

