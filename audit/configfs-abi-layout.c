#include <linux/module.h>
#include <linux/configfs.h>
#include <linux/usb/composite.h>
#include <linux/stddef.h>

#define ROW(t, m) pr_info("ABI sizeof(%s)=%zu offsetof(%s,%s)=%zu\\n", #t, sizeof(t), #t, #m, offsetof(t, m))

#define ABI_VALUE(name, value) char name[(value) + 1]
ABI_VALUE(abi_size_config_item, sizeof(struct config_item));
ABI_VALUE(abi_size_config_group, sizeof(struct config_group));
ABI_VALUE(abi_size_config_item_type, sizeof(struct config_item_type));
ABI_VALUE(abi_size_configfs_attribute, sizeof(struct configfs_attribute));
ABI_VALUE(abi_size_usb_function_instance, sizeof(struct usb_function_instance));
ABI_VALUE(abi_size_usb_function_driver, sizeof(struct usb_function_driver));
ABI_VALUE(abi_off_config_item_type_ct_owner, offsetof(struct config_item_type, ct_owner));
ABI_VALUE(abi_off_config_item_type_ct_item_ops, offsetof(struct config_item_type, ct_item_ops));
ABI_VALUE(abi_off_config_item_type_ct_group_ops, offsetof(struct config_item_type, ct_group_ops));
ABI_VALUE(abi_off_config_item_type_ct_attrs, offsetof(struct config_item_type, ct_attrs));
ABI_VALUE(abi_off_config_item_type_ct_bin_attrs, offsetof(struct config_item_type, ct_bin_attrs));
ABI_VALUE(abi_off_usb_function_instance_group, offsetof(struct usb_function_instance, group));
ABI_VALUE(abi_off_usb_function_instance_free_func_inst, offsetof(struct usb_function_instance, free_func_inst));
ABI_VALUE(abi_off_usb_function_driver_name, offsetof(struct usb_function_driver, name));
ABI_VALUE(abi_off_usb_function_driver_mod, offsetof(struct usb_function_driver, mod));
ABI_VALUE(abi_off_usb_function_driver_alloc_inst, offsetof(struct usb_function_driver, alloc_inst));
ABI_VALUE(abi_off_usb_function_driver_alloc_func, offsetof(struct usb_function_driver, alloc_func));

static int __init configfs_abi_layout_init(void)
{
	ROW(struct config_item, ci_type);
	ROW(struct config_group, cg_children);
	ROW(struct config_item_type, ct_owner);
	ROW(struct config_item_type, ct_item_ops);
	ROW(struct config_item_type, ct_group_ops);
	ROW(struct config_item_type, ct_attrs);
	ROW(struct config_item_type, ct_bin_attrs);
	ROW(struct configfs_attribute, ca_name);
	ROW(struct configfs_attribute, ca_owner);
	ROW(struct configfs_attribute, ca_mode);
	ROW(struct configfs_attribute, show);
	ROW(struct configfs_attribute, store);
	ROW(struct usb_function_instance, group);
	ROW(struct usb_function_instance, free_func_inst);
	ROW(struct usb_function_driver, name);
	ROW(struct usb_function_driver, mod);
	ROW(struct usb_function_driver, alloc_inst);
	ROW(struct usb_function_driver, alloc_func);
	pr_info("ABI sizeof(struct config_item)=%zu\\n", sizeof(struct config_item));
	pr_info("ABI sizeof(struct config_group)=%zu\\n", sizeof(struct config_group));
	pr_info("ABI sizeof(struct config_item_type)=%zu\\n", sizeof(struct config_item_type));
	pr_info("ABI sizeof(struct configfs_attribute)=%zu\\n", sizeof(struct configfs_attribute));
	pr_info("ABI sizeof(struct usb_function_instance)=%zu\\n", sizeof(struct usb_function_instance));
	pr_info("ABI sizeof(struct usb_function_driver)=%zu\\n", sizeof(struct usb_function_driver));
	return -ENODEV;
}
module_init(configfs_abi_layout_init);
MODULE_LICENSE("GPL");
