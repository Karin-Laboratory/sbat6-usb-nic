# 65532-byte NTB candidate v1

## Release status

The published `t6a-ncm-65532-candidate-v1` binary is retained as an asset
because it was loaded on the physical T6A and passed USB configuration, link,
ICMP, and bounded iperf3 tests. The recommended wording is: 「実機検証済みbinary、source pairingはprovenance-based」.
It is not recommended for new use: clean-build
comparison found an executable `.text` mismatch (B2). The public source is a
provenance record only; this release does not assert that it corresponds to
the published binary. `instrumented-v5` is not runtime-validated and is
experimental only; it is not an installation target.

## Tested result

Kernel: Linux 5.4.238, ARM64. The measured direction is shown explicitly:
T6A→Windows receiver throughput was P1 1.490, P4 1.580, P10 1.656 Gbit/s
mean; Windows→T6A was P4 1.923 and P10 1.982 Gbit/s mean. P1 reverse was
unstable (0.893 Gbit/s mean). Results are condition-specific, not a promise
for other hosts or kernels.

## Identity

| item | value |
|---|---|
| module | `t6a_usb_ncm_65532_candidate_v1.ko` |
| SHA256 | `7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1` |
| vermagic | `5.4.238 SMP mod_unload modversions aarch64` |
| license | GPL-2.0-only |

The source bundle is complete and its file hashes are in the source
directories. The module name, vermagic, modversions, and several non-code
sections match the clean build, but executable code does not. This is
reproducibility status B2, not B1 or status A. See [the reproducibility
record](REPRODUCIBILITY-STATUS-65532.md) and the [ELF comparison evidence](evidence/reproducibility/v1-elf-comparison-20260907.md).

## v6 baseline comparison

Canonical v6 remains available as the reproduction baseline. It uses 16 KiB
NTBs, 32 datagrams per TX NTB, and a 300 us flush timeout. v1 changes those
performance variables to 65532-byte NTBs, 64 datagrams, and an 80 us timeout;
the ABI compatibility and gadget integration are otherwise retained. v6 is
the fallback for experiments, not the recommended performance artifact.

## Safety and license

Back up the current module and confirm an independent management path before
changing a live gadget. Do not use force-unload, UDC-driver manipulation,
reboot, or security/eFuse operations as part of installation. Follow the
custom v1 installation is documented in [INSTALL-65532.md](INSTALL-65532.md);
the vendor rollback procedure remains in [docs/RECOVERY.md](docs/RECOVERY.md).
No vendor binary,
private runtime capture, device identifier, credential, or chat transcript
is included in this release.
