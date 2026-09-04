#!/bin/sh
set +e
LOG=/tmp/butlerx-t6a-final-restore-$(date +%Y%m%d-%H%M%S).log
exec > "$LOG" 2>&1
echo "start $(date)"
echo "mgmt-before"; ip -brief addr show br-lan; ip route
echo "xhci"; ls /sys/bus/platform/devices 2>/dev/null | grep -i xhci || true
echo "mode-before=$(cat /sys/devices/platform/11201000.usb/mode 2>/dev/null) gpio322-before=$(cat /sys/class/gpio/gpio322/value 2>/dev/null)"
echo > /config/usb_gadget/g1/UDC 2>/dev/null
rm -f /config/usb_gadget/g1/configs/b.1/f5
mkdir -p /config/usb_gadget/g1/functions/ncm.gs8
echo test-mac:00:00:01 > /config/usb_gadget/g1/functions/ncm.gs8/dev_addr
echo test-mac:00:00:02 > /config/usb_gadget/g1/functions/ncm.gs8/host_addr
echo 30 > /config/usb_gadget/g1/functions/ncm.gs8/qmult
ln -sf ../../../../usb_gadget/g1/functions/ncm.gs8 /config/usb_gadget/g1/configs/b.1/f5
echo 3 > /sys/devices/platform/11201000.usb/mode
echo 0 > /sys/class/gpio/gpio322/value
echo 11201000.usb > /config/usb_gadget/g1/UDC
sleep 8
echo "mode=$(cat /sys/devices/platform/11201000.usb/mode 2>/dev/null) gpio322=$(cat /sys/class/gpio/gpio322/value 2>/dev/null)"
echo "udc=$(cat /config/usb_gadget/g1/UDC 2>/dev/null) state=$(cat /sys/class/udc/11201000.usb/state 2>/dev/null) speed=$(cat /sys/class/udc/11201000.usb/current_speed 2>/dev/null)"
ls -l /config/usb_gadget/g1/configs/b.1; ls -l /config/usb_gadget/g1/functions
ip -brief addr show br-lan ncm0; ip link show ncm0 2>/dev/null; cat /sys/class/net/ncm0/carrier 2>/dev/null
lsmod | grep usb_net
echo "dmesg usb"; dmesg | grep -i -E 'usb|xhci|oops|BUG|call trace|warning' | tail -n 80
echo "LOG=$LOG"
