# 65532 v1 custom NCM installation

This procedure is for the published custom module
t6a_usb_ncm_65532_candidate_v1.ko. It is not the vendor procedure in
docs/USB-GADGET-NCM.md. Do not use vendor ncm.gs8, function name ncm, or
the vendor link configs/b.1/f5 for this candidate.

## Preconditions and manual gate

Keep an independent management path through raspi2 and disconnect the USB
host before changing ConfigFS. Confirm the matching T6A Linux 5.4.238 ARM64
kernel, module vermagic 5.4.238 SMP mod_unload modversions aarch64, and the
artifact hash in artifacts/SHA256SUMS. Save a read-only snapshot of the
current module list, ConfigFS tree, UDC state, and ncm0 state. Stop if any
expected path is missing, the vendor gadget is not in its known state, or
management continuity cannot be independently verified.

The operator must explicitly approve the next step after that preflight.
This document intentionally provides no automatic stock-to-custom switching
script.

## Custom identity and topology

The module registers the dedicated USB function-driver name t6a_ncm, not
the vendor ncm. The tested custom topology is:

    /config/usb_gadget/t6a_65532/
      functions/t6a_ncm.65532
      configs/c.1/t6a_ncm.65532 -> ../../../../usb_gadget/t6a_65532/functions/t6a_ncm.65532
      UDC = 11201000.usb

Use the target's reviewed VID/PID, strings, MAC addresses, and network
addresses from the saved baseline; do not copy vendor values blindly. The
custom function must be the only function in c.1. Never link it into vendor
g1/configs/b.1 and never bind a second gadget to the UDC.

## Manual activation and verification

After the manual gate, create or validate the custom gadget and function,
link only the topology above, and bind the UDC with a newline-terminated
write:

    echo 11201000.usb > /config/usb_gadget/t6a_65532/UDC
    cat /config/usb_gadget/t6a_65532/UDC
    cat /sys/class/udc/11201000.usb/state
    cat /sys/class/udc/11201000.usb/current_speed
    ip -brief link show ncm0
    ip -brief addr show ncm0
    cat /sys/class/net/ncm0/carrier

Success requires the custom function, configured UDC, host NCM enumeration,
ncm0 carrier up, and bidirectional IPv4 connectivity. Record every result.
A speed other than the tested SuperSpeed state is not a success claim.

## Failure stop and rollback

On any failed check, stop. Do not retry with force-unload, UDC-driver
manipulation, reboot, or role/GPIO/VBUS changes. Keep management available,
capture read-only state, and unbind only the custom gadget if safe:

    echo > /config/usb_gadget/t6a_65532/UDC

Remove only the custom c.1 link and function instance, restore the saved
vendor topology manually, and rebind the original UDC only after checking
it. The authoritative vendor recovery is docs/RECOVERY.md; its
g1/functions/ncm.gs8 and f5 topology is a rollback target, not the custom
v1 installation topology. If the baseline cannot be reconstructed exactly,
leave the UDC unbound and use the independent management path.

Live validation for this release covers custom module loading, function
identity, UDC bind, Windows enumeration, bidirectional IPv4, and SuperSpeed
on the matching T6A. It does not establish compatibility with another
kernel, UDC, host, or gadget layout.
