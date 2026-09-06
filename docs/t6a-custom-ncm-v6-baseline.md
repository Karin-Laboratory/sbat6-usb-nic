# Custom external NCM v6 working baseline

Date: 2026-09-06 JST

The corrected custom external NCM function driver loads on the stock SBA6D
kernel, enumerates on Windows as a `UsbNcm Host Device`, passes bidirectional
IPv4 traffic, and sustains approximately 340–353 Mbit/s in the current
baseline.

```text
artifact=candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.ko
SHA256=8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799
previous_bad_v6_SHA256=12c3f21ce5f387d0d5c21e42d3e3ca0ee8b9840d09c93a45caa66a6223c80212
```

## Root causes

v5 used an obsolete TX pointer offset. The timeout path legitimately calls
`ndo_start_xmit(NULL, netdev)` to flush a pending NCM NTB; the corrected
implementation preserves that behavior and uses `_tx=0x3c0`, queue stride
`0x140`, queue state `0x90`, `num_tx_queues=0x3c8`,
`real_num_tx_queues=0x3cc`, and `trans_start=0x88`.

The failed v6 reintroduced `DECLARE_USB_FUNCTION_INIT(ncm, ...)`. Its
`usb_function_driver` name collided with the vendor `usb_net` owner of
`"ncm"`, so `usb_function_register()` returned `-EEXIST` (`-17`) during
module initialization. The corrected v6 registers as `t6a_ncm` and contains
no `usbfunc:ncm` alias.

Detailed evidence is in `evidence/t6a-v6/`.

## Static gates

```text
MODULE_INIT_EEXIST_GATE=PASS
FUNCTION_DRIVER_NAME_COLLISION_GATE=PASS
NULL_SKB_TIMEOUT_PATH_GATE=PASS
TX_DATAPATH_FINAL_ELF_GATE=PASS
FINAL_ELF_VALIDATION=PASS
REPRODUCIBLE_BUILD=PASS
```

Two clean builds produced the published SHA256. The build used the
vendor-compatible Linux 5.4.238 AArch64 environment and symbol map; private
host paths are intentionally omitted.

## Reproduction

After transferring the artifact to T6A through the authorized management
gateway, verify and load it:

```sh
sha256sum /tmp/t6a_usb_ncm_canonical_v6.ko
insmod /tmp/t6a_usb_ncm_canonical_v6.ko
lsmod | grep t6a
mkdir -p /config/usb_gadget/t6a_ncm_test/functions/t6a_ncm.test0
mkdir -p /config/usb_gadget/t6a_ncm_test/configs/c.1
ln -s /config/usb_gadget/t6a_ncm_test/functions/t6a_ncm.test0 \
  /config/usb_gadget/t6a_ncm_test/configs/c.1/t6a_ncm.test0
echo '' > /config/usb_gadget/g1/UDC 2>/dev/null || true
echo 0 > /sys/class/gpio/gpio322/value
echo 3 > /sys/devices/platform/11201000.usb/mode
echo 11201000.usb > /config/usb_gadget/t6a_ncm_test/UDC
ip link set usb0 up
ip addr replace test-net.77.1/24 dev usb0
```

Windows should enumerate `UsbNcm Host Device` with `test-net.77.2/24` while
T6A uses `test-net.77.1/24`.

## Live-test record

Windows-to-T6A ping passed 30/30 with 0% loss after the initial link warm-up
packet. T6A-to-Windows passed 30/30 with 0% loss and 0.968/1.323/1.832 ms
min/avg/max RTT. Windows reported `Up` and 426.0 Mbps link speed.

```text
Windows -> T6A: sender 344 Mbits/sec, receiver 340 Mbits/sec
T6A -> Windows (-R): sender 353 Mbits/sec, receiver 352 Mbits/sec, Retr=0
T6A -> Windows (-R -P 4): SUM sender 359 Mbits/sec, SUM receiver 353 Mbits/sec, Retr=0
```

This is a working baseline only. Vendor-baseline performance above 1 Gbit/s,
long-duration endurance, reboot-time automatic configuration, and production
readiness remain unmet.
