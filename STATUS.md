# T6A current truth

Updated 2026-09-06.

- CURRENT_PHASE: CUSTOM_NCM_FUNCTIONAL_PERFORMANCE_TUNING
- CURRENT_CANONICAL_CANDIDATE: candidate/t6a-usb-ncm-canonical-v6
- CANONICAL_SHA256: 8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799
- CANONICAL_V6_LIVE_VALIDATED: yes
- WINDOWS_ENUMERATION: PASS
- BIDIRECTIONAL_IPV4: PASS
- UDC_BIND: PASS
- UDC_SPEED_CAPABLE: super-speed-plus
- KNOWN_WORKING_USB_SPEED: super-speed
- CANONICAL_V6_RECORDED_BASELINE_APPROX: 340-353 Mbit/s

## Proven

- external custom CDC-NCM module loads on stock T6A Linux 5.4.238
- custom ConfigFS function name `t6a_ncm` avoids vendor `ncm` registration collision
- UDC bind succeeds
- Windows 11 binds Microsoft UsbNcm.sys
- bidirectional IPv4 traffic succeeds
- canonical v6 artifact SHA256 is fixed and preserved
- vendor-private net_device / netdev_queue compatibility offsets used by canonical v6 are documented in ABI-MANIFEST.md

## Current work

Canonical v6 is the reproducibility baseline.

Performance experiments newer than the canonical-v6 baseline must not silently replace it.
Each promoted performance candidate requires its own immutable artifact, SHA256,
evidence, and Gate-0 provenance record.

## Safety

Never run `sbat6_usb_role_runtime2.ko role=2`.

Faulting or experimental candidates must not overwrite canonical-v6.

The authoritative build/provenance process is:
`docs/T6A_AUTONOMOUS_LOOP_V1.md`.
