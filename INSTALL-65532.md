# 65532 v1 custom NCM installation

This is the installation procedure for the published custom module
`t6a_usb_ncm_65532_candidate_v1.ko`. It is separate from the vendor procedure
in `docs/USB-GADGET-NCM.md`. Do not substitute the vendor `ncm.gs8`, `ncm`,
`g1`, `b.1`, or `f5` names in this procedure.

The names below are the only custom topology names covered by the recorded
T6A live validation:

```text
gadget   = t6a_ncm_test
function = t6a_ncm.test0
config   = c.1
UDC      = 11201000.usb
network  = usb0
```

## Read-only preflight and manual gate

Use the independent `raspi2` management path and disconnect the USB host
before changing ConfigFS. Do not begin activation if any check fails. Save
the output as the rollback snapshot; do not publish device-specific values.

```sh
G=/config/usb_gadget
UDC=11201000.usb
test -d "$G" && test -d "/sys/class/udc/$UDC" || exit 2
uname -a
cat /sys/class/udc/$UDC/state
cat /sys/class/udc/$UDC/current_speed
cat /sys/class/udc/$UDC/uevent
cat /proc/modules
find "$G" -maxdepth 4 -type l -o -type f | sort
ip -brief link show usb0
ip -brief addr show usb0
cat /sys/class/net/usb0/carrier 2>/dev/null || true
sha256sum /path/to/t6a_usb_ncm_65532_candidate_v1.ko
V=/config/usb_gadget/g1
test ! -e "$V/UDC" || test -z "$(cat "$V/UDC")" || exit 2
test ! -e /config/usb_gadget/t6a_ncm_test || exit 2
```

The hash must match `artifacts/SHA256SUMS`, and the target must be the
matching T6A Linux 5.4.238 ARM64 kernel with vermagic
`5.4.238 SMP mod_unload modversions aarch64`. Save the current module list,
the complete ConfigFS tree, UDC state, and `usb0` state. Confirm that the
existing vendor gadget is safely unbound and that management continuity is
independent of the USB data path. Stop if the vendor gadget is still bound,
if the UDC is not in the expected baseline state, or if any required path is
missing.

The operator must explicitly approve the activation after this read-only
preflight. There is intentionally no stock-to-custom automation script.

VID/PID, both NCM MAC addresses, and any existing strings are not included
here. Restore only values that exist in the saved, reviewed baseline
snapshot. The recorded snapshot had no root/config strings; do not create
`strings/0x409` or string files merely because this document contains
placeholders. If a reviewed snapshot contains those directories, restore
their saved values conditionally. Do not invent, copy blindly, or publish
device-specific values.

## Manual activation

Run these commands only after the gate above. The `mkdir` and `ln` operations
must be performed against an unbound custom gadget; they must not modify the
vendor gadget.

```sh
G=/config/usb_gadget/t6a_ncm_test
UDC=11201000.usb
MOD=/path/to/t6a_usb_ncm_65532_candidate_v1.ko

# Load the published custom module, then verify that init really succeeded.
insmod "$MOD"
test -d /sys/module/t6a_usb_ncm_65532_candidate_v1 || exit 2
awk '$1 == "t6a_usb_ncm_65532_candidate_v1" { found=1 } END { exit(found ? 0 : 1) }' /proc/modules || exit 2
test -d /config/usb_gadget || exit 2

# Create the dedicated gadget and its only configuration. The recorded
# snapshot has no root/config strings, so create those directories only when
# the reviewed local snapshot proves that they already existed.
mkdir -p "$G" "$G/configs/c.1"
mkdir "$G/functions/t6a_ncm.test0"

# Restore reviewed local snapshot values; these placeholders are deliberate.
: "${VID_HEX:?restore VID_HEX from the reviewed local snapshot}"
: "${PID_HEX:?restore PID_HEX from the reviewed local snapshot}"
: "${DEV_MAC:?restore DEV_MAC from the reviewed local snapshot}"
: "${HOST_MAC:?restore HOST_MAC from the reviewed local snapshot}"
: "${USB0_ADDR:?restore USB0_ADDR from the reviewed local snapshot}"
: "${PEER_IPV4:?restore PEER_IPV4 from the reviewed local snapshot}"
printf '%s\n' "$VID_HEX" > "$G/idVendor"
printf '%s\n' "$PID_HEX" > "$G/idProduct"
printf '%s\n' "$DEV_MAC" > "$G/functions/t6a_ncm.test0/dev_addr"
printf '%s\n' "$HOST_MAC" > "$G/functions/t6a_ncm.test0/host_addr"

# Only if the saved snapshot contains these exact string files, restore them
# from local values. With the recorded snapshot this block is skipped.
if [ "${SNAPSHOT_HAS_STRINGS:-0}" = 1 ]; then
    : "${SERIAL:?restore SERIAL from the reviewed local snapshot}"
    : "${MANUFACTURER:?restore MANUFACTURER from the reviewed local snapshot}"
    : "${PRODUCT:?restore PRODUCT from the reviewed local snapshot}"
    : "${CONFIGURATION:?restore CONFIGURATION from the reviewed local snapshot}"
    mkdir -p "$G/strings/0x409" "$G/configs/c.1/strings/0x409"
    printf '%s\n' "$SERIAL" > "$G/strings/0x409/serialnumber"
    printf '%s\n' "$MANUFACTURER" > "$G/strings/0x409/manufacturer"
    printf '%s\n' "$PRODUCT" > "$G/strings/0x409/product"
    printf '%s\n' "$CONFIGURATION" > "$G/configs/c.1/strings/0x409/configuration"
fi

# The relative link is from configs/c.1 to this gadget's functions directory.
ln -s ../../functions/t6a_ncm.test0 "$G/configs/c.1/t6a_ncm.test0"
test "$(readlink "$G/configs/c.1/t6a_ncm.test0")" = ../../functions/t6a_ncm.test0 || exit 2

# Bind only the dedicated gadget, with a newline-terminated write.
printf '%s\n' "$UDC" > "$G/UDC"
test "$(cat "$G/UDC")" = "$UDC" || exit 2
cat "/sys/class/udc/$UDC/state"
cat "/sys/class/udc/$UDC/current_speed"

# Configure the already-enumerated custom interface from the reviewed local
# snapshot. Do not reuse vendor addresses.
ip link set usb0 up
ip addr add "$USB0_ADDR" dev usb0
ip -brief link show usb0
ip -brief addr show usb0
cat /sys/class/net/usb0/carrier
```

The custom function must be the only link in `c.1`. Success requires the
module to appear in `/sys/module`, the function and link to resolve exactly as
above, the UDC to be bound, host NCM enumeration, `usb0` carrier up, and
bidirectional IPv4 connectivity using the reviewed peer address from the
snapshot. Record both directions explicitly, for example:

```sh
ping -I usb0 -c 3 "$PEER_IPV4"
# From the USB host, ping the reviewed T6A USB address as well.
```

The recorded successful validation used SuperSpeed. A different
`current_speed`, missing carrier, one-way ping, or failed host enumeration is
not a success claim. Stop and preserve the evidence.

## Failure stop and rollback

On any failed check, stop. Do not retry with `rmmod -f`, UDC-driver
manipulation, reboot, role/GPIO/VBUS changes, or an automatic fallback. Keep
the independent management path available and capture read-only state first.

If it is safe to remove only the custom gadget, use the following bounded
cleanup. Do not run it while the custom UDC field is non-empty or while an
unexpected link is present:

```sh
G=/config/usb_gadget/t6a_ncm_test
test "$(cat "$G/UDC")" = 11201000.usb && printf '\n' > "$G/UDC"
test -z "$(cat "$G/UDC")" || exit 2
rm -f "$G/configs/c.1/t6a_ncm.test0"
rmdir "$G/functions/t6a_ncm.test0"
```

The rollback target is the saved vendor configuration, not this custom
topology: `g1/functions/ncm.gs8` linked at `g1/configs/b.1/f5`, with the
saved vendor VID/PID, strings, MACs, and network values. Restore those values
manually from the snapshot and bind `11201000.usb` only after verifying the
target path and link. The authoritative vendor procedure is
`docs/RECOVERY.md`. If the original baseline cannot be reconstructed exactly,
leave the UDC unbound and retain the independent management path.

This release's live validation covers custom module loading, function-driver
identity, UDC bind, Windows enumeration, bidirectional IPv4, and SuperSpeed
on the matching T6A. It does not establish compatibility with another
kernel, UDC, host, or gadget layout.
