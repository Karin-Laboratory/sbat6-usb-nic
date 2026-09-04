# T6A NCM telemetry

This is the first-stage telemetry counter sink for the 1.34 Gbps investigation.
It is deliberately passive until a vendor-kernel instrumentation patch calls
the exported APIs. It was rebuilt against the saved vendor tree and its
load/read/unload path was smoke-tested on T6A without changing USB state.

## Build

```sh
make
```

The Makefile defaults to the existing 5.4.238 T6A source/output and arm64
cross compiler. Override `KDIR`, `KBUILD_OUTPUT`, or `CROSS_COMPILE` when
reproducing the build.

The default `KDIR` is the vendor tree, so the target vendor `Module.symvers`
and MODVERSIONS CRCs are used. The ax88179 comparison tree is not compatible.

## Readout after an authorized load

```sh
mount -t debugfs none /sys/kernel/debug       # only if already permitted
cat /sys/kernel/debug/sbat6_ncm_telemetry/stats
```

Record two snapshots around the same-duration iperf3 run. Do not interpret a
single snapshot as a rate. The file reports sums and logarithmic histogram
bins; the design document defines the derived rates and fill ratio.

## Rollback

After the test has stopped and the vendor integration no longer calls the
APIs, an authorized operator may run `rmmod sbat6_ncm_telemetry`. This removes
only its debugfs directory and counters; it does not touch the gadget, UDC,
role, configfs, or ncm0. If a module remains in use, do not force-unload it.

## Not included

There is no automatic hook into `usb_net.ko`, no NCM protocol change, no
64 KiB NTB change, and no performance claim. Those are separate, one-variable
experimental steps after baseline telemetry is obtained.
