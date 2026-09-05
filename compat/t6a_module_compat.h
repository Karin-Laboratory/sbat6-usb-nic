/* SPDX-License-Identifier: GPL-2.0 */
#ifndef T6A_MODULE_COMPAT_H
#define T6A_MODULE_COMPAT_H

/* Loader ABI is intentionally a gate, not a portable struct replacement. */
#if !defined(T6A_MODULE_LOADER_ABI_PROVEN)
#error "T6A module loader ABI has not been proven for this kernel"
#endif

#include <linux/module.h>
#endif
