# T6A custom NCM function-driver name isolation

Date: 2026-09-06

## Root cause

The Phase A–M live markers establish that the custom module reached
`usb_function_register()` and received `-EEXIST`. The ABI audit matched all
five required `struct usb_function_driver` offsets. The failure was therefore
a registry name collision: the existing vendor `usb_net` owns function-driver
name `ncm`.

The v3 candidate is frozen. The v4 candidate changes only the custom
ConfigFS function-driver registration identity to `t6a_ncm`; the vendor
`usb_net`, its `ncm.gs8` instance, and CDC NCM descriptors are unchanged.

## Static gates

```text
CUSTOM_USB_FUNCTION_DRIVER_NAME=t6a_ncm
USB_FUNCTION_DRIVER_NAME_COLLISION=0
STRUCT_MODULE_FINAL_GATE=PASS
MODVERSION_GATE=PASS
VERMAGIC_GATE=PASS
IMPORT_CRC_UNKNOWN_COUNT=0
NET_DEVICE_FINAL_ELF_MATCH_COUNT=9
NET_DEVICE_FINAL_ELF_MISMATCH_COUNT=0
SET_NETDEV_DEV_EMITTED=NO
UNAPPROVED_NATIVE_NETDEV_ACCESS=0
USB_FUNCTION_INSTANCE_FINAL_ELF_GATE=PASS
USB_FUNCTION_DRIVER_FINAL_ELF_GATE=PASS
F_NCM_OPTS_LAYOUT_AUDIT=PASS
DUPLICATE_EXPORT_COUNT=0
REJECTED_OFFSET_SCAN=PASS
REPRODUCIBLE_BUILD=PASS
FINAL_ELF_VALIDATION=PASS
```

The v4 artifact SHA-256 is:

```text
56fd9b93583dba5c5b17c2986cf4b5b485e147eea3dd89fac3b7f510ad762211
```

## Live loader and ConfigFS instance gates

The vendor module remained loaded throughout. The UDC stayed unbound and no
configuration symlink, function link, host cable, enumeration, IP setup, or
traffic test was performed.

```text
USB_FUNCTION_REGISTER_RC=0
CUSTOM_NCM_MODULE_LOAD=PASS
MODULE_LIVE_VISIBILITY=PASS
CUSTOM_NCM_30S_STABILITY=PASS
CUSTOM_NCM_MODULE_UNLOAD=PASS
CONFIGFS_INSTANCE_CREATE=PASS
CUSTOM_NCM_INSTANCE_VISIBLE=yes
CONFIGFS_INSTANCE_REMOVE=PASS
CUSTOM_NCM_POST_CONFIGFS_UNLOAD=PASS
CUSTOM_NCM_LOADER_GATE=PASS
CUSTOM_NCM_CONFIGFS_INSTANCE_GATE=PASS
KERNEL_OOPS=0
WDT=0
SPONTANEOUS_REBOOT=0
SSH_STABLE=yes
```

The management ICMP check did not receive replies during the stability
window; the management SSH session remained stable and the device uptime
continued. This is recorded as transport observation only, not as a custom
NCM data-path result.

## Function-link test status

```text
CUSTOM_NCM_FUNCTION_LINK_TEST_READY=yes
CUSTOM_USB_NIC_FIRST_PACKET=NOT_REACHED
UDC_BIND=NOT_TESTED
HOST_ENUMERATION=NOT_TESTED
```

The function-link test, UDC bind, Windows enumeration, IP configuration, and
traffic remain intentionally out of scope for this gate.
