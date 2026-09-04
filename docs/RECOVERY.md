# Recovery

Recovery is always performed over `raspi2 -> LAN/SSH -> T6A`. Do not use ADB for T6A management; the USB cable is the NCM data plane. Keep `br-lan` separate from `ncm0`.

Common failure state:

- `ncm.gs8` exists but `configs/b.1/f5` is absent;
- `ncm0` is absent or has no carrier;
- UDC is unbound or `not attached`;
- a cold boot removed RAM-only ConfigFS changes;
- MAC addresses may be regenerated;
- Windows static IP may need to be reapplied.

The recovery helper verifies the function and existing `f1`–`f4`, creates or validates `f5 -> ncm.gs8` using `readlink -f`, unbinds with `echo > "$UDC"`, rebinds `11201000.usb`, and restores the T6A NCM address. It does not restart `usb.init`, touch ADB, change role/mode/GPIO/VBUS, or force-unload a module.

Do not run a recovery script blindly against a changed ConfigFS layout. Capture state first and stop if expected links are missing. The cold-boot and failed candidate reconstruction records in `evidence/experiments/` are part of the recovery procedure.
