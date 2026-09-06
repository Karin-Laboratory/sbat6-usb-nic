obj-m += t6a_usb_ncm_canonical_v6.o
t6a_usb_ncm_canonical_v6-objs := u_ether.o f_ncm.o
ccflags-y += -I$(src)/source -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1 -include $(KERNEL_SRC)/include/linux/usb/composite.h
KBUILD_CFLAGS += -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1
