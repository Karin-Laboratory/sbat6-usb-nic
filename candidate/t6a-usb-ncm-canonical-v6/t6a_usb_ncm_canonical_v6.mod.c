#include <linux/build-salt.h>
#include <linux/module.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

BUILD_SALT;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(.gnu.linkonce.this_module) = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

static const struct modversion_info ____versions[]
__used __section(__versions) = {
	{ 0x3a3eb6e9, "module_layout" },
	{ 0x2f2c95c4, "flush_work" },
	{ 0x2d3385d3, "system_wq" },
	{ 0xc853d0c1, "kmalloc_caches" },
	{ 0xf03affba, "usb_gstrings_attach" },
	{ 0x349f6745, "usb_free_all_descriptors" },
	{ 0x349cba85, "strchr" },
	{ 0xc41263c7, "usb_ep_disable" },
	{ 0x6bfad17f, "usb_ep_enable" },
	{ 0x98cf60b3, "strlen" },
	{ 0xffaa944, "usb_ep_queue" },
	{ 0x41ed3709, "get_random_bytes" },
	{ 0xa0c6befa, "hrtimer_cancel" },
	{ 0xc7a4fbed, "rtnl_lock" },
	{ 0xa7168f9a, "netif_carrier_on" },
	{ 0xab6d5b3b, "hex_to_bin" },
	{ 0x850b4108, "netif_carrier_off" },
	{ 0x87b9dba2, "__dev_kfree_skb_any" },
	{ 0x409bcb62, "mutex_unlock" },
	{ 0x40f79de7, "usb_ep_set_halt" },
	{ 0xa0e62d4b, "usb_ep_alloc_request" },
	{ 0x3c3ff9fd, "sprintf" },
	{ 0x50fcff8a, "usb_function_unregister" },
	{ 0x15ba50a6, "jiffies" },
	{ 0xaea365c, "__netdev_alloc_skb" },
	{ 0xca336344, "netif_rx" },
	{ 0xeef4be27, "skb_queue_purge" },
	{ 0xfbdfc558, "hrtimer_start_range_ns" },
	{ 0x96e8c68d, "_dev_warn" },
	{ 0xdcb764ad, "memset" },
	{ 0x6f1609d2, "dev_set_mac_address" },
	{ 0xf6c100b0, "netif_tx_wake_queue" },
	{ 0x894defe7, "usb_put_function_instance" },
	{ 0x6a6e05bf, "kstrtou8" },
	{ 0x977f511b, "__mutex_init" },
	{ 0xc5850110, "printk" },
	{ 0xd13083a5, "ethtool_op_get_link" },
	{ 0x4696de3c, "usb_ep_autoconfig" },
	{ 0x216fb39a, "free_netdev" },
	{ 0xe17e26a0, "register_netdev" },
	{ 0x5792f848, "strlcpy" },
	{ 0x2ab7989d, "mutex_lock" },
	{ 0x69dd3b5b, "crc32_le" },
	{ 0x875b9ac1, "config_group_init_type_name" },
	{ 0xa168b429, "_dev_err" },
	{ 0x6571549d, "usb_function_register" },
	{ 0xc8ea074a, "usb_ep_dequeue" },
	{ 0x167c5967, "print_hex_dump" },
	{ 0x2b33cc1, "skb_queue_tail" },
	{ 0xf73df0f0, "_dev_info" },
	{ 0xcb4d5838, "__alloc_skb" },
	{ 0x9c1e5bf5, "queued_spin_lock_slowpath" },
	{ 0xdecd0b29, "__stack_chk_fail" },
	{ 0x82df7be2, "eth_type_trans" },
	{ 0xb384ca2e, "cpu_hwcap_keys" },
	{ 0xe734bc1, "config_ep_by_speed" },
	{ 0xa36ea15e, "usb_ep_free_request" },
	{ 0x65df82a0, "kmem_cache_alloc_trace" },
	{ 0x5fce6074, "eth_validate_addr" },
	{ 0x37a0cba, "kfree" },
	{ 0x4829a47e, "memcpy" },
	{ 0x1ee7d3cd, "hrtimer_init" },
	{ 0x96848186, "scnprintf" },
	{ 0x11ebaf0f, "usb_assign_descriptors" },
	{ 0xf3e04da8, "usb_interface_id" },
	{ 0x2f5b913b, "skb_dequeue" },
	{ 0x2594d818, "unregister_netdev" },
	{ 0x7c23703, "hrtimer_try_to_cancel" },
	{ 0xc5b6f236, "queue_work_on" },
	{ 0x656e4a6e, "snprintf" },
	{ 0xfc7b3f68, "usb_os_desc_prepare_interf_dir" },
	{ 0xe0fc520, "skb_put" },
	{ 0xe4cef668, "eth_mac_addr" },
	{ 0x14b89635, "arm64_const_caps_ready" },
	{ 0x6e720ff2, "rtnl_unlock" },
	{ 0x224a0869, "alloc_etherdev_mqs" },
};

MODULE_INFO(depends, "");

