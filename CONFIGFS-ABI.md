# T6A ConfigFS ABI audit (2026-09-05)

Scope: read-only static audit of the Linux 5.4.238 arm64 candidate and the
saved vendor `usb_net.ko`. No new candidate was built, loaded, or sent to T6A.

## Result

The strongest direct test does **not** show a `config_item_type` public-layout
mismatch. Candidate `ct_attrs` is at `+0x18`; the vendor type-object candidate
is `.rodata+0xb48`, and its attribute-table relocation is at `.rodata+0xb60`
(also `+0x18`) to `.data+0x958`. The candidate attribute array is `.data+0xf0`.

The same placement is recovered for `usb_function_driver`: `name +0x00`,
`mod +0x08`, `alloc_inst +0x20`, `alloc_func +0x28`.

This weakens `CONFIGFS_PUBLIC_ABI_MISMATCH` and
`USB_FUNCTION_DRIVER_ABI_MISMATCH`. It does not prove the vendor's private
implementation/lifecycle is interchangeable, nor does it prove
`config_group`/`usb_function_instance` internals from the vendor binary alone.

## Classification

`PRIVATE_LAYOUT_DIFFERENCE_ONLY` is the correct treatment for the 8-byte
`f_ncm_opts` difference. The directory-without-attributes observation remains
`NOT_PROVEN`; the remaining leading candidates are `VENDOR_CONFIGFS_EXTENSION`
and `VENDOR_U_ETHER_DEPENDENCY`. Candidate creation remains blocked.

The vendor object is a relocatable ELF with local symbols removed/retained in
an uneven way, so the type-object identification is a relocation-based
inference, not a vendor-source proof.
