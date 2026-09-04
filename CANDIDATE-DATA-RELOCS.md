# Candidate ConfigFS data layout

Artifact: `candidate/20260904/artifacts/usb_f_ncm.ko`.

* `ncm_func_type`: `.rodata+0x60`, size `0x28`.
* `ct_owner`: relocation at `.rodata+0x60` to `__this_module`.
* `ct_item_ops`: relocation at `.rodata+0x68` to `.data+0x1b8`.
* `ct_group_ops`: NULL.
* `ct_attrs`: relocation at `.rodata+0x78` to `.data+0xf0`; offset is `0x18`.
* `ct_bin_attrs`: NULL.
* `ncm_attrs`: `.data+0xf0`, size `0x28`, four attribute pointers plus NULL.
* Attribute objects: `.data+0x118`, `0x140`, `0x168`, `0x190`, each size
  `0x28`; their show/store callbacks resolve to the candidate text.
* `ncm_alloc_inst`: `.text+0x1928`; `ncm_alloc`: `.text+0x0a64`.

The actual candidate ELF therefore contains the table and callback pointers;
source presence alone was not used as PASS evidence.
