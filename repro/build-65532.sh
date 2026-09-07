#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
REPRO=$ROOT/repro
SOURCE=$ROOT/driver/t6a-ncm-65532-ntb-candidate-v1/source

: "${KERNEL_SRC:?Set KERNEL_SRC to the matching Linux 5.4.238 source tree}"
: "${KERNEL_BUILD:=$KERNEL_SRC}"
: "${CROSS_COMPILE:?Set CROSS_COMPILE, e.g. aarch64-linux-gnu-}"
[ -d "$KERNEL_SRC" ] || { echo "KERNEL_SRC is not a directory; refusing to build" >&2; exit 2; }
[ -f "$KERNEL_SRC/Makefile" ] || { echo "KERNEL_SRC has no kernel Makefile; refusing to build" >&2; exit 2; }
[ -d "$KERNEL_BUILD" ] || { echo "KERNEL_BUILD is not a directory; refusing to build" >&2; exit 2; }
[ -f "$KERNEL_BUILD/include/config/auto.conf" ] || { echo "KERNEL_BUILD is not a configured output tree; refusing to build" >&2; exit 2; }
[ -f "$SOURCE/SHA256SUMS" ] || { echo "source manifest missing; refusing to build" >&2; exit 2; }

for name in configfs.h f_ncm.c t6a_opaque_abi.h u_ether.c u_ether.h u_ether_configfs.h u_ncm.h; do
    [ -f "$SOURCE/$name" ] || { echo "missing source: $name; refusing to build" >&2; exit 2; }
done
(cd "$SOURCE" && sha256sum -c SHA256SUMS) >/dev/null

for name in configfs.h f_ncm.c t6a_opaque_abi.h u_ether.c u_ether.h u_ether_configfs.h u_ncm.h; do
    cp "$SOURCE/$name" "$REPRO/$name"
done
export KBUILD_EXTRA_SYMBOLS="$REPRO/t6a-vendor-Module.symvers"
make -C "$KERNEL_SRC" O="$KERNEL_BUILD" M="$REPRO" ARCH=arm64 CROSS_COMPILE="$CROSS_COMPILE" clean
exec make -C "$KERNEL_SRC" O="$KERNEL_BUILD" M="$REPRO" ARCH=arm64 CROSS_COMPILE="$CROSS_COMPILE" modules
