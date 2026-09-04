#!/bin/sh
set -u
LOG=/tmp/butlerx-t6a-attempt02-$(date +%Y%m%d-%H%M%S).log
exec >"$LOG" 2>&1
G=/config/usb_gadget/g1
C=$G/configs/b.1
F=$G/functions/ncm.gs8
U=$G/UDC
echo "ATTEMPT-02 $(date)"
echo "candidate=$(sha256sum /tmp/usb_f_ncm.ko)"
echo "telemetry=$(sha256sum /tmp/sbat6_ncm_telemetry.ko)"
echo '--- pre'
cat /proc/modules | grep -E 'usb_net|usb_f_ncm|sbat6_ncm' || true
ls -l "$C" "$G/functions"
cat "$U"; cat /sys/class/udc/11201000.usb/state; cat /sys/class/udc/11201000.usb/current_speed
echo '--- prepare vendor release'
printf '\n' > "$U"
for x in f1 f2 f3 f4; do rm -f "$C/$x"; done
for x in ncm.gs8 ecm.gs8 rndis.gs4; do rmdir "$G/functions/$x" || exit 20; done
rmmod usb_net || exit 21
insmod /tmp/sbat6_ncm_telemetry.ko || exit 22
insmod /tmp/usb_f_ncm.ko || exit 23
echo '--- candidate instance'
mkdir "$F" || exit 24
for x in dev_addr host_addr qmult ifname; do
  test -e "$F/$x" || { echo "missing attribute $x"; exit 25; }
  test -r "$F/$x" || { echo "unreadable attribute $x"; exit 26; }
done
echo 06:a2:ed:c1:80:59 > "$F/dev_addr"
echo fa:28:57:07:6b:6c > "$F/host_addr"
echo 30 > "$F/qmult"
echo '--- candidate attrs'
for x in dev_addr host_addr qmult ifname; do printf '%s=' "$x"; cat "$F/$x"; done
test ! -e "$C/f5" && test ! -L "$C/f5" || { echo 'unexpected existing f5'; exit 27; }
ln -s "$F" "$C/f5" || exit 28
test "$(readlink -f "$C/f5")" = "$(readlink -f "$F")" || exit 29
echo 3 > /sys/devices/platform/11201000.usb/mode
echo 0 > /sys/class/gpio/gpio322/value
echo 11201000.usb > "$U" || exit 30
sleep 10
echo '--- post bind'
echo UDC=$(cat "$U"); echo state=$(cat /sys/class/udc/11201000.usb/state); echo speed=$(cat /sys/class/udc/11201000.usb/current_speed)
ls -l "$C/f5"; ip -br link show ncm0; ip -br addr show ncm0
for x in carrier operstate address; do test -e "/sys/class/net/ncm0/$x" && echo "$x=$(cat /sys/class/net/ncm0/$x)"; done
echo '--- modules'; cat /proc/modules | grep -E 'usb_net|usb_f_ncm|sbat6_ncm' || true
echo '--- pstore'; find /sys/fs/pstore -maxdepth 1 -type f -print 2>/dev/null
echo '--- dmesg'; dmesg | tail -220
test -e /sys/class/net/ncm0 || exit 31
test "$(cat /sys/class/udc/11201000.usb/state)" = configured || exit 32
echo ATTEMPT02_BIND_PASS
