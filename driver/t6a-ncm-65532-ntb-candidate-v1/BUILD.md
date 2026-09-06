# t6a-ncm-65532-ntb-candidate-v1

This directory contains the complete source inputs for the recommended
65532-byte NTB candidate. It is an external module for the T6A vendor Linux
5.4.238 ARM64 kernel; it is not a generic upstream-kernel module.

The published module is built from the source files in `source/` and the
public reproducibility Makefile. The source tree, build configuration,
compiler family, vermagic, and final module hash are recorded in the release
notes. The module SHA256 is `7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1`.

Build with:

```sh
export KERNEL_SRC=/path/to/the/matching/t6a-linux-5.4.238-tree
export CROSS_COMPILE=aarch64-linux-gnu-
./repro/build-65532.sh
sha256sum repro/t6a_usb_ncm_65532_candidate_v1.ko
```

The expected vermagic is `5.4.238 SMP mod_unload modversions aarch64`.
The source is GPL-2.0-only. The vendor kernel tree and its proprietary
components are not redistributed here.
