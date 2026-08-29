# justnottoday

- Hostname: `OpenWrt-Desktop`; estate name: `justnottoday`.
- ELECOM WRC-2533GHBK-I, MediaTek MT7621, OpenWrt 25.12.5 revision `r33051-f5dae5ece4`.
- Role: L2 switch + Wi-Fi AP. `lan1`–`lan4`, `wan`, `phy0-ap0`, `phy0-ap1`, `phy1-ap0` are one `br-lan` bridge; WAN is intentionally a bridge member.
- Management is `network.lan`, DHCP client on `br-lan`; observed address `192.168.1.42/22`, gateway/DNS `192.168.0.1`, DHCP `192.168.0.88`, NTP `192.168.0.26`.
- SSIDs: `justnottoday` on 2.4 GHz and 5 GHz, plus `infra2g` on 2.4 GHz only; all baseline APs use AP mode and `sae-mixed`.
- Access is SSH alias `justnottoday` with a forced-command read-only observation key. The guard passes no remote command or user arguments. Arbitrary shell, configuration changes, service restarts, reboot, package changes, topology changes, key changes, and privilege expansion are forbidden.
- ButlerX has observation authority only; anomalies are recorded and proposed to the owner. No automatic remediation.
- Overlay is very small (about 1.9 MB total); alert threshold is 80% used.
