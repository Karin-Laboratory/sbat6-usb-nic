#!/bin/sh
set -u
E=/root/butlerx-live-evidence-20260905-netdev-final
S=/tmp
G=/config/usb_gadget/g1
C=$G/configs/b.1
F=$G/functions/ncm.gs8
U=$G/UDC
mkdir -p "$E" "$S"
log() { echo "[$(date -Is)] $*" | tee -a "$E/live.log"; }
mark() { echo "$(date -Is) $1" | tee -a "$E/markers.log"; }
snap() { dmesg | tail -160 > "$E/dmesg-$1" 2>&1 || true; cat /proc/modules > "$E/modules-$1" 2>&1 || true; uptime > "$E/uptime-$1" 2>&1 || true; }
mark A00_START
sha256sum "$S/sbat6_ncm_telemetry.ko" | tee "$E/telemetry-sha256"
sha256sum "$S/usb_f_ncm.ko" | tee "$E/candidate-sha256"
cat "$U" > "$E/udc-before" 2>&1 || true
cat /sys/class/udc/11201000.usb/state > "$E/udc-state-before" 2>&1 || true
grep -E '^(usb_net|usb_f_ncm|sbat6_ncm_telemetry) ' /proc/modules > "$E/modules-before" || true
for f in ncm.gs8 ecm.gs8 rndis.gs4; do
  p="$G/functions/$f"
  if [ -d "$p" ]; then rmdir "$p"; log "RELEASE_${f}_RC=$?"; else log "RELEASE_${f}=ABSENT"; fi
done
rmmod usb_net; log RMMOD_USB_NET_RC=$?
snap vendor-released
mark A01_VENDOR_RELEASED
insmod "$S/sbat6_ncm_telemetry.ko"; log TELEMETRY_INSMOD_RC=$?
snap telemetry
mark A02_TELEMETRY_LOADED
insmod "$S/usb_f_ncm.ko"; log CANDIDATE_INSMOD_RC=$?
snap candidate
mark A03_CANDIDATE_LOADED
mkdir "$F"; log INSTANCE_MKDIR_RC=$?
mark A04_INSTANCE_READY
echo 06:a2:ed:c1:80:59 > "$F/dev_addr"; a=$?
echo fa:28:57:07:6b:6c > "$F/host_addr"; b=$?
echo 30 > "$F/qmult"; c=$?
log ATTR_WRITE_RC=$a,$b,$c
for x in dev_addr host_addr qmult ifname; do printf '%s=' "$x"; cat "$F/$x" 2>&1 || true; done | tee "$E/attrs"
echo 3 > /sys/devices/platform/11201000.usb/mode; a=$?
echo 0 > /sys/class/gpio/gpio322/value; b=$?
log MODE_GPIO_RC=$a,$b
mark A05_F5_LINKED_PREP
ln -s "$F" "$C/f5"; log F5_LINK_RC=$?
readlink -f "$C/f5" | tee "$E/f5-resolved"
ip link > "$E/ip-after-f5" 2>&1 || true
ip link show ncm0 > "$E/ncm0-after-f5" 2>&1 || true
mark A06_PRE_UDC_STABLE
for i in 1 2 3 4 5 6; do date -Is; uptime; ip link show ncm0 2>&1 || true; sleep 5; done > "$E/pre-udc-30s"
mark A07_BEFORE_UDC_BIND
echo 11201000.usb > "$U"; log UDC_BIND_WRITE_RC=$?
mark A08_AFTER_UDC_BIND
sleep 5
for i in 1 2 3 4 5 6; do date -Is; uptime; cat "$U"; cat /sys/class/udc/11201000.usb/state; cat /sys/class/udc/11201000.usb/current_speed; ip link show ncm0 2>&1 || true; sleep 5; done > "$E/post-udc-30s"
mark A09_STABLE_5S
mark A10_STABLE_10S
mark A11_STABLE_30S
snap final
echo LIVE_SCRIPT_COMPLETE | tee -a "$E/live.log"
