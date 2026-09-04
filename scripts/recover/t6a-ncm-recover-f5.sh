#!/bin/sh
# T6A recovery helper: restore the vendor ncm.gs8 function link and rebind.
# Run as root on T6A. It deliberately does not restart usb.init or touch ADB,
# USB role, VBUS, mode, GPIO, flash, or persistent configuration.
set -eu

G=/config/usb_gadget/g1
C=$G/configs/b.1
U=$G/UDC
TARGET=$G/functions/ncm.gs8

[ -d "$TARGET" ] || { echo "missing $TARGET" >&2; exit 1; }
[ -e "$C/f1" ] && [ -e "$C/f2" ] && [ -e "$C/f3" ] && [ -e "$C/f4" ] || {
  echo 'refusing recovery: expected f1..f4 are incomplete' >&2
  exit 1
}

if [ ! -e "$C/f5" ]; then
  ln -s "$TARGET" "$C/f5"
fi
[ "$(readlink -f "$C/f5")" = "$(readlink -f "$TARGET")" ] || {
  echo 'refusing bind: f5 does not point to ncm.gs8' >&2
  exit 1
}

echo > "$U"
echo 11201000.usb > "$U"

ip addr add test-net.77.1/24 dev ncm0 2>/dev/null || true
ip link set ncm0 up
echo 'recovered f5 and rebound 11201000.usb'
ls -l "$C/f5"
cat "$U"
cat /sys/class/udc/11201000.usb/state
ip -br link show ncm0
ip -br addr show ncm0
