// SPDX-License-Identifier: GPL-2.0
/*
 * T6A NCM fast-route preflight module.
 *
 * This artifact deliberately does not register a USB function, touch configfs,
 * select a UDC, change a USB role, or install parameter setters.  It exists to
 * validate the 5.4.238 external-module ABI and the proposed tuning envelope
 * before the data plane is backported into the kernel tree.
 */
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>

#define SBAT6_NCM_MAX_NTB  (1024U * 1024U)
#define SBAT6_NCM_MAX_DEPTH 256U

static unsigned int ntb_size = 65536;
module_param_named(ntb_size, ntb_size, uint, 0444);
MODULE_PARM_DESC(ntb_size, "planned NTB size in bytes; preflight only");

static unsigned int tx_depth = 64;
module_param_named(tx_depth, tx_depth, uint, 0444);
MODULE_PARM_DESC(tx_depth, "planned TX request depth; preflight only");

static unsigned int rx_depth = 64;
module_param_named(rx_depth, rx_depth, uint, 0444);
MODULE_PARM_DESC(rx_depth, "planned RX request depth; preflight only");

static unsigned int flush_us = 80;
module_param_named(flush_us, flush_us, uint, 0444);
MODULE_PARM_DESC(flush_us, "planned TX flush delay; preflight only");

static bool ntb32 = true;
module_param_named(ntb32, ntb32, bool, 0444);
MODULE_PARM_DESC(ntb32, "planned NTB32 mode; preflight only");

static int __init sbat6_ncm_fast_init(void)
{
	/* No setter, worker, USB registration, endpoint lookup, or netdev action. */
	if (!ntb_size || ntb_size > SBAT6_NCM_MAX_NTB ||
	    tx_depth > SBAT6_NCM_MAX_DEPTH || rx_depth > SBAT6_NCM_MAX_DEPTH ||
	    flush_us > 1000000)
		return -EINVAL;

	pr_info("sbat6_ncm_fast: preflight only, no UDC bind (ntb=%u tx=%u rx=%u flush=%uus ntb32=%u)\n",
		ntb_size, tx_depth, rx_depth, flush_us, ntb32);
	return 0;
}

static void __exit sbat6_ncm_fast_exit(void)
{
	pr_info("sbat6_ncm_fast: preflight unloaded; no USB state changed\n");
}

module_init(sbat6_ncm_fast_init);
module_exit(sbat6_ncm_fast_exit);
MODULE_DESCRIPTION("T6A NCM fast-route ABI/preflight module; never binds UDC");
MODULE_LICENSE("GPL");
