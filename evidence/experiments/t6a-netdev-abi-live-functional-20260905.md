# T6A net_device ABI live functional test — 2026-09-05

## Scope and access

- Target: T6A / `192.168.3.2`
- Management path: agent-101-vm → raspi2 → LAN/SSH → T6A
- ADB: not used
- Windows USB cable: not connected
- Forbidden `sbat6_usb_role_runtime2.ko`: not used
- Pre-state snapshot on T6A: `/tmp/butlerx-t6a-netdev-abi-live-20260905-pre-080604`

## Artifact admission

The candidate was the newly built `usb_f_ncm.ko`, not the older `usb_net.ko` candidate.

```text
candidate SHA256 = f07600aa9d8bbec0edc1e05d9ac0ab000d98a353d2a79f89db6242a75d487ce4
telemetry SHA256 = 94b157ad17cbe678f2484d058b2e5f8231e5ed6de6fe33f8349ee1588ca6ebf5
```

Both files were transferred through raspi2 using temporary names, hashed on T6A,
then renamed.

## Pre-state

- T6A uptime: approximately 7194 seconds
- vendor `usb_net`: loaded, refcount 6
- ConfigFS f1–f4: `acm.gs2`, `ffs.adb`, `acm.gs0`, `acm.gs1`
- f5: absent
- UDC: `11201000.usb`, state `not attached`, current speed `super-speed`
- GPIO322: `1` (HIGH)
- xHCI platform device: absent
- pstore: empty
- Existing logs contained unrelated GPS/MTU/wireless warnings; these predated the test.

## Vendor release and load

Only the permitted unlinked function directories were removed:

```text
ncm.gs8: 6 -> 4
ecm.gs8: 4 -> 2
rndis.gs4: 2 -> 0
rmmod usb_net: RC=0
```

```text
insmod telemetry: RC=0
insmod candidate: RC=0
```

Both loaded modules were marked `[permanent]`. Candidate init returned 0. No
candidate-attributable Oops, BUG, call trace, or warning appeared.

## ConfigFS and bind attempt

The candidate NCM instance was created and all required attributes existed:

```text
dev_addr = 06:a2:ed:c1:80:59
host_addr = fa:28:57:07:6b:6c
qmult = 30
ifname = (unnamed net_device)
```

The established device preparation succeeded:

```text
mode: 2 -> 3
GPIO322: 1 -> 0
xHCI: absent
```

The required relative `ln -sf` operation for `configs/b.1/f5` failed with
`No such file or directory`; f1–f4 remained unchanged and f5 was not present.
The bind write itself returned RC=0, but it was not a valid f5-linked candidate
test. UDC briefly reported `not attached`, then `configured` at `super-speed`.

```text
ncm0: absent throughout the 10-second observation
gether_register_netdev+0x2c Oops: not observed
reboot during bind: not observed
pstore during bind: empty
```

## Stop decision

PHASE A was stopped immediately because f5 was not linked and `ncm0` did not
exist. No same-condition retry was performed. PHASE B (Windows enumeration and
bidirectional ping) and PHASE C (iperf3) were not run.

## Recovery

- UDC unbound successfully.
- Candidate `rmmod` was attempted once and refused (RC=255); no force unload.
- Vendor reload was refused because candidate still owned duplicate `gether_*`
  exports (RC=255).
- A normal reboot was performed to clear the permanent candidate/telemetry.
- After reboot and a 30-second SSH retry: vendor `usb_net` refcount 6,
  f1–f4 unchanged, UDC `not attached`, current speed `super-speed`,
  GPIO322=1, pstore empty.
- No candidate or telemetry module remained loaded.

## Classification

```text
NET_DEVICE_ABI_LIVE = FAIL (valid live functional condition not reached)
UDC_BIND             = FAIL (f5 link failed; no ncm0)
WINDOWS_ENUMERATION  = NOT_RUN
BIDIRECTIONAL_PING   = NOT_RUN
USB_NCM_FUNCTIONAL   = NOT_RUN
IPERF_BASELINE       = NOT_RUN
```

The previous `gether_register_netdev+0x2c` NULL dereference did not recur during
the attempted candidate load/bind sequence. This is evidence against that Oops
reappearing, but not a PASS for the requested functional test because the f5
link and `ncm0` prerequisites were absent.

## Evidence

- T6A snapshot: `/tmp/butlerx-t6a-netdev-abi-live-20260905-pre-080604`
- Candidate build: `/home/masataka/projects/sbair6-rce/work/isolated/t6a-netdev-provenance-20260905/module/usb_f_ncm.ko`
- GitHub candidate/static-gate commit supplied by owner: `d0b0ce3`
- ButlerX repository had no configured Git remote at test completion; no push was possible.
