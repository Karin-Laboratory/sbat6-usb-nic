# T6B AX88179 compatibility rebuild — 2026-10-01

Follow-up: [Ethernet cable testing](ethernet-test.md) confirmed 1 Gbps,
the reserved DHCP lease, and target-initiated ICMP. The initial-stage record
below retains its original test boundary.

**Result: fresh source rebuild, normal module removal/reload, and USB NIC
recognition succeeded. Ethernet traffic is not yet tested.**

The retained T6B configuration and later NCM ABI records were used to fix
the header/config mismatch in the earlier CRC-rewritten candidates.
This experiment recovered after the owner power-cycled the target; initial
SSH uptime was 471.59 seconds. The new modules were compiled from source,
not made by rewriting final ELF version fields.

## Reproduction chain

1. Initial isolated compatibility build: all specified actual-TU assertions
   passed, including module size/init/exit and netdev/queue anchors.
2. Final-ELF check caught an important build-system issue: ccflags-y did not
   reach generated `.mod.c`. Applying the flags/assertions through KCFLAGS
   corrected the actual cleanup relocation from 0x258 to 0x328.
3. Metadata checks passed: 6 + 92 + 48 version records, including dependencies.
4. Modules loaded successfully. USB NIC initially absent after power cycle;
   owner reinserted the USB connection. At uptime 878.659296, AX88179
   registered eth2. This was a physical enumeration issue, not failed probe.
5. A second build used only the bundled config/patch/map/assertions/recipe
   and a Git archive of upstream commit 6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6.
   No prior generated output or private header was supplied to this build.
6. Selected executable/data sections matched the first build; see
   `section-comparison.json`. This is section equality, not a claim of
   full ELF reproducibility across output paths or toolchain versions.
7. Normal rmmod of AX, usbnet, mii succeeded (uptime 1032.28).
8. The second build's exact files were transferred with hash verification,
   loaded one at a time, and AX88179 registered eth2 again at 1055.309987.
   `SHA256SUMS` identifies the second build, currently loaded at test end.
9. Final SSH health check at 1176.03 seconds still showed all three modules
   Live, eth2 present and USB speed 5000. No pstore files were listed.

The streamed log had no `Oops`, `Unable to handle`, `BUG:`, `WARNING: CPU`
or `Call trace:` match during the captured interval. Ordinary preexisting
vendor GPS/Wi-Fi warnings are not classified as new module faults. No
claim of long-term stability or Ethernet datapath correctness is made.

## Files and boundaries

- `*-metadata.json`: exact second-build module and reference hashes, imports.
- `kernel-excerpt.log`: relevant driver init/register/unregister records;
  the device MAC is redacted.
- `public-*-load.txt`: load return codes and module state.
- `public-recognized.txt`: speed, interface, driver, administrative state.
- `unload.txt`: normal removal of the first corrected build.
- `final-health.txt`: final management/USB/module observation.

The netdev was left administratively down, with Ethernet cable/traffic testing
pending. No route changes, firmware writes or persistence were added.
Module load/recognition is the achieved milestone, not universal driver safety.

Follow [the public build recipe](../../../driver/t6b-ax88179/README.md).
