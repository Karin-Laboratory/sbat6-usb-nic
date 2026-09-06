# Corrected custom NCM v6 artifact

This directory contains the source and final ELF for the working custom
external NCM v6 baseline. The function-driver registration name is `t6a_ncm`,
avoiding the vendor `usb_net` collision on `ncm`.

The module SHA256 is recorded in `SHA256SUMS`. ABI details are in
`ABI-MANIFEST.md`; the full baseline record is in
`docs/t6a-custom-ncm-v6-baseline.md`.
