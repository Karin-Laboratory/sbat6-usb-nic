# T6A autonomous research loop v2

This is an offline audit contract. Candidate build/load, ConfigFS mutation,
UDC bind, and Windows testing remain prohibited until all hard gates pass.

## v1 process failure

The v1 process allowed fields already present in the direct-access inventory to
be omitted from candidate admission. V2 makes the machine-readable ABI
manifest the only source of truth. Assertions and gates are generated from
the same records, so `CANDIDATE_DIRECT_ACCESS=yes` mechanically implies
`GATE_REQUIRED=yes`; a known field cannot be ungated.

## Hard gates

1. `GATE0_MANIFEST_IDENTITY`: one manifest fixes absolute source/header/config
   paths and hashes, autoconf, preprocessed TUs, `.cmd`, compiler/link
   commands, objects, `mod.c`, `Module.symvers`, CRC maps, final `.ko`, active
   Image, runtime kallsyms, and vendor `usb_net.ko`.
2. `SOURCE_MANIFEST_COVERAGE_GATE`: extract accesses from every actually linked
   TU and require `SOURCE_MANIFEST_COVERAGE=100%` and
   `UNGATED_DIRECT_ACCESS_COUNT=0`.
3. `INVENTORY_GATE_COVERAGE_GATE`: direct-access records require TU assertion,
   vendor evidence, and final-ELF inspection. Missing vendor offset is
   `BLOCKED_UNKNOWN_VENDOR_OFFSET` and blocks promotion.
4. `ACTIVE_IMAGE_IDENTITY_GATE`: join boot slot, boot partition, payload,
   decompressed Image, release, and independently captured raw
   `/proc/kallsyms` in one manifest.
5. `VA_IMAGE_MAPPING_GATE`: correlate at least five symbols from different
   regions. Each record contains runtime VA, Image offset, byte comparison,
   string context, call-graph context, and slide. Numeric subtraction alone is
   not proof.
6. `VENDOR_PRODUCER_GATE`: reconcile producer accesses in `usb_net.ko` with
   vendor source lineage and active Image consumers. Source-only or binary-only
   inference is never silently promoted.
7. `PIECEWISE_LAYOUT_GATE`: represent layout as regions and transitions;
   single-padding/shift models are forbidden. Sol selects the next strongly
   provable field by information gain around each transition.
8. `TU_ASSERT_GATE`: assertions execute in the actual TU; retained
   preprocessed TU, `.cmd`, and source hashes match the manifest.
9. `FINAL_ELF_CODEGEN_GATE`: exact ELF inspection checks every manifest field,
   private-base derivation, allocation, callback, and rejects stale generic
   offsets in executable sections.
10. `LOADER_REPRODUCIBILITY_GATE`: two clean runs agree on UND, `__versions`,
    `module_layout`, vermagic, and CRC mapping. The old `modcrc.tsv` is only a
    comparison input. Exact 052318 is classified as Case A/B/C read-only.
11. `RESET_STONE_2`: hostile review checks missing inventory/gates, inferred
    offsets, CRC provenance, stale codegen, lifetime/refcount, callback ABI,
    and unnecessary private-ABI exposure.

## Manifest and extraction contract

The sole source is `evidence/manifests/t6a-abi-manifest-v2.json`. Each field or
derived access in `struct net_device`, `struct eth_dev`,
`usb_function_instance`, `f_ncm_opts`, and other private structs touched by the
link closure has these keys:

```text
STRUCT FIELD CANDIDATE_DIRECT_ACCESS KERNEL_CONSUMED VENDOR_PRODUCER_ACCESS
SOURCE_LOCATION GENERIC_OFFSET VENDOR_OFFSET VENDOR_EVIDENCE CONFIDENCE
ACTUAL_TU_OFFSET TU_ASSERTION_REQUIRED TU_ASSERTION_PRESENT
FINAL_ELF_EXPECTED FINAL_ELF_OBSERVED FINAL_ELF_GATE GATE_REQUIRED GATE_STATUS
```

Human inventory, BUILD_BUG_ON lists, and ELF audit lists are generated views
only. Every loop records `SOL_LOOP_V1_DEFECTS`, `SOL_LOOP_V2_CHANGES`, the
information-gain field selected, evidence provenance, confidence, and open
alternatives. Findings A/B/C remain open until explicitly resolved or
retracted.

## Current disposition

```text
AUTONOMOUS_LOOP_V2=DESIGNED_OFFLINE
ABI_MANIFEST_SYSTEM=IN_PROGRESS
ACTIVE_IMAGE_IDENTITY=PARTIALLY_PROVEN
VA_IMAGE_MAPPING=FAIL
052318_MODVERSIONS_CONTRADICTION=RESOLVED_CASE_B
LOADER_GATE_REPRODUCIBLE=NO
PIECEWISE_NET_DEVICE_MAP=INSUFFICIENT
VENDOR_LINEAGE_RECONSTRUCTION=INCOMPLETE
RESET_STONE_2_READY=no
```
