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
for name in v4l2-dev v4l2-ioctl v4l2-device v4l2-fh v4l2-event v4l2-ctrls v4l2-subdev v4l2-clk v4l2-async v4l2-common v4l2-trace v4l2-i2c v4l2-dv-timings; do
  cp "$KERNEL_SRC/drivers/media/v4l2-core/$name.c" "$OUTPUT/module/"
done
cp "$KERNEL_SRC/drivers/media/v4l2-core/v4l2-compat-ioctl32.c" "$OUTPUT/module/"
cp "$KERNEL_SRC/drivers/media/v4l2-core/v4l2-spi.c" "$OUTPUT/module/"
for name in videobuf2-core videobuf2-v4l2 videobuf2-memops videobuf2-vmalloc; do
  case "$name" in
    videobuf2-core) out=vb2-core-source.c ;;
    videobuf2-v4l2) out=vb2-v4l2-source.c ;;
    videobuf2-memops) out=vb2-memops-source.c ;;
    videobuf2-vmalloc) out=vb2-vmalloc-source.c ;;
  esac
  cp "$KERNEL_SRC/drivers/media/common/videobuf2/$name.c" "$OUTPUT/module/$out"
done
cp "$KERNEL_SRC/drivers/media/common/videobuf2/vb2-trace.c" "$OUTPUT/module/vb2-trace-source.c"
cp "$KERNEL_SRC/mm/frame_vector.c" "$OUTPUT/module/frame-vector-source.c"
for name in uvc_driver uvc_queue uvc_v4l2 uvc_video uvc_ctrl uvc_status uvc_isight uvc_debugfs uvc_metadata; do
  cp "$KERNEL_SRC/drivers/media/usb/uvc/$name.c" "$OUTPUT/module/"
done
cp "$KERNEL_SRC/drivers/media/usb/uvc/uvcvideo.h" "$OUTPUT/module/"
KCFLAGS="-DCONFIG_MEDIA_SUPPORT_MODULE=1 -DCONFIG_MEDIA_CAMERA_SUPPORT=1 -DCONFIG_VIDEO_DEV_MODULE=1 -DCONFIG_VIDEO_V4L2_MODULE=1 -DCONFIG_VIDEOBUF2_CORE_MODULE=1 -DCONFIG_VIDEOBUF2_V4L2_MODULE=1 -DCONFIG_VIDEOBUF2_MEMOPS_MODULE=1 -DCONFIG_VIDEOBUF2_VMALLOC_MODULE=1 -DCONFIG_USB_VIDEO_CLASS_MODULE=1 -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1 -include $OUTPUT/module/abi_assert.h"
export KCFLAGS
make -C "$KERNEL_SRC" O="$OUTPUT/kernel" M="$OUTPUT/module" ARCH=arm64 LOCALVERSION= KERNEL_SRC="$KERNEL_SRC" -j"${JOBS:-4}" modules > "$OUTPUT/build.log" 2>&1
for name in v4l2-dv-timings videodev videobuf2-common videobuf2-v4l2 videobuf2-memops videobuf2-vmalloc uvcvideo; do
  python3 "$HERE/check-module-metadata.py" "$OUTPUT/module/$name.ko" --symvers "$HERE/vendor-image.symvers" --symvers "$OUTPUT/module/Module.symvers" > "$OUTPUT/$name-metadata.json" || true
  "${CROSS_COMPILE}objdump" -dr "$OUTPUT/module/$name.ko" > "$OUTPUT/$name.asm"
  "${CROSS_COMPILE}readelf" -SW -rW "$OUTPUT/module/$name.ko" > "$OUTPUT/$name-elf.txt"
done
(cd "$OUTPUT/module" && sha256sum *.ko > SHA256SUMS)
"${CROSS_COMPILE}gcc" --version > "$OUTPUT/compiler.txt"
