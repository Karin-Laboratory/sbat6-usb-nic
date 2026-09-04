#!/bin/sh
ip link set dev ncm0 up 2>/dev/null
ip addr add test-net.77.1/24 dev ncm0 2>/dev/null
sleep 3
ip -brief addr show ncm0
cat /sys/class/net/ncm0/carrier 2>/dev/null
ping -c 3 -W 1 test-net.77.2
