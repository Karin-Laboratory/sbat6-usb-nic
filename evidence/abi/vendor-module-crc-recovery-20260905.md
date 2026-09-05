# T6A vendor module CRC recovery — 2026-09-05

## Decision

```text
VENDOR_MODULE_CRC_RECOVERY_COMPLETE
BLOCKER=VENDOR_CRC_MAP_INCOMPLETE -> resolved offline
LIVE_MINIMAL_TEST_READY=yes
```

This was an offline-only investigation. No T6A connection, file transfer,
module load, ConfigFS operation, UDC operation, reboot, or live test was done.
The original 74-entry map was not modified.

## Inventory and provenance

The authoritative saved vendor module set is:

```text
../vendor-workspace/work/terminal6-kmods/all-complete/*.ko
```

It contains 157 `.ko` files. The retained `README-driver-build.md` identifies
these as the 157 modules recovered from Terminal 6; their ELF metadata is
arm64 relocatable, and sampled vendor-specific modules report
`5.4.238 SMP mod_unload modversions aarch64`. The set contains the exact
previously saved T6A `usb_net.ko` (SHA256
`271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f`).

The parallel `all/` directory contains another 157-file copy; 156 hashes are
identical to `all-complete/`, with only `nls_cp949.ko` differing. It was treated
as a duplicate recovery set, not as an independent confidence source.

Other saved `.ko` files were classified as local upstream/build/candidate
outputs, including `tmp-kernel-out.*`, `out-linux-5.4.238-air6-upstream`,
candidate artifacts, and locally built compatibility modules. They were not
used for vendor CRC adoption. No provenance-unknown or upstream CRC was used.

For every file in `all-complete/`, the following were inspected or recorded:
path, SHA256, ELF type/architecture, `.modinfo` vermagic, undefined symbols,
and `__versions`. The complete set extraction summary was:

```text
modules scanned : 157
records found   : 5015
unique symbols  : 1422
unique CRC pairs: 1422
CRC conflicts   : 0
```

## Recovered missing symbols

The values below came directly from the `__versions` section of the listed
vendor `.ko`; they are not calculated or inferred.

| symbol | CRC | source module | module SHA256 | evidence path |
|---|---:|---|---|---|
| hrtimer_init | `0x1ee7d3cd` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| kmem_cache_alloc | `0x2f2cca69` | nf_conncount.ko | `56f6191de2347b18321a9505603dcadfa151e2db24a4503adfdb8781de9782a3` | `work/terminal6-kmods/all-complete/nf_conncount.ko` |
| usb_assign_descriptors | `0x11ebaf0f` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| usb_ep_alloc_request | `0xa0e62d4b` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| usb_ep_dequeue | `0xc8ea074a` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| usb_ep_disable | `0xc41263c7` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| usb_ep_enable | `0x6bfad17f` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| usb_ep_free_request | `0xa36ea15e` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| usb_ep_queue | `0x0ffaa944` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |
| usb_ep_set_halt | `0x40f79de7` | usb_net.ko | `271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f` | `work/terminal6-kmods/all-complete/usb_net.ko` |

`readelf -sW` and `aarch64-linux-gnu-nm -u` found the target imports in
`usb_net.ko` and `nf_conncount.ko` as expected. All ten entries were present
in the vendor module `__versions` records. The full recovered set had zero
same-symbol CRC conflicts.

## Extended map and offline rebuild

The new map is separate from the original:

```text
candidate/20260905-mtk-fi-compat/abi/vendor-kimage-extended.Module.symvers
SHA256=b259e638ada0a638c3b0142e1bb7ee604b9e5d718dd944615175f2c9d74a041a
```

It contains the original 74 entries plus the ten recovered values. The
module-source provenance is retained in this report; the kbuild source column
is `vmlinux` so the imported vendor exports do not become false module
dependencies.

Offline rebuild artifact:

```text
candidate/20260905-mtk-fi-compat/artifacts/usb_f_ncm-extended.ko
SHA256=1fb49fd6cf347e2676327d92a22808ee0d767792dcbc52261d2d41b81b0afc06
```

## Gate

```text
kernel actual imports CRC = 74/74
telemetry CRC = 7/7
module_layout = 0x3a3eb6e9
structural ABI = PASS
vermagic = PASS
RESULT=PASS
LIVE_MINIMAL_TEST_READY=yes
```

The 74 kernel imports exclude the separate `module_layout` ABI guard; the
rebuilt ELF has 81 undefined symbols total (74 kernel + 7 telemetry) and 82
version records including `module_layout`. The existing diagnostic shell gate
counts that guard in its raw equality check, so its unmodified count check is
not used as the result here; direct final-ELF CRC comparison is the gate.

The artifact remains offline-only. It has not been copied to or loaded on
T6A.
