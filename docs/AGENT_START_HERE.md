# Agent start here

This file routes new agents to the appropriate device-side or host-side task.

## T6B USB host NIC: start here

For AX88179 host NIC builds, go directly to
[the tested build recipe](../driver/t6b-ax88179/README.md), then
[its hardware results](../evidence/reproducibility/t6b-compat-20261001/README.md).
The bundled config, patch, reference symbols, assertions, and build script
are the current starting point. Do not repeat CRC-only ELF rewriting or
reconstruct the known ABI from early failed NCM reports.

For a different NIC, read [the applicability assessment](NIC-APPLICABILITY.md).
The current script is fixed to MII + usbnet + AX88179; successful compilation
of another driver is not evidence of compatibility. The common corrections
are reusable, but driver-specific dependency/access checks remain necessary.

The following section concerns the **T6A USB device-side NCM** project.

## Read in this order

1. `STATUS.md`
2. `candidate/t6a-usb-ncm-canonical-v6/README.md`
3. `candidate/t6a-usb-ncm-canonical-v6/ABI-MANIFEST.md`
4. `docs/T6A_AUTONOMOUS_LOOP_V1.md`
5. `known-non-working/README.md`

Do not reconstruct the current project state by scanning `evidence/` chronologically.
The evidence tree intentionally contains PROVEN, FAIL, RETRACTED, and historical
results.

`STATUS.md` is the current-truth pointer.

## Baseline versus performance candidate

The canonical v6 module is the immutable reproducibility baseline.

The latest performance candidate is separate. At the time of this file,
`t6a-ncm-65532-ntb-candidate-v1` has artifact SHA256
`7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1`
but has not yet completed clean-repository Gate-0 promotion.

Do not replace canonical v6 with it merely because it is faster.

The canonical v6 `.ko` binary is not committed in this repository. Its
authoritative SHA256 is recorded in
`candidate/t6a-usb-ncm-canonical-v6/SHA256SUMS`.

## Critical corrections

The ~350 Mbit/s to ~1.49 Gbit/s jump was primarily High-Speed to SuperSpeed
after restoring `bcdUSB=0x0320`. Do not attribute that jump to NTB expansion.

MTU3 rejects USB requests of 65536 bytes and reports a maximum of 65532 bytes.

RPS is a proven major RX performance lever. Best observed Windows -> T6A
results are approximately P1 1.263, P4 1.887, and P10 1.999 Gbit/s.

## Hard safety rule

Never run:

`sbat6_usb_role_runtime2.ko role=2`

Do not retry known faulting conditions merely to reproduce a crash.
