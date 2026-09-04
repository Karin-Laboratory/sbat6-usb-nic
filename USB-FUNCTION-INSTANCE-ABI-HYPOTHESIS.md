# USB function instance ABI hypothesis

Status: **leading hypothesis; T6A candidate reinsertion remains prohibited**.

## Layouts

All pointer fields are 8 bytes on the AArch64 target. The generic Linux 5.4
layout used by the candidate is:

| member | generic offset |
|---|---:|
| `group` | `0x00` |
| `cfs_list` | after `group` |
| `fd` | `0x98` |
| `set_inst_name` | `0xa0` |
| `free_func_inst` | `0xa8` |
| `sizeof(struct usb_function_instance)` | `0xb0` |

The public MediaTek/Android downstream variant adds `struct usb_function *f`
between `fd` and the callbacks:

| member | vendor-family offset |
|---|---:|
| `fd` | `0x98` |
| `f` | `0xa0` |
| `set_inst_name` | `0xa8` |
| `free_func_inst` | `0xb0` |
| `sizeof(struct usb_function_instance)` | `0xb8` |

This is semantic layout reproduction, not padding-only alignment.

## Three-way evidence

### Candidate ELF

`ncm_alloc_inst` at `.text+0x1928` allocates `0x1b8` bytes and contains:

```text
1988: ADRP/ADD .text+0x840
1990: STR x1, [x19, #168]       // +0xa8
```

The candidate disassembly identifies `.text+0x840` as `ncm_free_inst`.
Therefore candidate `+0xa8` contains `ncm_free_inst`, not `set_inst_name`.

### Vendor ELF

The recovered vendor NCM allocation path (`vendor-objdump-dr.txt`, around
`0x1c7c`) allocates `0x1c0` bytes, initializes a mutex at `+0x198`, and
stores a function pointer at `+0xb0`:

```text
1cb8: mov w1, #0xcc0
1cbc: mov x0, #0x1c0
1d14: add x0, x19, #0x198
1d20: bl  __mutex_init
1d24: ADRP/ADD .text+0x63c8
1d2c: str x0, [x19, #176]       // +0xb0
1d30: bl  gether_setup_name_default
1d38: str x0, [x19, #184]       // +0xb8, net
```

The callback identity is recovered from the unique free/lifecycle path and
relocation/disassembly context; the vendor ELF is partially stripped.
Vendor private offsets also show `net +0xb8`, mutex `+0x198`, and allocation
`0x1c0`, versus candidate `+0xb0`, `+0x190`, and `0x1b8`.

### Sibling allocators

The same vendor object contains sibling ConfigFS instance allocation paths:

| recovered path | callback store | related evidence | status |
|---|---:|---|---|
| NCM | `+0xb0` | alloc `0x1c0`, mutex `+0x198`, net `+0xb8` | confirmed |
| ECM | `+0xb0` | `__mutex_init` at `+0x198`, `gether_setup_name_default` follows | confirmed from disassembly |
| RNDIS | `+0xb0` | sibling `rndis_alloc_inst` strings and instance allocator block | callback offset confirmed; full private-size mapping not required |
| ACM | — | no ACM allocator in this `usb_net.ko` ELF | not applicable to this module |

The sibling comparison strengthens the conclusion that `+0xb0` is the
vendor-family `free_func_inst` position, rather than an NCM-only accident.

### pstore

The raw pstore records a NULL dereference at `0x208` while `cat` opens a
ConfigFS attribute, with PC/LR in `__configfs_open_file`. This matches the
replay's `mkdir RC=0`, directory-only result, and attribute-read failure. It
does not print the callback target, so callback-level attribution is a strong
correlation rather than a direct trace proof.

## Mechanism

Generic ConfigFS `function_make()` calls:

```c
if (fi->set_inst_name)
    ret = fi->set_inst_name(fi, instance_name);
```

With the vendor-family layout, offset `+0xa8` is read as `set_inst_name`.
The candidate puts `ncm_free_inst` at that same offset. The wrong-callback
mechanism therefore explains creation success followed by corruption or an
invalid operation when ConfigFS attributes are opened.

## Root-cause labels

```text
USB_FUNCTION_INSTANCE_ABI_MISMATCH
WRONG_SET_INST_NAME_CALLBACK
USE_AFTER_FREE_AFTER_FUNCTION_MAKE
```

The first is the leading, high-confidence candidate. The third remains
unconfirmed unless a future offline/static or protected trace demonstrates a
free followed by the failing access.

## Gate for any future offline candidate

Only an offline build may be considered after this review. No `insmod`, no
T6A copy, and no runtime test is authorized by this work item. A valid static
gate must show `set_inst_name +0xa8`, `free_func_inst +0xb0`,
`f_ncm_opts.net +0xb8`, lock `+0x198`, and size `0x1c0`, with the actual
MediaTek `f` member in the source type. No performance, telemetry, NTB,
queue, or descriptor changes are permitted.
