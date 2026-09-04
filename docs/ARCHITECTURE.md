# Architecture

The target is a SoftBank Air Terminal 6 / SBA6D running vendor Linux 5.4.238 on a MediaTek MTU3 USB controller. The device side exposes a ConfigFS USB gadget containing vendor-provided `ncm.gs8`; configuration `b.1/f5` links that function to the gadget. A Windows or Linux host enumerates the gadget as CDC-NCM and obtains the USB NIC.

The management LAN remains on `br-lan` and is used for SSH through raspi2. The USB link is a separate data plane on `ncm0`. The vendor provider is `usb_net`; its observed aliases are `ncm`, `ecm`, and `rndis`.

The experimental layers are intentionally separated:

1. vendor baseline and recovery;
2. passive telemetry sink;
3. one-variable NCM/kernel performance candidates.

An external module is not assumed to safely replace private `f_ncm`/`u_ether` state. A source-compatible vendor-tree patch is the eventual route for data-plane changes.
