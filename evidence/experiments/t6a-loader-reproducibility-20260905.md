# T6A loader reproducibility experiment — 2026-09-05

Offline clean-build experiment only. No copy to T6A, module load, ConfigFS,
UDC bind, or candidate live test was performed.

```text
BUILD_A=PASS
BUILD_B=PASS
ELF_RECORDS_A=82
ELF_RECORDS_B=82
MODULE_LAYOUT_A=0x3a3eb6e9
MODULE_LAYOUT_B=0x3a3eb6e9
VENDOR_CRC_MISMATCH_A=0
VENDOR_CRC_MISMATCH_B=0
VERMAGIC_A=5.4.238 SMP mod_unload modversions aarch64
VERMAGIC_B=5.4.238 SMP mod_unload modversions aarch64
__versions=IDENTICAL
.text=IDENTICAL
.rodata=IDENTICAL
.modinfo=IDENTICAL
ABI_RELEVANT_CODEGEN=IDENTICAL
FULL_ELF=NOT_BIT_IDENTICAL
LOADER_GATE_REPRODUCIBLE=PASS
```

The full ELF hashes differed because independently copied build paths affect
retained debug/provenance sections. The pass applies to the reproduced
module-layout-v2 source/configuration; it is not a claim that the older
`052318` artifact itself has an immutable exact-source bundle.
