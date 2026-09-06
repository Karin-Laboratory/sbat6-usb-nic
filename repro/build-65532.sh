#!/bin/sh
set -eu
: "${KERNEL_SRC:?Set KERNEL_SRC to the matching Linux 5.4.238 source tree}"
: "${CROSS_COMPILE:?Set CROSS_COMPILE, e.g. aarch64-linux-gnu-}"
exec make -C "$KERNEL_SRC" M="$PWD/repro" ARCH=arm64 CROSS_COMPILE="$CROSS_COMPILE" modules
