# T6A NCM ATTEMPT-03 rebuild and live result — 2026-09-05

## Rebuild

The four recorded provenance header hashes matched exactly:

```text
netdevice.h  9214601db460247e6f1b51110d8c0d694ec09729164073066339055371440286
kconfig.h    74156ad6a09b721a8bfbb390e9a702260f9d41ff7c7aafb2b6cbe3279da7e3b7
autoconf.h   f36b4c3f2eaf3d6c0ec92309c170eaa0c2219fc95a1a95faa3d3daa630cd5cfa
auto.conf    687158a2548a00eab29271186acf1ca4b80cc1f19dd87d9a51835ab81b48d2ab
```

The clean module workdir was:
`/home/masataka/projects/sbair6-rce/work/isolated/attempt03-clean-20260905-090210`

The build used the recorded isolated source/object trees, `ARCH=arm64`,
`CROSS_COMPILE=aarch64-linux-gnu-`, and the vendor plus telemetry symbol maps.
The generated module was:

```text
SHA256=73b070c90bb1d8bacd9b0145b72f385d445afd44adb553b1ab9c97ee42f6441d
original f07600aa... reproduced: no
vermagic=5.4.238 SMP mod_unload modversions aarch64
depends=sbat6_ncm_telemetry
```

Static validation passed: `UND=81`, `versions=82`, kernel CRC `74/74`,
telemetry CRC `7/7`, `module_layout=0x3a3eb6e9`, the three
`usb_function_instance` offsets, the `u_ether.c` net_device compile-time
assertions (`sizeof=0x8c0`, `dev_addr=0x318`, `dev=0x510`, priv base `0x8c0`),
and final ELF access offsets. The canonical host artifact is:

`/home/masataka/projects/sbat6-usb-nic/candidate/20260905-attempt03-clean/usb_f_ncm.ko`

## Distribution and preflight

Host → raspi2 staging → T6A `/tmp/usb_f_ncm.ko` SHA256 matched the value above.
The telemetry map matched its recorded SHA256. The telemetry `.ko` was then
found and staged separately; its SHA256 was
`94b157ad17cbe678f2484d058b2e5f8231e5ed6de6fe33f8349ee1588ca6ebf5`.

The first live run released vendor network functions exactly `6 -> 4 -> 2 -> 0`
for `ncm.gs8`, `ecm.gs8`, and `rndis.gs4`, then `rmmod usb_net` succeeded.
It stopped at telemetry `insmod`: the `.ko` had not been staged in the first
run. Candidate load, ConfigFS instance, attributes, mode/GPIO, f5, ncm0, and
all ATTEMPT-03 markers were not reached. No ACM, FFS, or mass-storage function
was touched; no UDC bind or Windows connection occurred.

During recovery the telemetry module reported `[permanent]`, so it could not
be unloaded. A reboot was issued to clear the temporary state. After reboot
T6A SSH became unreachable because raspi2 `eth0` was DOWN and the `codex` user
could not bring it up (`RTNETLINK answers: Operation not permitted`). No
serial device was present on raspi2. Therefore reboot reason, pstore, final
vendor restoration, and persistent marker state could not be collected.

```text
F5_ABSOLUTE_LINK_LIVE=NOT_RUN
NCM0_CREATION=NOT_RUN
CANDIDATE_PRE_UDC_STABILITY_30S=NOT_RUN
NET_DEVICE_PRE_UDC_LIVE=NOT_RUN
UDC_BIND=NOT_RUN
WDT/Oops caused by this attempt=not observed before loss; prior WDT record remained
last persistent marker=none (M01..M10 not reached)
final classification=BLOCKED during recovery: T6A management path unavailable
```
