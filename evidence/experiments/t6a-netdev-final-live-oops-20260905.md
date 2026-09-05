# T6A new netdev-private candidate live attempt — 2026-09-05

## Result

The candidate passed static ABI gates and loaded through the controlled
`raspi2 -> T6A` path, but the isolated UDC bind caused a fresh kernel Oops and
WDT reboot. Windows was disconnected throughout. The candidate is permanently
live-banned pending offline ABI reconstruction.

```text
ATTEMPT_TIME=2026-09-05T15:46:13+09:00 JST
CANDIDATE_SHA256=052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f
TELEMETRY_SHA256=94b157ad17cbe678f2484d058b2e5f8231e5ed6de6fe33f8349ee1588ca6ebf5
WINDOWS_CONNECTED=no
STATIC_ABI=PASS
PRE_UDC_STABLE_30S=PASS
UDC_BIND_LIVE=FAIL
WINDOWS_NCM_ENUMERATION=NOT_RUN
KERNEL_OOPS=1
WDT=1
SPONTANEOUS_REBOOT=1
```

## Reached gates

Vendor `ncm.gs8` was absent; only `ecm.gs8` and `rndis.gs4` were removed.
`usb_net` was unloaded successfully. Telemetry and candidate insertion,
ConfigFS instance creation, attributes, `f5 -> ncm.gs8`, and the 30-second
pre-UDC interval all completed. No ACM, FFS, mass-storage, ADB, role, flash,
or irreversible security operation was touched.

The first bind write failed with `Resource busy` because the stale UDC value
was still `11201000.usb` while state was `not attached`. Sol audit
`t6a-live-resource-busy-audit-20260905-v2` identified this as stale ConfigFS
state. A changed-condition retry explicitly wrote an empty UDC and verified
it empty before one bind write.

## Fresh fault provenance

The corrected bind then produced this new pstore fault:

```text
NULL dereference at virtual address 0x0
pc : register_netdevice+0xb4/0x37c
lr : register_netdevice+0xa8/0x37c
x0 : 0x0
x1 : 0x9bf8596d9f5cfb00
call trace: register_netdevice -> register_netdev
             -> gether_register_netdev+0x38/0x8c [usb_f_ncm]
             -> ncm_bind+0x8c/0x2d4 [usb_f_ncm]
WDT status: 2; reboot followed
```

Pstore source: `/sys/fs/pstore/console-ramoops-0`, retained on T6A under
`/root/butlerx-live-evidence-20260905-netdev-final`. The prior Resource busy
attempt and the corrected attempt are separated by persistent markers; the
post-bind files were not written because the fault interrupted the SSH
session. A09–A11 from the first script run are invalid and are not used as
stability evidence.

## Sol decision

Sol invocation: `t6a-new-register-netdevice-oops-audit-20260905`, model
`gpt-5.6-sol`, session
`01a07057-b9a5-7350-9e43-24759d185e39`.

Sol diagnosis: static ABI coverage is incomplete. The recovered active Image
and kallsyms mapping show `register_netdevice+0xb0` loads `x0` from
`net_device + 0x1f8`, and `+0xb4` dereferences that pointer. The candidate's
`netdev_ops` store is currently generated at `net_device + 0x218`, leaving the
kernel-consumed `+0x1f8` slot NULL. This is a high-confidence ABI mismatch,
not yet a vendor-kernel defect.

```text
IMAGE_SHA256=de3a1bee91314be0a65bd79f60a954d928f2c31cc4861d41f2e90b948d650082
REGISTER_NETDEVICE_RUNTIME=ffffffc0107d6260
IMAGE_TEXT_BASE=ffffffc010100000
KERNEL_CONSUMED_NETDEV_OPS_OFFSET=0x1f8
CANDIDATE_NETDEV_OPS_STORE_OFFSET=0x218
SOL_LIVE_TEST_READY=no
```

Further live attempts are forbidden. The next action is a changed-condition
offline reconstruction against the original vendor `usb_net.ko` and actual
Image text. The exact vendor offset for every kernel-consumed field must be
re-derived; no blind `+0x10` or isolated pointer write is permitted.

## Recovery

After the WDT reboot, management SSH recovered. T6A returned to vendor
`usb_net` loaded, UDC `not attached`, `current_speed=UNKNOWN`, and no `ncm0`.
No candidate remains loaded.
