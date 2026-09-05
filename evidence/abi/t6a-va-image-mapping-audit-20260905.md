# Active kernel VA to Image mapping audit — 2026-09-05

This is a read-only, current-boot-scoped audit. The crash boot's pstore offset
is kept separate from the current boot's kallsyms. The ARM64 Image header was
decoded from the recovered `boot_b` Image: `text_offset=0x80000`,
`image_size=0x1b69000`, `flags=0xa`, magic `ARMd`.

The current kallsyms capture supplies runtime addresses, including
`_stext=0xffffffc010100800`, `register_netdevice=0xffffffc0107d6260`, and
eleven further independent core symbols. It does not supply runtime instruction
bytes. `/proc/kcore` is unavailable, so no byte equality, function boundary,
branch-target, literal-reference, or caller/callee proof is presently possible.

The diagnostic subtraction from `0xffffffc010000000` is retained only as a
candidate hypothesis. It is not promoted to a mapping rule. In particular,
`CURRENT_BOOT_KASLR_SLIDE` remains `UNPROVEN`; `CRASH_BOOT_KASLR_SLIDE=0x80000`
comes only from pstore and must not be reused for the current boot.

Machine-readable record: [mapping model](t6a-va-image-mapping-model-20260905.json).

```text
CURRENT_BOOT_KASLR_SLIDE=UNPROVEN
CRASH_BOOT_KASLR_SLIDE=0x80000
VA_IMAGE_MAPPING_SAMPLE_COUNT=0
VA_IMAGE_MAPPING_CONFLICT_COUNT=0
VA_IMAGE_MAPPING=FAIL
REGISTER_NETDEVICE_EXACT_FAULT=UNPROVEN
EVIDENCE_STATUS=FAIL
```
