# Linux 5.4.238 canonical external media-module universe.
obj-m := videodev.o videobuf2-common.o videobuf2-v4l2.o videobuf2-memops.o videobuf2-vmalloc.o uvcvideo.o

videodev-objs := v4l2-dev.o v4l2-ioctl.o v4l2-device.o v4l2-fh.o \
                 v4l2-event.o v4l2-ctrls.o v4l2-subdev.o v4l2-clk.o \
                 v4l2-async.o v4l2-common.o v4l2-trace.o \
                 v4l2-compat-ioctl32.o v4l2-spi.o
videodev-objs += v4l2-i2c.o
obj-m += v4l2-dv-timings.o

videobuf2-common-objs := vb2-core-source.o vb2-trace-source.o
videobuf2-v4l2-objs := vb2-v4l2-source.o
videobuf2-memops-objs := vb2-memops-source.o frame-vector-source.o
videobuf2-vmalloc-objs := vb2-vmalloc-source.o

uvcvideo-y := uvc_driver.o uvc_queue.o uvc_v4l2.o uvc_video.o uvc_ctrl.o \
              uvc_status.o uvc_isight.o uvc_debugfs.o uvc_metadata.o
