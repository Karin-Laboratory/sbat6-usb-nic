# Ethernet cable test — 2026-10-01

The owner connected the Ethernet cable after reserving the adapter MAC in
DHCP. The same public-recipe modules remained loaded.

- Enabled eth2 with `ip link set eth2 up`.
- Carrier became 1; negotiated Ethernet speed was 1000 Mbps.
- BusyBox udhcpc obtained the reserved address, subnet /22, lease 21600 s.
- A temporary lease hook configured only interface address/netmask; no
  default route or DNS changes were made. Existing management access stayed up.
- ICMP initiated by T6B, explicitly using eth2, to the permitted raspi2 host:
  3 transmitted, 3 received, 0% loss. RTT min/avg/max 2.233/42.289/122.176 ms.
- After this test: RX 118 packets / TX 6, RX and TX errors and drops all zero.
- No new Oops, BUG, kernel CPU warning or call-trace marker in the stream.

Reverse-direction initiation was also tested: raspi2 to the reserved target
address returned 0/3. A second attempt during a six-second target eth2 ICMP
capture produced zero captured packets. This does not identify the exact
filtering/routing boundary, but it does not demonstrate an ICMP request
reaching the driver and being dropped by the target. No firewall restrictions
were changed or bypassed. The owner subsequently confirmed that raspi2's
codex account is intentionally restricted by a firewall from connecting to
arbitrary LAN addresses. The reverse test therefore is not a valid negative
NIC test; it is subject to the management host's access boundary. The exact
rule/counter was not independently inspected, and inbound NIC reachability
cannot be assessed with this restricted test origin.

This establishes DHCP and a bidirectional exchange of basic packets initiated
by the target. It does not establish unrestricted inbound reachability,
sustained throughput, or long-term stability. The udhcpc test used `-n -q`;
the one-shot client exited after obtaining the lease. Automatic lease renewal
and persistent configuration were not installed.
