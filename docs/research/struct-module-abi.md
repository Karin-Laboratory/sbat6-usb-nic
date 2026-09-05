# T6A vendor `struct module` ABI investigation

## Evidence boundary

The retained vendor corpus contains 157 module files. 156 have a valid
`.gnu.linkonce.this_module` symbol/section; one malformed artifact is excluded
from field statistics. Across the valid samples, the common section size is
`0x340` and the module-name field is at `0x18` in all 156 samples.

For modules exposing both callbacks, relocations repeatedly identify `init` at
`0x150` and `cleanup` at `0x328`. These are the only two useful relocation
anchors currently recovered. Six valid modules do not expose both callback
relocations, which is compatible with modules without both callbacks.

The raw vendor module files are not redistributed in this repository. Public
records contain counts, offsets, classifications, and reproducibility tooling
only; proprietary firmware and potentially restricted binary dumps remain
outside the repository.

## Compiler comparisons

The arm64 5.4.238 compiler oracle produces:

| layout source | size | init | cleanup/exit | result |
| --- | ---: | ---: | ---: | --- |
| upstream Linux 5.4.238 | `0x280` | `0x150` | `0x258` | rejected |
| MediaTek Android lineage | `0x2c0` | `0x150` | `0x258` | rejected |
| lineage plus known conditional groups | `0x340` | `0x158` | `0x2c0` | rejected |

The last row demonstrates why matching the total size is insufficient: it
changes earlier offsets and still misses the observed cleanup relocation.

## Runtime oracle

Read-only sysfs inspection observed
`/sys/module/<module>/sections/.gnu.linkonce.this_module` for 157 loaded
modules. This supplies runtime section addresses and module placement context,
but neither BTF nor `/proc/kcore` was available. Consequently no raw runtime
`struct module` bytes, runtime name offset, or runtime callback offset is
claimed here.

## Gate policy

```text
STRUCT_MODULE_HOLDOUT_PASS=NOT_RUN
VENDOR_OPAQUE_BLOCK_PROVEN=NO
STRUCT_MODULE_LOADER_ABI_PROVEN=no
LIVE_TEST_AUTHORIZED=no
```

Only two relocation anchors are not enough to infer a vendor-specific opaque
block. Do not add guessed padding, patch an ELF, or load a candidate. The
candidate must first reproduce independent anchors and pass hold-out
validation. A live test is permitted only when independent ABI evidence
converges.
