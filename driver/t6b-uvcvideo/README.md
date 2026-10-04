# UVC / V4L2 / videobuf2

Status: **HARDWARE PROBE + STREAM + VISUAL VALIDATION PASS**

## Provenance and build

These are official Linux 5.4.238 sources at commit
`6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6`, built for the SBA6D ARM64 vendor
kernel. The directory includes the source snapshot, config, ABI patch, vendor
`Module.symvers`, assertions, and `build.sh`. Build with:

```sh
export KERNEL_SRC=/path/to/linux-5.4.238
export CROSS_COMPILE=aarch64-linux-gnu-
export OUTPUT=$PWD/out-uvc
sh build.sh
```

The config enables `MEDIA_SUPPORT=m`, camera/USB media, V4L2 and the four
videobuf2 module options, with media controller and UVC input events disabled.
Canonical KCFLAGS include the media module options, tracing, and the ABI assertion
header. The dependency/load order used on hardware was:

```text
v4l2-dv-timings
videobuf2-memops -> videobuf2-vmalloc
videodev -> videobuf2-v4l2
videobuf2-common -> videobuf2-v4l2
videobuf2-v4l2 + videodev + videobuf2-common + videobuf2-vmalloc -> uvcvideo
```

All seven modules have metadata MATCH, `struct module=0x340`, vermagic
`5.4.238 SMP mod_unload modversions aarch64`, and Build A/B section-equivalent
ELFs. The live artifact is Build A, not a replacement rebuild.

## Exact published modules

The seven exact Build A modules loaded on SBA6D are in [`artifacts/t6b_uvc/`](../../artifacts/t6b_uvc/):

`v4l2-dv-timings.ko`, `videobuf2-memops.ko`, `videobuf2-vmalloc.ko`,
`videodev.ko`, `videobuf2-common.ko`, `videobuf2-v4l2.ko`, and `uvcvideo.ko`.
Their hashes are in [`artifacts/SHA256SUMS`](../../artifacts/SHA256SUMS).

## Hardware result

The device was UltraSemi `USB2 Video`, VID:PID `345f:2130`, USB 480 Mbps, UVC
1.00. `uvcvideo` bound and created `/dev/video0` (capture) and `/dev/video1`.
`/dev/video0` streamed MJPEG 640x480 through MMAP/STREAMON; five frames were
received and the saved fifth JPEG was 15,843 bytes. The color-bar image is
[`evidence/reproducibility/t6b-uvc-frame.jpg`](../../evidence/reproducibility/t6b-uvc-frame.jpg).
Decode and visual inspection passed: clean white/yellow/cyan/green/magenta/red/
blue/black bars, no visible corruption. boot_id stayed unchanged; no USB reset,
disconnect, UVC/vb2 WARN, Oops, or panic occurred. Full evidence is
[`evidence/reproducibility/t6b-uvc-stream-20261004.md`](../../evidence/reproducibility/t6b-uvc-stream-20261004.md).

