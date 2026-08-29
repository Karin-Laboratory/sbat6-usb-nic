# raspi2 Zen3 GNSS time source

## Household operating policy

Zen3 GNSS is not intended to be a precision NTP clock. In this household,
approximately 0.3-second error is acceptable because the goal is an independent
auxiliary GNSS time source. Do not mark ZEN3 unsuitable merely for that expected
error; monitor expansion beyond the measured baseline instead.

## Role

Zen3 (ASUS_Z012DA) is an auxiliary GNSS status/time source for raspi2.
Internet NTP remains the authoritative fallback and must remain healthy when
Zen3 is absent or rejected.

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

Packets are now accepted. Internet NTP remains the preferred/main source.
ZEN3 is configured as a trusted auxiliary source without `prefer`; it must not
cause large clock steps.

## 2026-08-30 baseline

- Feeder offset: approximately -0.12 to -0.22 s (GNSS minus raspi2)
- Chrony ZEN3 sample: approximately +0.195 s; standard deviation 0.016 s
- Normal: absolute offset <= 0.8 s
- WARN: absolute offset > 1 s for 3 consecutive patrols
- ALERT: absolute offset > 2 s for 3 consecutive patrols
- CRITICAL: absolute offset > 5 s for 3 consecutive patrols
