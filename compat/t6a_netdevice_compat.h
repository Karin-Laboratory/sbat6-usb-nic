/* SPDX-License-Identifier: GPL-2.0 */
#ifndef T6A_NETDEVICE_COMPAT_H
#define T6A_NETDEVICE_COMPAT_H

/*
 * Deliberately no guessed struct definition is exported here.  Consumers
 * must opt into an exact, hash-pinned vendor header and prove the assertions
 * in the real translation unit before defining T6A_NETDEVICE_LAYOUT_PROVEN.
 */
#if !defined(T6A_NETDEVICE_LAYOUT_PROVEN)
#error "T6A net_device layout is not proven for this build"
#endif

#include <linux/netdevice.h>
#endif
