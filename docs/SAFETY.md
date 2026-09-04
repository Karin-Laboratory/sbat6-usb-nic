# Safety

- Keep the management LAN available and separate from USB data.
- Before mode changes, ensure the intended USB host is disconnected and the VBUS measurement plan is understood.
- Never use `force rmmod` for the vendor USB provider.
- Do not load a candidate beside the vendor NCM provider without an audited ownership and rollback path.
- Do not use hot-path printk, tracing, or debug logging in throughput tests.
- Do not program eFuses, Secure Boot, Flash Encryption, permanent JTAG disablement, or other one-time settings.
- Redact passwords, tokens, SIM identifiers, IMEI/IMSI/ICCID, private keys, and device-unique secrets from evidence.

A failure is a result. Record it as `REGRESSION`, `BLOCKED`, or `ABORTED`; do not delete it or relabel it as success.
