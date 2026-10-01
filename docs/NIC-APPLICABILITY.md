# Can a new agent build another NIC quickly from public information?

Assessment date: 2026-10-01. The recipe is introduced by PR #9.
The earlier main commit 97f55791dd0de4161cb2a9bd06ab9799ff580a8d does not contain it;
use a main revision containing `driver/t6b-ax88179/`.

| Scope | Supported statement |
|---|---|
| AX88179 on the tested T6B firmware/config | Public inputs suffice for a short, scripted build. An isolated rebuild and hardware recognition/DHCP/ICMP were verified. |
| Another Linux 5.4 driver using the same usbnet framework | Shared module/netdev fixes and references are reusable; quick adaptation is plausible, but not demonstrated. |
| Any source-available Linux NIC driver | Not established. Source availability does not ensure 5.4 API compatibility, target exports, firmware dependencies, or matching struct/callback semantics. |
| Another SBAT6 firmware or hardware variant | Not established from the kernel release string alone. Revalidate target identity and applicable ABI anchors. |

The tests used a new build directory but the same agent/build host. They are
not a blind test with a context-free agent or a fresh container. No measured
end-to-end time bound, including downloads/dependency installation, is claimed.

## What an agent can reuse without reverse engineering it again

- Fixed upstream source commit and normalized config.
- net_device patch and documented WEXT dependency.
- module loader settings, especially applying KCFLAGS to generated .mod.c.
- Actual-TU assertions for the listed module/netdev/queue fields.
- 10,205 target Image export CRCs, hash-pinned regeneration, dependency CRC checking.
- Isolated build, final ELF inspection, staged load, log capture and recovery lessons.

## What is still missing for a broad short-build claim

1. A selectable driver/source entry point; current Makefile and source-copy list
   are hard-coded to mii, usbnet and ax88179_178a.
2. A procedure that resolves each new driver's kernel API version, Kconfig,
   exported-symbol dependencies and any required firmware blobs.
3. An inventory of new direct struct accesses, inline helpers and callbacks,
   with evidence for fields outside the existing assertions. The current
   checks do not cover all USB, SKB, ethtool, PHY or networking ABI details.
4. A second structurally different NIC demonstrated through this procedure.
5. A blind public-only test with no inherited chat/private files, recording
   prerequisites, elapsed time and any necessary interventions.

The appropriate present claim is: **the tested AX88179 can be rebuilt from
public inputs without rediscovering the known ABI work; a reusable starting
environment now exists for other NICs.** A promise that any publicly sourced
NIC can quickly become a working SBAT6 module would exceed the evidence.
