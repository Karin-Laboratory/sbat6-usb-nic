# SBAT6 external-module applicability

The current evidence supports a reusable **starting compatibility environment**
for SBA6D/SBAT6 Linux 5.4.238 ARM64 external modules. It is not a claim that an
arbitrary kernel subsystem or hardware variant will work automatically.

## Proven across

- networking and `net_device`
- USB networking and `usbnet`
- Realtek vendor `r8152` (RTL8156 regression; RTL8157 source target pending)
- in-tree `aqc111` (AQC111U/AQC112U targets pending hardware)
- media/V4L2 and videobuf2
- UVC probe, stream, JPEG decode, and visual validation

The same canonical config, vendor export-CRC inputs, module-layout assertions,
global KCFLAGS, final-ELF audit, and staged load method were reused. UVC is the
evidence that this compatibility environment is not limited to the network
subsystem.

## Not proven

- arbitrary kernel subsystems
- arbitrary firmware revisions or SBAT6 hardware variants
- drivers requiring unknown private vendor APIs
- RTL8157 5GbE hardware/link/traffic
- AQC111U/AQC112U hardware probe/link/traffic
- long-duration or repeated hotplug/reload endurance

Every new family still requires source provenance, dependency and firmware audit,
direct structure-access audit, exact final-ELF checks, and hardware validation.

