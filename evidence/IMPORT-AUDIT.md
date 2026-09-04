# Initial import audit — 2026-09-04

## Imported

- 45 T6A CDC-NCM / USB experiment records from `evidence/experiments/`.
- Recovery and inspection scripts from `tools/t6a-*`.
- Observation-only telemetry source, Makefile, design, symbol and static audits.
- Fast-route ABI/preflight source, Makefile, README and static audit.
- Redacted public design and safety documentation.

## Classified as evidence, not current behavior

- Aborted ConfigFS teardown and candidate replacement attempts.
- Blocked Windows re-enumeration and no-carrier states.
- Historical tuning trials, including values later restored.
- Older `mode=2` observations: host/transition context only; deprecated as a DEVICE success value.

## Excluded

- `.ko`, object files, build output and large raw captures; source and recorded hashes are retained.
- SIM/IMEI/IMSI/ICCID, credentials, private keys, tokens, and device-unique secrets.
- Unrelated Jabra, ESP32, Zen3, venue, and general SBA6A cellular research.
- Local absolute paths and private host implementation details where they are not needed for reproduction.

Original files remain in the ButlerX working tree. This repository is the public System of Record for the T6A USB NIC/kernel-driver project from this initial commit onward.
