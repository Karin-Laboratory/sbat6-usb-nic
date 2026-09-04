# Static audit — `sbat6_ncm_telemetry.ko`

Date: 2026-09-04

## Scope and result

Built against the existing T6A Linux 5.4.238 arm64 output. The module has no
USB function registration, UDC/configfs operation, role operation, netdev
operation, kprobe/ftrace hook, worker, timer, or parameter setter. It only
creates a read-only debugfs directory and file and removes them on unload.

Build result: PASS (make returned 0).

Artifact: `sbat6_ncm_telemetry.ko`

SHA-256: `73f715152013d80e407bfef0fe7b31c572ef2a674f88e49de8a9e350b12bf2ac`

## Safety observations

- Data is per-CPU; no new lock is taken in data-path calls.
- No pointers or kernel objects cross the call boundary.
- No allocation or sleeping occurs in telemetry calls.
- Debugfs read aggregates counters and does not reset them.
- Completion timestamps use `ktime_get()` only at completion call sites.
- The module does not itself observe NCM; values remain zero without a source
  integration patch.

## ABI observations

The build uses the T6A tree's generated headers and `Module.symvers`. The
artifact is relocatable aarch64 and contains versioned CRCs for its exported
telemetry API. Before any load, the target must be checked again for matching
kernel release, vermagic, configuration, architecture, and every imported
symbol CRC. No `insmod` has been performed.

## Explicit load gate

This artifact is not approved for T6A loading yet. Approval requires a
separate source integration review, a fresh target symbol/ABI comparison, a
no-cable/no-function smoke test if loading is authorized, and a rollback
procedure. The present request stops before that gate.
