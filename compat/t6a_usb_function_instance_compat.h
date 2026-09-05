/* SPDX-License-Identifier: GPL-2.0 */
#ifndef T6A_USB_FUNCTION_INSTANCE_COMPAT_H
#define T6A_USB_FUNCTION_INSTANCE_COMPAT_H

#include <linux/usb/composite.h>

/* Offsets require a vendor-header assertion in the actual TU. */
#if !defined(T6A_USB_FUNCTION_INSTANCE_ABI_PROVEN)
#warning "USB function-instance ABI is not yet promoted to stable API"
#endif

#endif
