# Vendor data relocation reconstruction

Artifact: saved T6A vendor `usb_net.ko`, relocatable AArch64 ELF.

## NCM attribute table

`ncm_attrs[]` is inferred at `.data+0x958`: four consecutive relocations at
`+0x00,+0x08,+0x10,+0x18` point to attribute objects `.data+0x9f8`,
`0x9d0`, `0x9a8`, and `0x980`; the fifth slot at `+0x20` is NULL.

The inferred `ncm_func_type` is `.rodata+0xb48`. Its relocations are:

* `+0x00` -> `__this_module` (`ct_owner`)
* `+0x08` -> `.data+0xa20` (`ct_item_ops` candidate)
* `+0x10` -> NULL (`ct_group_ops`)
* `+0x18` -> `.data+0x958` (`ct_attrs`)
* `+0x20` -> NULL (`ct_bin_attrs`)

Therefore vendor estimated `ct_attrs` offset is **0x18**, matching the
candidate compile-time layout. The inference is anchored by the four
attribute-object relocation cluster and the `config_group_init_type_name`
import; vendor source was unavailable.

## Function driver

The inferred vendor `usb_function_driver` starts at `.data+0x928`:

* `+0x00` name -> `.rodata.str1.1+0x1a33`
* `+0x08` mod -> `__this_module`
* `+0x10,+0x18` list fields have no non-zero relocation
* `+0x20` alloc_inst -> `.text.unlikely+0x1c7c`
* `+0x28` alloc_func -> `.text.unlikely+0x1fe8`

This matches candidate offsets `0x00, 0x08, 0x20, 0x28`. The vendor strings
and call graph identify the former as NCM allocation and the latter as NCM
function allocation, but symbol naming is not required for the placement
comparison.
