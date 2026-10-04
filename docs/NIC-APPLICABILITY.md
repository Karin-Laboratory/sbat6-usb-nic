# Can a new agent build another NIC quickly from public information?

## AQC111U / AQC112U and RTL8157 update

`aqc111` is an independent in-tree USB NIC driver family that reuses `usbnet`
and `mii`. Its dependency load and live `insmod` sequence passed on SBA6D, but
neither AQC hardware target was available for probe, link, or traffic testing.
AQC111U (5GbE class) and AQC112U (2.5GbE class) are represented by one shared
published binary, not two copies.

RTL8157 is an additional chip target in the existing Realtek `r8152` family.
The source has RTL8157 support and its exact module passed SBA6D load plus
RTL8156 regression, while RTL8157 hardware/link/traffic remains pending.

Assessment date: 2026-10-04. The recipe is introduced by PR #9.
The earlier main commit 97f55791dd0de4161cb2a9bd06ab9799ff580a8d does not contain it;
use a main revision containing `driver/t6b-ax88179/`.

| Scope | Supported statement |
|---|---|
| AX88179 on the tested T6B firmware/config | Public inputs suffice for a short, scripted build. An isolated rebuild and hardware recognition/DHCP/ICMP were verified. |
| RTL8156 / r8152 on the tested T6B firmware/config | The AX88179 compatibility environment was reused for a structurally different driver. Module load, bind, MAC retrieval, netdev creation, interface UP, 2500 Mb/s Full Duplex link, 60-second ping at 0% loss, and short iperf3 throughput (P1 2.27 Gbit/s, P4 2.15 Gbit/s, retransmissions 0) all passed without r8152-related Oops/panic. |
| Another Linux 5.4 driver | Reuse is now demonstrated beyond usbnet, but every new driver still needs its own API/dependency/firmware/direct-structure-access audit and final-ELF verification. |
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
4. A blind public-only test with no inherited chat/private files, recording
   prerequisites, elapsed time and any necessary interventions.

The appropriate present claim is: **the tested compatibility environment has now brought up both AX88179 and RTL8156/r8152 on the tested T6B firmware/config, including a structurally different driver that directly touches more networking internals.** This is strong evidence for a reusable SBA6D external-driver starting environment, but it is still not a promise that any publicly sourced NIC can quickly become a working SBAT6 module. The RTL8156 physical-link datapath and short throughput are now verified; long-duration stability, reverse-direction throughput and repeated hotplug/reload endurance remain to be characterized.
