# 2026-08-30 Zen3 primary policy

- `trust prefer` makes chrony select ZEN3 despite the household-accepted
  0.3-0.8 second difference from Internet NTP.
- A sender restart restored packets; normal live state reached `#* ZEN3`,
  Reach 125, LastRx 3 seconds, with Internet NTP still configured.
- The feeder now invalidates SHM after 10 seconds without a valid packet.
- In live testing, chrony 4.6.1 still retained `#* ZEN3` after Reach reached
  zero. Restarting chrony with sender stopped selected Internet NTP, and
  restarting sender later returned selection to ZEN3. Automatic fallback on
  sender stop therefore remains unresolved and must not be claimed complete.
- Sender was restored and is running at handoff.
