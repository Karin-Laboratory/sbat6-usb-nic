# raspi2 Zen3 GNSS time source

## Household operating policy

Zen3 GNSS is not intended to be a precision NTP clock. In this household,
approximately 0.3-second error is acceptable because the goal is an independent
auxiliary GNSS time source. Do not mark ZEN3 unsuitable merely for that expected
error; monitor expansion beyond the measured baseline instead.

## Role and household policy (2026-08-30)

Zen3 (ASUS_Z012DA) is raspi2's PRIMARY time source. Internet NTP remains
configured, monitored, usable, and is the BACKUP selected only when Zen3 is
unavailable. The household intentionally accepts approximately 0.3-0.8 s of
Zen3 error; Internet NTP must not be preferred merely because it is more
precise. This policy must not be changed back to the usual precision-first
selection rule.

## Identity and data path

- USB VID:PID: `0b05:4dae`
- Android serial: `GCAZCY05P824JAW`
- Wi-Fi sender address observed: `192.168.1.40`
- UDP status: Zen3 broadcasts to `192.168.3.255:40123`
- raspi2 receiver: `/home/codex/zen3-ntp/zen3_gnss_feeder.py`
- receiver service: `zen3-gnss-time.service`, user `codex`
- chrony refclock: SHM 0, refid `ZEN3`
- packet marker: `zen3-gnss-v1-7f3c9a`

Important diagnostic rule: GNSS main path is the Android sender's UDP status
datagram, not ADB. ADB is only auxiliary diagnosis.

## Patrol observations

Observe USB presence, model/serial, ADB as auxiliary, sender app/service,
UDP/40123 listener and last packet/accept/reject, chrony ZEN3 Reach and LastRx,
selected source, and Internet NTP fallback. Distinguish `USB+ADB+service but
no UDP` as sender/input failure.

## Current incident note (2026-08-30)

The sender package was absent after USB reconnection. The stored newer APK also
had an invalid ZIP path (`../dex/classes.dex`). A corrected, locally signed
build was installed and started. The source additionally needed GPS epoch to
Unix UTC conversion and a fallback to GPS provider `Location.getTime()` because
this Zenfone firmware registers no usable GNSS measurements callback.

Packets are now accepted. Zen3 is configured with `trust prefer` so it is the
preferred source while healthy and is not rejected solely for the accepted
household offset. Internet NTP remains configured as the fallback.

The live fallback test exposed a chrony 4.6.1/SHM behavior: invalidating the
SHM sample made Reach zero, but the currently selected trusted refclock could
remain `*` until chrony was restarted. The feeder now invalidates stale SHM
data after 10 seconds, but automatic sender-stop fallback is not yet proven
without a chrony restart; do not report this as complete until resolved.

## 2026-08-30 baseline

- Feeder offset: approximately -0.12 to -0.22 s (GNSS minus raspi2)
- Chrony ZEN3 sample: approximately +0.195 s; standard deviation 0.016 s
- Normal: absolute offset <= 0.8 s
- WARN: absolute offset > 1 s for 3 consecutive patrols
- ALERT: absolute offset > 2 s for 3 consecutive patrols
- CRITICAL: absolute offset > 5 s for 3 consecutive patrols
