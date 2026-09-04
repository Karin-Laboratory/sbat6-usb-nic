# T6A NCM pre-UDC isolation — 2026-09-05

## Result

The live attempt was **blocked before ATTEMPT03**.  No vendor release,
telemetry load, candidate load, ConfigFS mutation, mode/GPIO change, UDC
operation, Windows connection, ping over NCM, iperf, RPS, IRQ tuning, or
reboot was performed in this attempt.

The requested candidate could not be admitted because the exact SHA256 file
was not present on the agent host, raspi2, or T6A:

```text
candidate SHA256 = f07600aa9d8bbec0edc1e05d9ac0ab000d98a353d2a79f89db6242a75d487ce4
telemetry SHA256 = 94b157ad17cbe678f2484d058b2e5f8231e5ed6de6fe33f8349ee1588ca6ebf5
```

The telemetry artifact is present on the agent host, but it was not loaded.
No different candidate was substituted.

## Access and precondition checks

Required management path was used:

```text
agent-101-vm -> ssh raspi2 -> SSH root@192.168.3.2
```

At 2026-09-05 08:48–08:50 JST:

```text
raspi2 eth0 = 192.168.3.220/24
T6A SSH = success
T6A uptime = 19 minutes at final snapshot
```

Ping from raspi2 returned 0/2, but SSH succeeded, so this was not classified
as management loss.  The T6A reboot record remains:

```text
WDT status: 2
fiq step: 71
exception type: 2
&oops_in_progress: 0xffffffc0111a465c
```

## Current T6A state (read-only snapshot)

```text
loaded modules: usb_net 77824 6
candidate: absent
telemetry: absent
UDC: 11201000.usb
UDC state: not attached
UDC speed: UNKNOWN
mode: 2
GPIO322: 1
xHCI: 11200000.xhci0 present
ncm0: DOWN, a2:c4:0a:04:cf:2b, NO-CARRIER
pstore: console-ramoops-0 present (91084 bytes)
```

The existing ConfigFS snapshot showed the vendor configuration intact:

```text
f1 -> ../../../../usb_gadget/g1/functions/acm.gs2
f2 -> ../../../../usb_gadget/g1/functions/ffs.adb
f3 -> ../../../../usb_gadget/g1/functions/acm.gs0
f4 -> ../../../../usb_gadget/g1/functions/acm.gs1
f5 -> ../../../../usb_gadget/g1/functions/ncm.gs8
```

`ncm0` and `f5` therefore cannot be attributed to the requested candidate.
The snapshot also showed an existing `console-ramoops-0`; it was not changed
or removed.  The current state is retained as found.

## Exact commands used

Read-only repository/artifact checks:

```text
find /home/masataka /tmp -type f -size +500k -size -3M -print0 |
  xargs -0 -n1 sha256sum | grep f07600aa9d8bbec0edc1e05d9ac0ab000d98a353d2a79f89db6242a75d487ce4
find /home/masataka -type f -name usb_f_ncm.ko -exec sha256sum {} \;
find /home/masataka/projects -type f -name '*.ko' -exec sha256sum {} \;
```

Management and T6A checks, through raspi2:

```text
ssh raspi2
ssh -i /home/codex/.ssh/terminal6_ed25519 -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=no root@192.168.3.2
date; uptime; cat /proc/aed/reboot-reason
awk '/usb_net|usb_f_ncm|sbat6_ncm/{print}' /proc/modules
ls -la /config/usb_gadget/g1/configs/b.1
readlink /config/usb_gadget/g1/configs/b.1/f5
cat /config/usb_gadget/g1/UDC
cat /sys/class/udc/11201000.usb/state
cat /sys/class/udc/11201000.usb/current_speed
cat /sys/devices/platform/11201000.usb/mode
cat /sys/class/gpio/gpio322/value
ls /sys/bus/platform/devices | grep -i xhci
ip -br link
ip -s link show ncm0
ls -la /sys/fs/pstore
dmesg | tail -80
```

## Marker timeline

```text
ATTEMPT03_START       NOT_WRITTEN: exact candidate admission failed
M01..M11              NOT_RUN
```

Writing persistent markers was intentionally not started: there was no valid
attempt to mark, and the known safe marker path was not modified.

## Failure classification and diagnosis

```text
last persistent marker: none for ATTEMPT03
exact failure point: preflight / candidate SHA256 admission
WDT/Oops: prior WDT record present; no new WDT/Oops caused by this attempt
new pstore: no new file; existing console-ramoops-0 was observed
f5 absolute link: NOT_TESTED in this attempt (existing vendor link observed)
ncm0 creation: NOT_TESTED in this attempt (existing vendor ncm0 observed)
30-second stability: NOT_RUN
```

The leading operational cause is missing exact test input, not a live kernel
failure.  The previously recorded offline diagnosis remains applicable to the
next design step: the candidate must be rebuilt or recovered with the proven
vendor `usb_function_instance` / ConfigFS ABI and admitted with the stated
static gates before another live test.  The prior ATTEMPT-02 WDT evidence must
not be reclassified as a `gether_register_netdev+0x2c` recurrence from this
blocked attempt.

`sol` was not callable from this workspace.  The diagnosis above is the
existing offline-analysis result recorded in
`t6a-autonomous-debug-resume-20260905.md`; no new sol claim is being made.

## Classification

```text
F5_ABSOLUTE_LINK_LIVE              = NOT_RUN
NCM0_CREATION                      = NOT_RUN
CANDIDATE_PRE_UDC_STABILITY_30S   = NOT_RUN
NET_DEVICE_PRE_UDC_LIVE           = NOT_RUN
UDC_BIND                           = NOT_RUN
WINDOWS_ENUMERATION                = NOT_RUN
NEXT_LIVE_TEST_READY               = no
BLOCKER                            = exact candidate artifact unavailable
```

Recovery was not needed: T6A was found in the existing vendor state and was
left unchanged.  A subsequent attempt requires the exact candidate artifact,
its SHA256 verification, and a fresh pre-state snapshot.  Only then may the
specified marker-backed sequence begin.
