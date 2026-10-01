#!/bin/sh
# Isolated source build. This script does not contact or load a target.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${KERNEL_GIT:?Set KERNEL_GIT to a Git checkout containing upstream v5.4.238}"
: "${OUTPUT:?Set OUTPUT to a new absolute build directory}"
CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}
export CROSS_COMPILE
REV=6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6
case "$OUTPUT" in /*) ;; *) echo 'OUTPUT must be absolute' >&2; exit 2;; esac
case "$OUTPUT" in *' '*) echo 'OUTPUT must not contain spaces' >&2; exit 2;; esac
[ ! -e "$OUTPUT" ] || { echo 'OUTPUT already exists; use a fresh directory' >&2; exit 2; }
(cd "$HERE" && sha256sum -c INPUTS.sha256)
git -C "$KERNEL_GIT" cat-file -e "$REV^{commit}"
mkdir -p "$OUTPUT/source" "$OUTPUT/kernel" "$OUTPUT/module"
# Archive the fixed commit; ignore any local working-tree changes.
git -C "$KERNEL_GIT" archive --format=tar --output="$OUTPUT/source.tar" "$REV"
tar -xf "$OUTPUT/source.tar" -C "$OUTPUT/source"
rm "$OUTPUT/source.tar"
patch -d "$OUTPUT/source" -p1 < "$HERE/netdevice.patch"
cp "$HERE/kernel.config" "$OUTPUT/kernel/.config"
make -C "$OUTPUT/source" O="$OUTPUT/kernel" ARCH=arm64 LOCALVERSION= olddefconfig modules_prepare
cp "$HERE/vendor-image.symvers" "$OUTPUT/kernel/Module.symvers"
cp "$HERE/Makefile" "$HERE/abi_assert.h" "$OUTPUT/module/"
cp "$OUTPUT/source/drivers/net/mii.c" "$OUTPUT/module/"
cp "$OUTPUT/source/drivers/net/usb/usbnet.c" "$OUTPUT/source/drivers/net/usb/ax88179_178a.c" "$OUTPUT/module/"
# KCFLAGS is intentional: ccflags-y alone does NOT cover generated *.mod.c.
KCFLAGS="-DCONFIG_WIRELESS_EXT=1 -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1 -include $OUTPUT/module/abi_assert.h"
export KCFLAGS
make -C "$OUTPUT/source" O="$OUTPUT/kernel" M="$OUTPUT/module" ARCH=arm64 LOCALVERSION= -j"${JOBS:-4}" modules
for name in mii usbnet ax88179_178a; do
    python3 "$HERE/../../tools/check-module-metadata.py" "$OUTPUT/module/$name.ko" \
        --symvers "$HERE/vendor-image.symvers" --symvers "$OUTPUT/module/Module.symvers" > "$OUTPUT/$name-metadata.json"
    "${CROSS_COMPILE}objdump" -dr "$OUTPUT/module/$name.ko" > "$OUTPUT/$name.asm"
    "${CROSS_COMPILE}readelf" -SW -rW "$OUTPUT/module/$name.ko" > "$OUTPUT/$name-elf.txt"
done
(cd "$OUTPUT/module" && sha256sum mii.ko usbnet.ko ax88179_178a.ko > SHA256SUMS)
"${CROSS_COMPILE}gcc" --version > "$OUTPUT/compiler.txt"
printf 'Build and metadata checks completed. Load safety is not established by this script.\n'
