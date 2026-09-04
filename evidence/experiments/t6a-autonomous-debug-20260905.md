# T6A NCM autonomous debug — 2026-09-05

## ATTEMPT-01 — exact f5 diagnosis and vendor baseline

- Start: 2026-09-05 08:17 JST
- Candidate: `f07600aa9d8bbec0edc1e05d9ac0ab000d98a353d2a79f89db6242a75d487ce4`
- Management path: `agent-101-vm -> raspi2 -> SSH -> root@192.168.3.2`
- ADB: not used; forbidden `sbat6_usb_role_runtime2.ko`: not used
- Hypothesis: the reported `f5` failure may be a relative-link spelling/stale ConfigFS problem

### Exact previous failure

The command is recorded in `tools/t6a-phase2.sh` line 21:

```sh
ln -sf ../../../../usb_gadget/g1/functions/ncm.gs8 /config/usb_gadget/g1/configs/b.1/f5
```

Observed result in `t6a-netdev-abi-live-functional-20260905.md`:

```text
RC != 0
stderr: No such file or directory
f1..f4 unchanged
f5 absent
```

The same failure is independently recorded as `ENOENT` in
`t6a-usb-net-instance-owner-audit-20260904-2227.md`. The subsequent UDC write
returned `RC=0`, but was not a valid candidate test because `f5` was absent and
`ncm0` never existed.

### Current live observation before any new candidate operation

- T6A reachable over SSH; management LAN healthy
- vendor `usb_net` loaded, refcount `6`
- no `usb_f_ncm`, no telemetry module, no pstore files
- ConfigFS vendor tree has `f1..f4` links to `acm.gs2`, `ffs.adb`, `acm.gs0`, `acm.gs1`
- vendor `functions/ncm.gs8`, `ecm.gs8`, and `rndis.gs4` exist
- UDC `11201000.usb`, state `configured`, current speed `super-speed`
- no `ncm0`
- candidate was not loaded in this attempt

### Classification

The relative string is not the leading root cause. The same relative target is
the normal ConfigFS representation of vendor links, and vendor recovery records
show that the equivalent absolute target succeeds. The candidate-specific
failure occurs earlier: after `mkdir functions/ncm.gs8`, the candidate instance
had no regular ConfigFS attributes and no netdev. Therefore the target was not a
valid registered function instance, and `ln` reported `ENOENT` as a downstream
effect. This is a candidate ConfigFS/function-instance ABI or registration
failure, not yet a path-only failure.

### Offline evidence

The candidate source in
`/home/masataka/projects/sbair6-rce/work/isolated/t6a-netdev-provenance-20260905/module/`
uses a private `usb_function_instance` representation with an extra `struct
usb_function *f` and custom conversions. Netdev/header provenance and CRC gates
passed, but those gates do not prove ConfigFS registration behavior. The
candidate must not be live-retried until this registration boundary is explained
or corrected.

### Decision

No same-condition retry. T6A was left in vendor state. Candidate replacement,
forced unload, unknown role/GPIO operations, Windows connection, and iperf were
not performed.

## ATTEMPT-02 — absolute-link live retry

- Start: 2026-09-05 08:29 JST
- Candidate and telemetry hashes were verified on T6A before use:
  `f07600aa9d8bbec0edc1e05d9ac0ab000d98a353d2a79f89db6242a75d487ce4` and
  `94b157ad17cbe678f2484d058b2e5f8231e5ed6de6fe33f8349ee1588ca6ebf5`.
- Change from ATTEMPT-01: absolute function target, `ln -s` (not `ln -sf`),
  explicit absence/readability gate for `dev_addr`, `host_addr`, `qmult`, and
  `ifname` before link creation.
- The remote command began vendor provider release, loaded telemetry and the
  candidate, then lost the T6A management path before a result log could be
  collected. The initiating SSH command returned without usable stdout; a
  30-second retry and subsequent retries found ARP/SSH unreachable or no route.
- No evidence is available that Windows enumeration, UDC bind success, `ncm0`,
  or a kernel Oops occurred. They are all `NOT_VERIFIED`.
- Because the target became unreachable during candidate ConfigFS operations,
  same-condition retry is prohibited. Recovery cannot be completed over the
  approved SSH path at this time; ADB and unknown out-of-band operations were
  not attempted.

### Current blocker

```text
T6A management path lost during ATTEMPT-02 candidate ConfigFS sequence
USB_NCM_VISIBLE_FROM_WINDOWS = NOT_REACHED
T6A final module/config state = UNVERIFIED
pstore = UNRECOVERABLE_WHILE_OFFLINE
```

The next safe action, once T6A management returns or the owner performs the
minimum approved recovery action, is pstore-first collection followed by vendor
baseline verification. Do not repeat the candidate until that evidence is
collected.
