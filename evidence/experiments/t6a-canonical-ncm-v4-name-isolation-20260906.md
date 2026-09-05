# T6A canonical NCM v4 name-isolation experiment

Date: 2026-09-06 JST

## Cause confirmed

Phase A–M established `usb_function_register("ncm") = -EEXIST` after the
custom init marker. The five-field `struct usb_function_driver` ABI audit
matched with zero mismatches. The existing vendor `usb_net` owns `ncm`.

## Candidate

```text
CANDIDATE=t6a_usb_ncm_canonical_v4.ko
SHA256=56fd9b93583dba5c5b17c2986cf4b5b485e147eea3dd89fac3b7f510ad762211
USB_FUNCTION_DRIVER_NAME=t6a_ncm
USB_FUNCTION_DRIVER_NAME_COLLISION=0
V3_SHA256=8f72631cb274792ad5f214bb9182472a3326ca4a38ec3fc2e55c8dc4a683a798
```

The v4 build used the established exact kernel source/output, ARM64
cross-compiler, generated headers, flags, and vendor symbol map. The final
ELF contains `alias=usbfunc:t6a_ncm` and no `usbfunc:ncm`. CDC NCM descriptor
bytes were unchanged from v3. Unknown imports and duplicate exports were 0.

## Live sequence

Baseline was saved before load. The UDC was `not attached`; vendor
`usb_net` was live and remained live throughout. No config symlink, UDC
mutation, cable connection, enumeration, IP setup, or traffic was performed.

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
```

The instance `/config/usb_gadget/g1/functions/t6a_ncm.test0` exposed
read-only `ifname`, `qmult`, `dev_addr`, and `host_addr`; it was removed
without linking it into a configuration. The final unload returned 0 and the
module was absent from both live module views.

```text
KERNEL_OOPS=0
WDT=0
SPONTANEOUS_REBOOT=0
SSH_STABLE=yes
CUSTOM_NCM_FUNCTION_LINK_TEST_READY=yes
CUSTOM_USB_NIC_FIRST_PACKET=NOT_REACHED
UDC_BIND=NOT_TESTED
HOST_ENUMERATION=NOT_TESTED
```

The management ICMP probe had 0/2 replies, while SSH remained stable; this is
recorded as management transport observation and not treated as NCM traffic.

## Public update

Published on branch `compat/t6a-ncm-name-collision-v4`:

```text
GITHUB_REMOTE_MATCH=PASS
GITHUB_DIFF_SANITY=PASS
GITHUB_SECRET_SCAN=PASS
GITHUB_PUBLIC_SANITIZATION=PASS
GITHUB_BRANCH=compat/t6a-ncm-name-collision-v4
GITHUB_COMMIT=1467476
GITHUB_PUSH=PASS
```

Pull request URL:

`https://github.com/everyoneknows/sbat6-usb-nic/pull/new/compat/t6a-ncm-name-collision-v4`
