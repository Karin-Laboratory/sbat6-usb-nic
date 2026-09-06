# 65532 candidate v1 reproducibility status

Status: **B** — the corresponding source inputs are present, but a clean
build producing the published module SHA has not yet been reproduced.

Published artifact:

```text
t6a_usb_ncm_65532_candidate_v1.ko
SHA256  7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1
```

The source files and public build inputs are under
`driver/t6a-ncm-65532-ntb-candidate-v1/` and `repro/`. A clean build using
Linux 5.4.238, the recorded ARM64 configuration, the aarch64 cross compiler,
and the available vendor symbol version input completed successfully, but
produced SHA256 `218facacf102ac53e13edc907a8b3f2b56b892871756c5c3c6b56618d00b0c1c`.
That output is not the published artifact and must not be substituted for it.

The published binary remains available for inspection and download, but the
source/binary pairing is currently provenance-based rather than clean-build
SHA-proven. Do not describe this release as reproducible until the exact
published SHA is independently regenerated.
