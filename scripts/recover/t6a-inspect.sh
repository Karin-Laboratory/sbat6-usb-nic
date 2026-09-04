#!/bin/sh
set +e
echo '=== time/identity ==='; date; uname -a; id
echo '=== mgmt ==='; ip -brief addr; ip route; ip link show br-lan
echo '=== mode/gpio ==='; for f in /sys/class/gpio/gpio321/value /sys/class/gpio/gpio322/value /sys/class/gpio/gpio323/value /sys/devices/platform/soc/soc:gpio@*/gpio/gpio321/value /sys/devices/platform/soc/soc:gpio@*/gpio/gpio322/value /sys/devices/platform/soc/soc:gpio@*/gpio/gpio323/value; do [ -e "$f" ] && echo "$f=$(cat "$f")"; done; for f in /sys/module/*/parameters/mode /sys/module/*/parameters/role; do [ -e "$f" ] && echo "$f=$(cat "$f")"; done
echo '=== usb gadget tree ==='; find /config/usb_gadget/g1 -maxdepth 4 -printf '%y %p -> %l\n' 2>/dev/null
echo '=== gadget attrs ==='; for f in /config/usb_gadget/g1/idVendor /config/usb_gadget/g1/idProduct /config/usb_gadget/g1/bcdUSB /config/usb_gadget/g1/bcdDevice /config/usb_gadget/g1/UDC /config/usb_gadget/g1/functions/ncm.gs8/*; do [ -e "$f" ] && { printf '%s=' "$f"; cat "$f" 2>/dev/null; }; done
echo '=== ncm/network ==='; ip -details link show ncm0 2>/dev/null; ip addr show ncm0 2>/dev/null; for f in /sys/class/net/ncm0/address /sys/class/net/ncm0/operstate /sys/class/net/ncm0/carrier /sys/class/net/ncm0/statistics/*; do [ -e "$f" ] && echo "$f=$(cat "$f")"; done
echo '=== modules ==='; lsmod; echo '--- usb_net ---'; lsmod | grep usb_net
echo '=== params ==='; find /sys/module/usb_net/parameters /sys/module/mtu3/parameters -maxdepth 1 -type f -print -exec sh -c 'printf "="; cat "$1"' sh {} \; 2>/dev/null
echo '=== udc ==='; for f in /sys/class/udc/*/{state,current_speed,maximum_speed}; do [ -e "$f" ] && echo "$f=$(cat "$f")"; done
echo '=== modules/files ==='; ls -l /tmp/*.ko /root/*.ko /lib/modules/$(uname -r)/**/*.ko 2>/dev/null; sha256sum /tmp/*.ko /root/*.ko 2>/dev/null
echo '=== dmesg tail ==='; dmesg | tail -120
