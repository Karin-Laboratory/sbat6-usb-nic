#!/bin/sh
# Published MAC addresses are examples; set them to your local configuration before use.
set +e
LOG=/tmp/butlerx-rollback-$(date +%Y%m%d-%H%M%S).log
exec > "$LOG" 2>&1
echo "rollback $(date)"
echo > /config/usb_gadget/g1/UDC 2>/dev/null
for s in /config/usb_gadget/g1/configs/b.1/*; do [ -L "$s" ] && rm -f "$s"; done
for f in /config/usb_gadget/g1/functions/*; do [ -d "$f" ] && rmdir "$f" 2>/dev/null; done
rmmod usb_f_ncm 2>/dev/null
rmmod sbat6_ncm_telemetry 2>/dev/null
modprobe usb_net 2>/dev/null || insmod /lib/modules/5.4.238/usb_net.ko 2>/dev/null
echo 3 > /sys/devices/platform/11201000.usb/mode 2>/dev/null
[ -e /sys/class/gpio/gpio322/value ] && echo 0 > /sys/class/gpio/gpio322/value
mkdir -p /config/usb_gadget/g1/functions/ncm.gs8
echo test-mac:00:00:01 > /config/usb_gadget/g1/functions/ncm.gs8/dev_addr
echo test-mac:00:00:02 > /config/usb_gadget/g1/functions/ncm.gs8/host_addr
echo 30 > /config/usb_gadget/g1/functions/ncm.gs8/qmult
ln -sf ../../../../usb_gadget/g1/functions/ncm.gs8 /config/usb_gadget/g1/configs/b.1/f5
ip addr flush dev ncm0 2>/dev/null
ip addr add test-net.77.1/24 dev ncm0 2>/dev/null
ip link set ncm0 up 2>/dev/null
echo 11201000.usb > /config/usb_gadget/g1/UDC 2>/dev/null
echo '--- final ---'; lsmod | grep usb_net; cat /sys/class/udc/11201000.usb/state 2>/dev/null; cat /sys/class/udc/11201000.usb/current_speed 2>/dev/null; ip -brief addr show br-lan ncm0
