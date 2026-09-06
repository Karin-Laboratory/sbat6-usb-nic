# 65532-byte NTB candidate v1

## Recommendation

`t6a-ncm-65532-ntb-candidate-v1` is the recommended artifact for the tested
T6A configuration. It has been loaded on the physical T6A and passed USB
configuration, link, ICMP, and bounded iperf3 tests. `instrumented-v5` is not
runtime-validated and is experimental only; it is not an installation target.

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
directories. The module name, source constants, build inputs, and final ELF
hash were cross-checked against the recorded build and runtime provenance.

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
existing recovery procedure for the target platform. No vendor binary,
private runtime capture, device identifier, credential, or chat transcript
is included in this release.
