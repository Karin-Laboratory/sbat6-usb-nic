#!/bin/sh
set +e
echo > /config/usb_gadget/g1/UDC 2>/dev/null
rm -f /config/usb_gadget/g1/configs/b.1/f5
ln -s /config/usb_gadget/g1/functions/ncm.gs8 /config/usb_gadget/g1/configs/b.1/f5
echo 3 > /sys/devices/platform/11201000.usb/mode 2>/dev/null
echo 0 > /sys/class/gpio/gpio322/value 2>/dev/null
echo 11201000.usb > /config/usb_gadget/g1/UDC 2>/dev/null
sleep 8
echo MODE; cat /sys/devices/platform/11201000.usb/mode 2>/dev/null
echo GPIO; cat /sys/class/gpio/gpio322/value 2>/dev/null
echo XHCI; find /sys/bus/platform/devices -maxdepth 1 -iname '*xhci*' -print
echo LINKS; ls -l /config/usb_gadget/g1/configs/b.1
echo UDC; cat /config/usb_gadget/g1/UDC; cat /sys/class/udc/11201000.usb/state; cat /sys/class/udc/11201000.usb/current_speed
echo NET; ip -brief addr show br-lan; ip -brief addr show ncm0; ip link show dev ncm0 2>/dev/null; cat /sys/class/net/ncm0/carrier 2>/dev/null
echo MOD; lsmod | grep usb_net
