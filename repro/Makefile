obj-m += t6a_usb_ncm_65532_candidate_v1.o
t6a_usb_ncm_65532_candidate_v1-objs := u_ether.o f_ncm.o
KERNEL_SRC ?= /path/to/vendor-linux-5.4.238
ccflags-y += -I$(src)/../driver/t6a-ncm-65532-ntb-candidate-v1/source -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1 -include $(KERNEL_SRC)/include/linux/usb/composite.h
KBUILD_CFLAGS += -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1
