# Zen3 GNSS patrol

status: ACTIVE
owner: ButlerX
target: Zen3 GNSS time source on raspi2

Policy: expected primary is ZEN3; Internet NTP is monitored backup. The
patrol records `expected_primary=ZEN3` and flags an Internet-selected source as
unexpected fallback while Zen3 is usable.

Implementation: `tools/zen3_gnss_patrol.py`; bounded history is kept in
`state/zen3_gnss_history.jsonl` (500 records) and state in
`state/zen3_gnss_patrol.json`. The existing `butlerx-patrol.service` invokes it
every 5 minutes; standalone timer units are retained as an optional deployment
artifact because this session has no user-systemd DBus.
Discord notification is emitted only on persistent WARN/ALERT/CRITICAL
transitions or recovery; a short outage with healthy Internet NTP is degraded
auxiliary-source status, not a system-clock alert.

Patrol with a grace period and repeated observations. A short USB disconnect is
not a major alert if Internet NTP remains selected and healthy. Notify only
after persistence; notify recovery when accepted packets and chrony health
return.

Checks:

- USB `0b05:4dae`, ASUS_Z012DA, serial `GCAZCY05P824JAW`
- `zen3-gnss-time.service` active
- UDP/40123 listener present
- packet last-received time and feeder accept/reject reason
- chrony `ZEN3` Reach and LastRx
- selected source and Internet NTP fallback
- ADB only as supporting evidence

Interpretation:

- USB/ADB/service healthy but no UDP = GNSS sender/input failure.
- ZEN3 stopped plus Internet NTP healthy = degraded auxiliary source, not
  time-sync critical.
- Never infer GNSS failure from ADB absence alone.
