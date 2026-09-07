# 65532 candidate v1 reproducibility status

Status: **B2** — the clean build does not match in executable code. The
published binary is retained as a live-validated asset, but its corresponding
source is not asserted.

Published artifact:

```text
t6a_usb_ncm_65532_candidate_v1.ko
SHA256  7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1
```

The public source inputs are under
`driver/t6a-ncm-65532-ntb-candidate-v1/` and `repro/`. A clean build using
Linux 5.4.238, the recorded ARM64 configuration, the aarch64 cross compiler,
and the available vendor symbol version input completed successfully and
produced SHA256
`a9477d52e129f78c2dc0ec93ed01c9ec29a9ffb5e2b3cf50aae7d3474d410cfd`.
That output is not the published artifact and must not be substituted for it.

The decisive evidence is section-level: `.text` differs
(`11646a5b…` versus `499db820…`) and normalized `objdump -drwC` differs in
`ncm_alloc_inst` and subsequent code. `.data`, `__versions`, `.modinfo`,
vermagic, module name, and normalized modinfo are equal, but those metadata
matches do not make this B1. The complete table and command inputs are in
`evidence/reproducibility/v1-elf-comparison-20260907.md`.

The published binary remains available for inspection and download as a
live-validated asset. Do not describe the public source as its corresponding
source, and do not recommend v1, until a new provenance investigation resolves
the B2 executable mismatch.
