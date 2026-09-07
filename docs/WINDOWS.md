# Windows host

The confirmed host path uses Windows `UsbNcm.sys` and enumerates the device as `UsbNcm Host Device`, VID:PID `2C7C:7006`.

The test addressing is:

```text
T6A       test-net.77.1/24
Windows   test-net.77.2/24
```

Verify enumeration and link carrier before assigning addresses or running iperf. The established vendor baseline is approximately 1.34–1.39 Gbit/s T6A→Windows and 1.01–1.03 Gbit/s Windows→T6A, with the recorded baseline runs showing TCP Retr 0 in the forward direction.

## Troubleshooting: UDC configured/SuperSpeed/carrier, but ping or iperf does not work

If the UDC is configured, the USB link is SuperSpeed, and the interface has carrier but ping or iperf3 fails, check the Windows route and interface metric. Tailscale, an Exit Node, or another VPN can take the route for the USB-direct subnet. Temporarily stop Tailscale/Exit Node or the relevant VPN, then re-test with ping first and iperf3 only after ping succeeds.

In the SBA6D / Windows 11 check recorded for this repository, stopping Tailscale/Exit Node restored ping 3/3 and iperf3 P1 at 1.42 Gbit/s without changing USB, the driver, or ConfigFS. Do not change the firewall or driver first; verify route/interface selection and the VPN state before making those changes.
