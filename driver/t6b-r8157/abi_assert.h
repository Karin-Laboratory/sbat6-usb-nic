#include <linux/module.h>
#include <linux/netdevice.h>

#define CHECK_FIELD(t, f, n) \
	static_assert(offsetof(struct t, f) == (n), #t "." #f)

static_assert(sizeof(struct module) == 0x340, "module size");
CHECK_FIELD(module, init, 0x150);
CHECK_FIELD(module, exit, 0x328);

static_assert(sizeof(struct net_device) == 0x8c0, "netdev size");
CHECK_FIELD(net_device, netdev_ops, 0x1f8);
CHECK_FIELD(net_device, ethtool_ops, 0x200);
CHECK_FIELD(net_device, dev_addr, 0x318);
CHECK_FIELD(net_device, dev, 0x510);
CHECK_FIELD(net_device, _tx, 0x3c0);
static_assert(sizeof(struct netdev_queue) == 0x140, "queue size");
CHECK_FIELD(netdev_queue, state, 0x90);

/* flags is intentionally recorded by audit, not asserted here. */
