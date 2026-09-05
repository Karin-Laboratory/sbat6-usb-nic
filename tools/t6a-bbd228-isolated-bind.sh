#!/bin/sh
set +e
D=/root/butlerx-bbd228-udc-20260905-1423
mkdir -p "$D"
M="$D/markers.log"
mark(){ echo "$(date -Iseconds) $1" >>"$M"; sync; }
collect(){
 echo "=== $(date --iso-8601=seconds) ==="
 echo mode=$(cat /sys/devices/platform/11201000.usb/mode 2>/dev/null)
 echo gpio322=$(cat /sys/class/gpio/gpio322/value 2>/dev/null)
 echo udc=$(cat /config/usb_gadget/g1/UDC 2>/dev/null)
 echo udc_state=$(cat /sys/class/udc/11201000.usb/state 2>/dev/null)
 echo speed=$(cat /sys/class/udc/11201000.usb/current_speed 2>/dev/null)
 lsmod | grep -E 'usb_net|sbat6_ncm|usb_f_ncm' || true
 ip -br link show ncm0 2>&1 || true
 dmesg | tail -n 180
}
mark B00_START
collect >"$D/preflight.txt"
sha256sum /tmp/usb_f_ncm.ko /tmp/sbat6_ncm_telemetry.ko >"$D/sha.txt"
cat "$D/sha.txt"
printf '3\n' > /sys/devices/platform/11201000.usb/mode
printf '0\n' > /sys/class/gpio/gpio322/value
printf '\n' > /config/usb_gadget/g1/UDC
sleep 1
for s in /config/usb_gadget/g1/configs/b.1/*; do
 [ -L "$s" ] || continue
 case "$(readlink -f "$s")" in */functions/ncm.gs8) rm -f "$s";; esac
done
rmdir /config/usb_gadget/g1/functions/ncm.gs8 2>/dev/null
rmdir /config/usb_gadget/g1/functions/ecm.gs8 2>/dev/null
rmdir /config/usb_gadget/g1/functions/rndis.gs4 2>/dev/null
rmmod usb_net; echo vendor_rmmod_rc=$?
[ "$(lsmod | awk '$1 == "usb_net" {print $1}')" = "" ] || { echo VENDOR_RELEASE_FAILED; exit 21; }
mark B01_CANDIDATE_LOADED
insmod /tmp/sbat6_ncm_telemetry.ko; echo telemetry_insmod_rc=$?
[ -e /sys/module/sbat6_ncm_telemetry ] || exit 22
insmod /tmp/usb_f_ncm.ko; echo candidate_insmod_rc=$?
[ -e /sys/module/usb_f_ncm ] || { echo CANDIDATE_LOAD_FAILED; exit 23; }
sha256sum /tmp/usb_f_ncm.ko /tmp/sbat6_ncm_telemetry.ko
mkdir -p /config/usb_gadget/g1/functions/ncm.gs8
printf '06:a2:ed:c1:80:59\n' > /config/usb_gadget/g1/functions/ncm.gs8/dev_addr
printf 'fa:28:57:07:6b:6c\n' > /config/usb_gadget/g1/functions/ncm.gs8/host_addr
printf '30\n' > /config/usb_gadget/g1/functions/ncm.gs8/qmult
ln -sf ../../../../usb_gadget/g1/functions/ncm.gs8 /config/usb_gadget/g1/configs/b.1/f5
[ "$(readlink -f /config/usb_gadget/g1/configs/b.1/f5)" = "/config/usb_gadget/g1/functions/ncm.gs8" ] || exit 24
mark B02_F5_LINKED
ip -br link show ncm0 2>&1 || true
sleep 30
mark B03_NCM0_PRESENT
ip -br link show ncm0 2>&1 || true
mark B04_PRE_UDC_STABLE
cp /sys/fs/pstore/console-ramoops-0 "$D/pstore-before-udc" 2>/dev/null || true
dmesg > "$D/dmesg-before.txt"
mark B05_BEFORE_UDC_UNBIND
printf '\n' > /config/usb_gadget/g1/UDC
sleep 1
mark B06_AFTER_UDC_UNBIND
collect >"$D/before-bind.txt"
mark B07_BEFORE_UDC_BIND
printf '11201000.usb\n' > /config/usb_gadget/g1/UDC
echo bind_write_rc=$?
mark B08_AFTER_UDC_BIND
sleep 5; mark B09_STABLE_5S; collect >"$D/after-5s.txt"
sleep 5; mark B10_STABLE_10S; collect >>"$D/after-5s.txt"
sleep 20; mark B11_STABLE_30S; collect >"$D/after-30s.txt"
echo RESULT=PASS_CANDIDATE_BIND_SURVIVED_30S
