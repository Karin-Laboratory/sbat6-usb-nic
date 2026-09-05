# T6A actual `register_netdevice` text recovery — 2026-09-05

## Scope and safety

This investigation followed the requested fail-closed order. All T6A reads
below were performed through `the approved read-only management path`.
No module, ConfigFS, UDC, GPIO, USB-role, network, boot, or flash operation
was performed. No candidate was created or loaded.

## Runtime capability inventory

Observed on T6A:

```text
Linux T6A 5.4.238 #0 SMP Mon Apr 17 13:15:36 2023 aarch64 GNU/Linux
kptr_restrict=0
/proc/kallsyms: -r--r--r-- root root 0
/proc/kcore: absent (No such file or directory)
ffffffc0107d6260 T register_netdevice
ffffffc0107d65dc T register_netdev
ffffffc0097dd714 t gether_register_netdev [usb_net]
```

Therefore:

```text
KALLSYMS_REGISTER_NETDEVICE_VISIBLE=yes
REGISTER_NETDEVICE_RUNTIME_ADDR=ffffffc0107d6260
KCORE_PRESENT=no
KCORE_READABLE=no
```

The `/proc/kcore` route is unavailable on this running T6A. No attempt was
made to bypass that restriction.

## Boot-image fallback inventory

The live command line reported:

```text
root=/dev/mmcblk0p39
bootslot=b
```

`/proc/partitions` exposed `/dev/mmcblk0p38` and `/dev/mmcblk0p39`. `blkid`
identified them as:

```text
/dev/mmcblk0p38 PARTLABEL="boot_b" PARTUUID="0fbbafa2-4aa9-4490-8983-5329328505fd"
/dev/mmcblk0p39 PARTLABEL="rootfs_b" PARTUUID="a76e4b2f-31cb-40ba-826a-c0cb0b73c856"
```

This proves the active slot is `b` and identifies `/dev/mmcblk0p38` as the
current boot partition. The partition was streamed with read-only `dd`.

```text
partition=/dev/mmcblk0p38 (boot_b)
partition_size=33554432 bytes
partition_sha256=1316aed38c40ea43a105b7e389efda4aa4f1d9569dbeda2b53580c2dce3f5398
collection_time=2026-09-05 JST (runtime read at 14:44-14:45)
```

The image header was:

```text
magic=ANDROID!
header_version=2
page_size=2048
kernel_size=6313752
ramdisk_size=0
second_size=0
kernel_offset=2048
```

The kernel payload starts at offset `0x800` and is gzip-compressed:

```text
boot_kernel_payload_size=6313752 bytes
boot_kernel_payload_sha256=97d2406111477250fd1a75878b8c4bdd018e5e62632f5839c62b158ca3a329b0
compression=gzip (magic 1f 8b 08)
```

After read-only decompression:

```text
kernel_Image_size=17408008 bytes
kernel_Image_sha256=de3a1bee91314be0a65bd79f60a954d928f2c31cc4861d41f2e90b948d650082
format=Linux kernel ARM64 boot executable Image, little-endian, 4K pages
Linux version=5.4.238 (vendor-author@swdev-120), GCC 9.3.0, 2023-04-17
```

Saved artifacts:

```text
evidence/abi/t6a-boot_b-20260905.bin
evidence/abi/t6a-boot_b-kernel-20260905.bin
evidence/abi/t6a-boot_b-Image-20260905
```

## Runtime VA to Image mapping status

The recovered payload is a raw compressed-kernel output, not an ELF file, so
it has no ELF `PT_LOAD` headers. `/proc/kcore` is absent, so no live ELF
program-header mapping can be established.

The usual arm64 Image placement hypothesis would put the text at the Image
text base, but it is not accepted as proof here. A diagnostic disassembly at
the byte offset numerically corresponding to the visible runtime address did
not provide an independently proven symbol boundary: the bytes around the
candidate location contain a function prologue at `0x7d622c`, while the
runtime kallsyms value numerically corresponds to `0x7d6260` under that
hypothesis. This discrepancy means the VA-to-Image mapping and exact symbol
identity remain unproven.

Consequently, no `register_netdevice` function byte window was labelled as
actual text, and no `+0xb4` opcode was declared authoritative. In particular,
the following are intentionally not asserted:

```text
REGISTER_NETDEVICE_B4_OPCODE=UNCONFIRMED
REGISTER_NETDEVICE_B4_OPERANDS=UNCONFIRMED
REGISTER_NETDEVICE_ACTUAL_TEXT=UNPROVEN
```

## Oops data-flow evidence retained

The governing bbd228 Oops remains the saved evidence in
`evidence/experiments/t6a-bbd228-udc-bind-isolated-20260905-1423.md`:

```text
pc=register_netdevice+0xb4/0x37c
call_trace=gether_register_netdev+0x34 [usb_f_ncm] -> ncm_bind+0x8c
x0=0
x1=1f73025eabcb7b00
NULL dereference at 0x0
WDT=YES (wdt_status=0x2)
```

The complete register lines were recovered read-only from the live pstore
file and saved as:

```text
evidence/abi/t6a-bbd228-pstore-console-20260905.txt
sha256=10d342acd462f912572e0ff6cba1ab0bd5ba8a2879ab09e037372efd7d089315
size=79021 bytes
```

The dump additionally records:

```text
Kernel Offset: 0x80000 from 0xffffffc010000000
sp=ffffffc021ae3a20
x29=ffffffc021ae3a20 x28=ffffff8067aa3c88
x27=ffffff8067aa3800 x26=ffffff8052f9e6b0
x25=ffffff80779e4550 x24=ffffff806683c198
x23=ffffff80779e4520 x22=ffffff805df80930
x21=ffffffc0111688c0 x20=0000000000000000
x19=ffffff805df80000 x18=0000000000000000
x17=0000000000000000 x16=0000000000000000
x15=0000000000000000 x14=0000000000000000
x13=0000000000000020 x12=0000000000000020
x11=0101010101010101 x10=ffffff7f7f7f7f7f
x9=fefefdff2f617274 x8=ffffffffffffffff
x7=fefefefefefefefe x6=ffffff805df80004
x5=0000000000000000 x4=ffffffffffffffff
x3=0000000030627375 x2=0000000000000004
x1=1f73025eabcb7b00 x0=0000000000000000
```

The raw values are preserved in the pstore file. The pstore also confirms
`lr=register_netdevice+0xa8/0x37c` and the complete call trace through
`register_netdev`, `gether_register_netdev`, and `ncm_bind`.

Because the actual instruction at `+0xb4` and its preceding instructions are
not proven from the running kernel, register-to-field data flow is not
claimed. `x0=0` is not treated as proof of a NULL `net_device`.

## Conclusion

```text
KCORE_TEXT_EXTRACTION=unavailable (/proc/kcore absent)
BOOT_KERNEL_IMAGE_RECOVERED=yes
ACTUAL_VENDOR_KERNEL_TEXT=UNPROVEN
REGISTER_NETDEVICE_EXACT_FAULT=UNPROVEN
ROOT_CAUSE=UNPROVEN
NEW_CANDIDATE_SHA256=
NEXT_LIVE_TEST_READY=no
```

The current evidence proves that the active `boot_b` partition and its kernel
Image were recovered read-only, but does not yet prove a trustworthy mapping
from runtime kallsyms VA to the `Image` bytes. Candidate creation, patching,
and another UDC bind remain prohibited.
