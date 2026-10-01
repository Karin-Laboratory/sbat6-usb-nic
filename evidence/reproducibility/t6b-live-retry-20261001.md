# T6B staged AX88179 load retry — 2026-10-01

After the offline audit, the device owner explicitly authorized another
load experiment on the test device, accepting physical power-cycle recovery.
These are the earlier **Image-CRC-rewritten** candidates, not new ABI-corrected
builds. This test does not change their unsupported structural ABI status.

| Candidate | SHA256 | Observed outcome |
|---|---|---|
| mii.ko | e3a49e17b84308123c2934cc639026aea57f16739a5719789fb5482f2cbd1935 | insmod exit 0, Live; subsequent SSH successful |
| usbnet.ko | c780f87df7e699781bff09f9bdd5c55a8606cc489835564743acf4239e517fbb | insmod exit 0, initcall returned 0; Live before AX load |
| ax88179_178a.ko | 18afe66af34543c27966d4501ec802fb65ecb6b58a25ade8cb4c4b9b473f2372 | Oops during initialization; remains Loading; no new netdev |

Target: SBA6D / Linux 5.4.238 ARM64; USB device 0b95:1790.
Each module was copied separately to /tmp and its on-target hash checked.
No boot persistence was configured. The third insmod did not return before
the 35-second SSH wrapper timeout. Modules were not forcibly unloaded.

## Captured fault

BusyBox dmesg does not support `-w`; a separate SSH connection streaming
`/dev/kmsg` captured the fault before connectivity was lost.
[Selected kernel records](t6b-ax88179-load-fault-20261001.log) show:

- usbnet initcall returned 0 after 6 usecs.
- AX driver initcall starts at uptime 1128.391400 seconds.
- NULL pointer dereference at 1128.391611, ESR 0x96000046, write fault.
- Oops, then `mtk_aee_exception_notifier_call_chain`, followed by another
  paging fault at ffff5994d63ac4af.

No original fault PC or complete call trace was captured. The evidence
narrows the failing stage to AX driver initialization but does not identify
the precise field or function responsible. A USB interface driver symlink
appeared, but this is **not successful probe completion**: the module stayed
Loading and the netdev list had no addition.

A new SSH connection still worked at uptime 1148.15 seconds. A later
diagnostic connection timed out. Power-cycle recovery was requested from
the owner. Recovery is pending in this record; no claim of restored health
or completed recognition is made.

## Implication for the public workflow

CRC rewriting allowed progression past metadata checks but did not produce
a functioning driver. MII/usbnet initialization success does not validate
their code paths invoked later by AX88179. Retain the staged load order and
off-device kernel-log streaming in future experiments, while correcting and
validating the source/header ABI before promoting any build as supported.
