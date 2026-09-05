# T6A bbd228 isolated UDC-bind — 2026-09-05

## Corrected Sol audit

```text
SOL_ESCALATION_TIME=2026-09-05T14:22+09:00 JST
SOL_PREVIOUS_ASSUMPTION_CORRECTED=yes
SOL_BBD228_KNOWN_OOPS=none attributable before this attempt
SOL_RECOMMENDS_UDC_BIND_TEST=yes, conditional single attempt
SOL_DIAGNOSIS=old exact Oops belongs to 1fb49f; bbd228 bind boundary remained unproven
SOL_RECOMMENDED_NEXT_ACTION=one marker-backed isolated bind with Windows disconnected
```

## Artifact and preflight

The requested candidate and telemetry were SHA-256 verified on T6A immediately
before loading:

```text
candidate=bbd228debf2c49a55a68729b1a09eff3e8bba34bb6bb0cb7c085b0158ae88e3c
telemetry=94b157ad17cbe678f2484d058b2e5f8231e5ed6de6fe33f8349ee1588ca6ebf5
```

Windows remained disconnected. Management SSH through raspi2 was available.
Vendor `usb_net` was released (`6 -> 0`) without removing ACM, FFS, or
mass-storage links. Candidate load, ConfigFS attributes, absolute `f5` link,
and the 30-second pre-UDC interval completed.

## Result

The only actual bbd228 UDC bind write was preceded by `B07_BEFORE_UDC_BIND`.
SSH disconnected immediately afterward. After reboot, pstore contained this
new bbd228-owned fault:

```text
BBD228_UDC_BIND=FAIL
GETHER_REGISTER_NETDEV_LIVE=FAIL
NET_DEVICE_ABI_LIVE=FAIL
NULL dereference at 0x0
pc: register_netdevice+0xb4/0x37c
call trace: gether_register_netdev+0x34 [usb_f_ncm] -> ncm_bind+0x8c
x0=0, x1=1f73025eabcb7b00
WDT=YES (pstore reports wdt_status=0x2; reboot followed)
reboot=YES
Oops=YES, bbd228 own new fault
```

The prior `1fb49f` Oops was not reused. No Windows enumeration or traffic was
attempted. T6A is currently responsive with vendor `usb_net` loaded, `mode=3`,
`GPIO322=LOW`, UDC `not attached`, and no `ncm0`. Persistent markers and the
raw pre-bind pstore are retained on T6A at:

```text
/root/butlerx-bbd228-udc-20260905-1423/
```

The candidate is now permanently stopped pending analysis of this new fault.

```text
NEXT_TEST=WINDOWS_ENUMERATION prohibited; changed candidate/static analysis required
```
