#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${KERNEL_SRC:?Set KERNEL_SRC to the fixed Linux 5.4.238 checkout}"
: "${OUTPUT:?Set OUTPUT to a new absolute build directory}"
CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}
export CROSS_COMPILE
REV=6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6
case "$OUTPUT" in /*) ;; *) echo 'OUTPUT must be absolute' >&2; exit 2;; esac
[ ! -e "$OUTPUT" ] || { echo 'OUTPUT already exists' >&2; exit 2; }
git -C "$KERNEL_SRC" cat-file -e "$REV^{commit}"
mkdir -p "$OUTPUT/kernel" "$OUTPUT/module"
ln -s "$KERNEL_SRC" "$OUTPUT/source"
cp "$HERE/kernel.config" "$OUTPUT/kernel/.config"
patch -d "$KERNEL_SRC" -p1 < "$HERE/netdevice.patch" > "$OUTPUT/netdevice-patch.log"
restore_source() { patch -d "$KERNEL_SRC" -p1 -R < "$HERE/netdevice.patch" >/dev/null 2>&1 || true; }
trap restore_source EXIT
make -C "$KERNEL_SRC" O="$OUTPUT/kernel" ARCH=arm64 LOCALVERSION= olddefconfig modules_prepare > "$OUTPUT/prepare.log" 2>&1
cp "$HERE/vendor-image.symvers" "$OUTPUT/kernel/Module.symvers"
cp "$HERE/Makefile" "$HERE/abi_assert.h" "$OUTPUT/module/"
cp "$KERNEL_SRC/drivers/net/mii.c" "$OUTPUT/module/"
cp "$KERNEL_SRC/drivers/net/usb/usbnet.c" "$OUTPUT/module/"
cp "$HERE/aqc111.c" "$HERE/aqc111.h" "$OUTPUT/module/"
KCFLAGS="-DCONFIG_USB_NET_AQC111_MODULE=1 -DCONFIG_USB_USBNET_MODULE=1 -DCONFIG_USB_RTL8152_MODULE=1 -DCONFIG_WIRELESS_EXT=1 -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1 -include $OUTPUT/module/abi_assert.h"
export KCFLAGS
make -C "$KERNEL_SRC" O="$OUTPUT/kernel" M="$OUTPUT/module" ARCH=arm64 LOCALVERSION= -j"${JOBS:-4}" modules > "$OUTPUT/build.log" 2>&1
for name in mii usbnet aqc111; do
  python3 "$HERE/check-module-metadata.py" "$OUTPUT/module/$name.ko" --symvers "$HERE/vendor-image.symvers" --symvers "$OUTPUT/module/Module.symvers" > "$OUTPUT/$name-metadata.json" || true
  "${CROSS_COMPILE}objdump" -dr "$OUTPUT/module/$name.ko" > "$OUTPUT/$name.asm"
  "${CROSS_COMPILE}readelf" -SW -rW "$OUTPUT/module/$name.ko" > "$OUTPUT/$name-elf.txt"
done
(cd "$OUTPUT/module" && sha256sum mii.ko usbnet.ko aqc111.ko > SHA256SUMS)
"${CROSS_COMPILE}gcc" --version > "$OUTPUT/compiler.txt"
