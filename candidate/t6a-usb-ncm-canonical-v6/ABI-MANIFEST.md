# ABI manifest: custom NCM v6

```text
net_device._tx=0x3c0
net_device.num_tx_queues=0x3c8
net_device.real_num_tx_queues=0x3cc
netdev_queue.stride=0x140
netdev_queue.state=0x90
netdev_queue.trans_start=0x88
net_device.netdev_ops=0x1f8
net_device.ethtool_ops=0x200
net_device.mtu=0x228
net_device.min_mtu=0x22c
net_device.max_mtu=0x230
net_device.dev_addr=0x318
net_device.dev=0x510
net_device.private_base=0x8c0
usb_function_instance.name=0xa0
usb_function_instance.set_inst_name=0xa8
usb_function_instance.free_func_inst=0xb0
```

These are the audited compatibility offsets for this candidate, not a claim
of complete symbolic reconstruction of vendor kernel headers.
