/* T6A_OPAQUE_ABI_V1: audited runtime offsets; no native net_device fields. */
#ifndef T6A_OPAQUE_ABI_H
#define T6A_OPAQUE_ABI_H

#include <linux/device.h>
#include <linux/netdevice.h>

#define T6A_NETDEV_NETDEV_OPS 0x1f8
#define T6A_NETDEV_ETHTOOL_OPS 0x200
#define T6A_NETDEV_MIN_MTU 0x22c
#define T6A_NETDEV_MAX_MTU 0x230
#define T6A_NETDEV_ADDR_ASSIGN_TYPE 0x25e
#define T6A_NETDEV_DEV_ADDR 0x318
#define T6A_NETDEV_EMBEDDED_DEV 0x510
#define T6A_NETDEV_PRIV 0x8c0

static inline char *t6a_netdev_name(struct net_device *net)
{ return (char *)net; }
static inline const struct net_device_ops **t6a_netdev_ops_ptr(struct net_device *net)
{ return (const struct net_device_ops **)((char *)net + T6A_NETDEV_NETDEV_OPS); }
static inline const struct ethtool_ops **t6a_ethtool_ops_ptr(struct net_device *net)
{ return (const struct ethtool_ops **)((char *)net + T6A_NETDEV_ETHTOOL_OPS); }
static inline unsigned int *t6a_min_mtu_ptr(struct net_device *net)
{ return (unsigned int *)((char *)net + T6A_NETDEV_MIN_MTU); }
static inline unsigned int *t6a_max_mtu_ptr(struct net_device *net)
{ return (unsigned int *)((char *)net + T6A_NETDEV_MAX_MTU); }
static inline unsigned char *t6a_addr_assign_type_ptr(struct net_device *net)
{ return (unsigned char *)net + T6A_NETDEV_ADDR_ASSIGN_TYPE; }
static inline unsigned char *t6a_dev_addr_ptr(struct net_device *net)
{ return (unsigned char *)net + T6A_NETDEV_DEV_ADDR; }
static inline struct device *t6a_embedded_device_ptr(struct net_device *net)
{ return (struct device *)((char *)net + T6A_NETDEV_EMBEDDED_DEV); }
static inline void *t6a_netdev_priv(const struct net_device *net)
{ return (char *)net + T6A_NETDEV_PRIV; }

static inline struct usb_function_instance *t6a_fi_from_opts(void *opts)
{ return (struct usb_function_instance *)opts; }

#endif
