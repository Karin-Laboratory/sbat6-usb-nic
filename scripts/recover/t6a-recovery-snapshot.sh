#!/bin/sh
set -u

D=/tmp/butlerx-t6a-recovery-before-20260904-$(date +%H%M%S)
mkdir -p "$D/tree" "$D/attrs"
{
  date -Is
  uname -a
  cat /etc/openwrt_release 2>/dev/null || true
  id
} > "$D/host.txt"
mount > "$D/mounts.txt"
find /config/usb_gadget/g1 -maxdepth 8 -printf '%y %p -> %l\n' 2>/dev/null > "$D/tree/list.txt"
find /config/usb_gadget/g1 -type f | while read -r p; do
  rel=${p#/config/usb_gadget/g1/}
  safe=$(printf '%s' "$rel" | tr '/ ' '__')
  {
    printf 'PATH=%s\n' "$p"
    readlink "$p" 2>/dev/null || true
    cat "$p" 2>&1 || true
    printf '\n'
  } > "$D/attrs/$safe.txt"
done
for p in \
 /config/usb_gadget/g1/UDC \
 /config/usb_gadget/g1/idVendor \
 /config/usb_gadget/g1/idProduct \
 /config/usb_gadget/g1/bcdUSB \
 /config/usb_gadget/g1/bcdDevice \
 /config/usb_gadget/g1/configs/b.1/MaxPower \
 /config/usb_gadget/g1/configs/b.1/bmAttributes \
 /config/usb_gadget/g1/functions/ncm.gs8/* \
 /sys/class/udc/11201000.usb/state \
 /sys/class/udc/11201000.usb/current_speed \
 /sys/class/udc/11201000.usb/max_speed; do
  [ -e "$p" ] || [ -L "$p" ] || continue
  printf '%s=' "$p" >> "$D/key-values.txt"
  cat "$p" 2>&1 >> "$D/key-values.txt" || true
  printf '\n' >> "$D/key-values.txt"
done
cat /proc/modules > "$D/proc-modules.txt"
lsmod > "$D/lsmod.txt" 2>&1 || true
ip -br link > "$D/ip-br-link.txt"
ip -br addr > "$D/ip-br-addr.txt"
ip -details link show > "$D/ip-details-link.txt" 2>&1 || true
ip route show table all > "$D/ip-route.txt" 2>&1 || true
for p in /sys/class/net/*/carrier /sys/class/net/*/operstate /sys/class/net/*/address /sys/class/net/*/mtu; do
  [ -e "$p" ] && printf '%s=' "$p" && cat "$p"
done > "$D/net-sysfs.txt"
dmesg | tail -300 > "$D/dmesg-tail-300.txt"
for p in /etc/init.d/usb.init /etc/rc.d/S30usb.init /etc/config/usb; do
  [ -f "$p" ] && {
    printf '\n===== %s =====\n' "$p"
    sed -n '1,260p' "$p"
  }
done > "$D/vendor-usb-config.txt"
printf '%s\n' "$D"
printf '%s\n' '--- tree list ---'
sed -n '1,240p' "$D/tree/list.txt"
printf '%s\n' '--- key values ---'
cat "$D/key-values.txt"
printf '%s\n' '--- modules ---'
grep -E '^(usb_net|usb_f_ncm|ncm|u_ether|libcomposite|mtu3) ' "$D/proc-modules.txt" || true
printf '%s\n' '--- net ---'
cat "$D/ip-br-link.txt"
cat "$D/ip-br-addr.txt"
