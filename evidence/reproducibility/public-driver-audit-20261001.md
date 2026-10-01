# Public-input driver reproduction audit — 2026-10-01

Public baseline: `97f55791dd0de4161cb2a9bd06ab9799ff580a8d` in
`Karin-Laboratory/sbat6-usb-nic`. The audit used a separate Git worktree of
that fetched commit. Existing private build directories were not supplied
as missing public build prerequisites.

## Reproducible public checks

- Both artifact manifests: hashes match.
- Both published driver source manifests: all seven files each match.
- `env -u KERNEL_SRC -u KERNEL_BUILD -u CROSS_COMPILE sh repro/build-65532.sh`:
  exit 2, `KERNEL_SRC: Set KERNEL_SRC to the matching Linux 5.4.238 source tree`.
  No clean kernel/module rebuild was completed by this audit.
- Tracked files do not provide the matching kernel tree, a complete kernel
  patch series or a kernel config. The patch README explicitly states that
  no production patch is included.
- v6 metadata inspection using the new checker and the public reference:
  76 MATCH, 0 MISMATCH, 0 UNKNOWN, exact vermagic, no unversioned undefined
  symbols. [Full result](public-v6-metadata-20261001.json).
- New checker regression suite: six tests pass, covering the published
  artifact, incorrect release, missing reference entries, conflicting maps,
  wrong CRC and truncated ELF. Run `python3 tools/test-module-metadata.py`.

No result above establishes load safety. The checker reads the final ELF
and hashes its reference; it does not validate reference provenance or
structural ABI. An exit code of zero must not trigger an automated load.

## Supplemental local counterexample (not a public-only build)

An existing T6B upstream-built `mii.ko` was compared to the *public* NCM
reference map. It has 3 MISMATCH and 3 UNKNOWN records; no record matches.
[Full result and artifact hash](t6b-natural-mii-public-map-20261001.json).
This module is not shipped here and this comparison is not claimed to be
a fresh public-input reproduction. Its purpose is to identify the exact
missing/mismatching public-map entries for the AX88179 dependency chain.

`module_layout` is `0x6006b85e` in this module versus `0x3a3eb6e9` in the
reference. `netdev_info` and the two ethtool conversion helpers are unknown
to the public map. Unknown does not mean absent from the target kernel.

An earlier local attempt to load Image-CRC-rewritten candidates lost target
management access and required a physical power cycle. No crash stack was
recovered. That experiment is a failed load-safety outcome; it does not
identify a specific faulting instruction. It was not repeated in this audit.

## Result

**BLOCKED for arbitrary safe driver generation from public inputs.**
Published supplementation consists of the reusable metadata checker,
negative tests, the zzzzz-method summary with evidence boundaries, an
input-gap table, and correction of the stale v1 source-pairing claim.
See [the reproduction guide](../../docs/DRIVER-REPRODUCTION.md).
Kernel reconstruction and AX88179 structural ABI completion remain open.
