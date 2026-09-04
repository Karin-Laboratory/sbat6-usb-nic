#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/stddef.h>

#define V(name, value) char name[(value) + 1]
V(sz_net_device, sizeof(struct net_device));
V(off_dev_addr, offsetof(struct net_device, dev_addr));
V(off_netdev_ops, offsetof(struct net_device, netdev_ops));
V(off_ethtool_ops, offsetof(struct net_device, ethtool_ops));
V(off_dev, offsetof(struct net_device, dev));
V(off_addr_assign_type, offsetof(struct net_device, addr_assign_type));
V(off_mtu, offsetof(struct net_device, mtu));
V(off_flags, offsetof(struct net_device, flags));
V(off_features, offsetof(struct net_device, features));
V(off_netdev_priv, ALIGN(sizeof(struct net_device), NETDEV_ALIGN));
V(netdev_align, NETDEV_ALIGN);

static int __init probe_init(void) { return -ENODEV; }
module_init(probe_init);
MODULE_LICENSE("GPL");
