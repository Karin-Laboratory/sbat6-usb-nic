# T6A custom NCM isolated function-link test — 2026-09-06

The v4 artifact was tested on T6A through the approved raspi2 jump path.
Windows remained disconnected and no UDC bind, enumeration, IP setup, or
traffic was performed.

## Artifact and baseline

```text
CANDIDATE=t6a_usb_ncm_canonical_v4.ko
SHA256=56fd9b93583ba5c5b17c2986cf4b5b485e147eea3dd89fac3b7f510ad762211
KERNEL=5.4.238 aarch64
VENDOR_GADGET=/config/usb_gadget/g1
VENDOR_UDC_BEFORE=11201000.usb
VENDOR_UDC_AFTER=11201000.usb
VENDOR_FUNCTION_LINKS_BEFORE_AFTER_MATCH=yes
VENDOR_FUNCTIONS_BEFORE_AFTER_MATCH=yes
VENDOR_MODULE_AFTER=usb_net
```

## Isolated sequence

The temporary gadget `/config/usb_gadget/t6a_ncm_test` was created with only
test metadata and config `c.1`. Its `UDC` was verified empty before and after
the link. The custom instance was created as
`functions/t6a_ncm.test0`; its initial `ifname` was `(unnamed net_device)`.

```text
TEST_GADGET_CREATED=PASS
TEST_GADGET_UDC_BOUND=no
CONFIGFS_INSTANCE_CREATE=PASS
CUSTOM_NCM_INSTANCE_VISIBLE=yes
ALLOC_FUNC_REACHED=unknown
FUNCTION_BIND_REACHED=unknown
SYMLINK_RC=0
CUSTOM_NCM_FUNCTION_LINK=PASS
CUSTOM_NCM_FUNCTION_LINK_30S_STABILITY=PASS
CUSTOM_NETDEV_CREATED=no
CUSTOM_NETDEV_NAME=
```

The link increased the module reference count from 0 to 2 without creating a
network interface, as expected for an unbound composite gadget. SSH and a
management ICMP probe remained available during the 30-second observation;
uptime continued without reboot. No new Oops, BUG, watchdog, panic, or call
trace marker was observed in the test interval. Existing unrelated vendor
wireless warning messages remained present.

```text
CUSTOM_NCM_FUNCTION_UNLINK=PASS
TEST_GADGET_CLEANUP=PASS
VENDOR_GADGET_UNCHANGED=PASS
CUSTOM_NCM_MODULE_UNLOAD=PASS
KERNEL_OOPS=0
WDT=0
SPONTANEOUS_REBOOT=0
SSH_STABLE=yes
CUSTOM_NCM_UDC_BIND_TEST_READY=yes
```

The final verification found no `/config/usb_gadget/t6a_ncm_test`, no custom
module, and the original vendor gadget/function links unchanged. The
observed `CUSTOM_NETDEV_CREATED=no` is not a failure at this stage because
the UDC was intentionally left unbound.

`UDC_BIND`, `HOST_ENUMERATION`, and `CUSTOM_USB_NIC_FIRST_PACKET` remain
untested and are not promoted to PASS.
