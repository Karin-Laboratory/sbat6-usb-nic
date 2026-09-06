# Privacy cleanup — 2026-09-06

Repository ownership and current account references use `Karin-Laboratory`.

Personal workstation paths and management LAN addresses have been replaced with
generic paths or documentation addresses. Device MAC addresses in published
evidence and recovery examples are placeholders, not original measured values.
Configure recovery examples for your own device before running them.

Three obsolete diagnostic binaries contained personal build paths and have been
removed from the current branch:

- `candidate/20260904/artifacts/sbat6_ncm_telemetry.ko`
- `candidate/20260904/artifacts/usb_f_ncm.ko`
- `candidate/20260905-netdev-abi-compat/usb_f_ncm-netdev-abi.ko`

Historical analysis may still refer to their original hashes and filenames;
those references describe withdrawn diagnostic artifacts, not available files.
The current canonical v6 source and binaries have not been modified by this cleanup.
Upstream copyright notices and vendor-authored source attribution are preserved.

This normal cleanup commit does not erase older Git commits or cached copies.
