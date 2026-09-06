# T6A v5 live test — 2026-09-06

```text
TARGET=T6A
V5_SHA256=9c00e3d3517c14868cf0bf991c3a9cc4c5e2b5d5017def3da65fbe800736bd9f
CUSTOM_NCM_MODULE_LOAD=PASS
CUSTOM_NCM_UDC_BIND=PASS
CUSTOM_NETDEV_CREATED=yes
HOST_USB_CONFIGURED=PASS
T6A_IP_CONFIG=PASS
WINDOWS_IP_CONFIG=NOT_VERIFIED
HOST_NET_ADAPTER_CREATED=NOT_VERIFIED
HOST_TO_T6A_PING=NOT_RUN
T6A_TO_HOST_PING=FAIL
CUSTOM_USB_NIC_FIRST_PACKET=FAIL
WINDOWS_DRIVER=NOT_VERIFIED
PSTORE=pre-existing console-ramoops-0 observed before test; post-event recovery unavailable
VENDOR_RESTORED=FAIL_UNCONFIRMED
RUNTIME2=NOT_USED
```

The v5 module loaded with the expected SHA. The custom ConfigFS gadget and
`t6a_ncm.test0` instance were created, vendor `g1` was unbound, and the custom
gadget bound to `11201000.usb`. The UDC reached `configured` at `super-speed`
and `usb0` appeared. After assigning `192.168.77.1/24` and bringing `usb0` up,
the first ping attempt made T6A unreachable over the management path. No blind
retry was performed. The target must be power-cycled before pstore collection
and vendor baseline restoration can be verified.
