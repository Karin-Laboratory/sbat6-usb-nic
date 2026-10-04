#ifndef BUTLERX_ABI_ASSERT_H
#define BUTLERX_ABI_ASSERT_H
#include <linux/module.h>
static inline void butlerx_struct_module_assert(void)
{
        BUILD_BUG_ON(sizeof(struct module) != 0x340);
        BUILD_BUG_ON(offsetof(struct module, init) != 0x150);
        BUILD_BUG_ON(offsetof(struct module, exit) != 0x328);
}
#endif
