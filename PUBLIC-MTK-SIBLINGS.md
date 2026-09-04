# Public MTK sibling sources

Exploration date: 2026-09-05. Exact indexed public matches for the five
vendor-only `ppe_usb_*` hook names were not found, so no false exact-match
claim is made. The following public sibling sources are retained as family
references:

| source | commit/version | relevance |
|---|---|---|
| https://github.com/torvalds/linux/blob/master/drivers/usb/gadget/function/u_ether.h | current master (web snapshot) | `gether_setup_name_default`, netdev lifecycle and gadget Ethernet API |
| https://android.googlesource.com/kernel/mediatek/+/android-6.0.1_r0.16/drivers/usb/gadget/u_ether.c | `android-6.0.1_r0.16` | MediaTek kernel u_ether implementation and netdev/request lifecycle |
| https://github.com/torvalds/linux/tree/master/drivers/net/ethernet/mediatek | current master | public MTK PPE/offload family (`mtk_ppe*`) |
| https://git.openwrt.org/openwrt/staging/nbd/tree/target/linux/generic/backport-5.10/610-v5.13-35-net-ethernet-mediatek-ppe-fix-busy-wait-loop.patch?h=9e137bb10e2652dd1eb826e228d9842f872789f | `9e137bb10e2652dd1eb826e228d9842f872789f` | OpenWrt MTK PPE integration/backport |
| https://github.com/ytalm/openwrt-rax3000m-nand | repository default branch | documented MTK USB external-netdev to PPE integration in a sibling SoC tree |

The public material supports the family-level conclusion: vendor `usb_net`
contains a u_ether derivative plus MTK/PPE integration. It does not identify
the exact RG620T source or prove which vendor hook is necessary for ConfigFS
attributes.
