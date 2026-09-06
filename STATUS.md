# T6A current truth

Updated 2026-09-06.

- CURRENT_PHASE: CUSTOM_NCM_FUNCTIONAL_PERFORMANCE_TUNING
- CURRENT_CANONICAL_CANDIDATE: `candidate/t6a-usb-ncm-canonical-v6`
- CANONICAL_SHA256: `8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799`
- CANONICAL_V6_LIVE_VALIDATED: yes
- WINDOWS_ENUMERATION: PASS
- BIDIRECTIONAL_IPV4: PASS
- UDC_BIND: PASS
- KNOWN_WORKING_USB_SPEED: super-speed
- UDC_SUPER_SPEED_PLUS_CAPABLE: unproven
- CURRENT_PERFORMANCE_CANDIDATE_LABEL: `t6a-ncm-65532-ntb-candidate-v1`
- CURRENT_PERFORMANCE_CANDIDATE_SHA256: `7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1`
- CURRENT_PERFORMANCE_CANDIDATE_PROMOTED_IN_REPO: no

## Proven

- external custom CDC-NCM module loads on stock T6A Linux 5.4.238
- custom ConfigFS function name `t6a_ncm` avoids vendor `ncm` registration collision
- UDC bind and Windows UsbNcm.sys enumeration succeed
- bidirectional IPv4 traffic succeeds
- canonical v6 is fixed and preserved as the reproducibility baseline
- MTU3 rejects 65536-byte requests; 65532 bytes is the proven request maximum
- restoring gadget `bcdUSB=0x0320` restored SuperSpeed
- the earlier ~350 Mbit/s result was High-Speed and must not be attributed to NTB size
- T6A -> Windows with the 65532-byte performance candidate:
  - P1 1.492 Gbit/s
  - P4 1.059 Gbit/s
  - P10 1.023 Gbit/s
- Windows -> T6A responds strongly to RPS CPU pipeline separation:
  - P1 best 1.263 Gbit/s
  - P4 best 1.887 Gbit/s
  - P10 best 1.999 Gbit/s
- MTU3 IRQ 305 remained concentrated on CPU0
- softnet_stat drop/time_squeeze remained effectively zero

## Interpretation

Canonical v6 is the immutable reproducibility baseline. It is not the latest
performance candidate.

The current 65532-byte performance candidate has a recorded artifact SHA above,
but its complete source/build/Gate-0 provenance has not yet been promoted into
this clean repository. Do not silently promote it to canonical.

Current performance work is measurement-first.

TX reaches ~1.5 Gbit/s for P1 but falls near ~1.0 Gbit/s for P4/P10.
RX reaches ~2.0 Gbit/s with RPS.

The next priority is instrumentation of NTB fill, DPE count, flush reason,
completion cadence, QMU occupancy where observable, and RX allocation/copy cost.

## Safety

Never run `sbat6_usb_role_runtime2.ko role=2`.

Do not overwrite canonical-v6.

Do not force-enable SG, checksum offload, TSO/GSO/UFO,
`CHECKSUM_UNNECESSARY`, IOC suppression, zero-copy RX, or qdepth=120
without new evidence and a separate reviewed candidate.

The authoritative provenance process is
`docs/T6A_AUTONOMOUS_LOOP_V1.md`.

New humans and agents should start at `docs/AGENT_START_HERE.md`.
