(() => {
  "use strict";

  const PREFIX = "[VenueAdSkip]";
  const POLL_MS = 250;
  const RESTORE_DELAY_MS = 700;
  const SEEK_EPSILON = 0.08;
  const FALLBACK_AFTER_MS = 500;
  const FALLBACK_RATE = 16;
  let state = null;
  let restoreTimer = 0;
  let lastUrl = location.href;
  let seekTimer = 0;
  let cleanBaseline = null;

  function log(event, extra = {}) {
    const entry = { event, url: location.href, ...extra };
    console.info(PREFIX, event, extra);
    try { chrome.runtime.sendMessage({ type: "venue-ad-log", entry }); } catch (_) {}
  }

  function video() {
    return document.querySelector(".html5-main-video, video");
  }

  function isAd(videoElement) {
    const player = document.querySelector("#movie_player");
    const visible = (element) => {
      if (!element) return false;
      const style = getComputedStyle(element);
      return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
    };
    return Boolean(
      player?.classList.contains("ad-showing") ||
      document.querySelector(".ad-showing") ||
      visible(document.querySelector(".ytp-ad-player-overlay")) ||
      visible(document.querySelector(".ytp-ad-text")) ||
      visible(document.querySelector(".video-ads.ytp-ad-module:not(:empty)")) ||
      videoElement?.classList.contains("ad-showing")
    );
  }

  function startAd(v) {
    if (state?.video === v) return;
    if (state) restore("new-ad");
    const baseline = cleanBaseline?.video === v ? cleanBaseline : v;
    state = { video: v, rate: baseline.rate || 1, muted: Boolean(baseline.muted),
      startedAt: performance.now(), seekAt: 0, fallback: false };
    log("ad-detected", { rate: state.rate, muted: state.muted, duration: v.duration });
    // duration is often 0/Infinity for the first few polls of an ad.  The
    // retry in tick() is intentional: a one-shot seek is race-prone on SPA
    // navigations and was the main source of intermittent fallback behavior.
    seekToEnd(v);
  }

  function seekToEnd(v) {
    if (!Number.isFinite(v.duration) || v.duration <= 0) return;
    try {
      v.currentTime = Math.max(0, v.duration - SEEK_EPSILON);
      if (state?.video === v) state.seekAt = performance.now();
      v.dispatchEvent(new Event("timeupdate"));
      log("seek-to-end", { duration: v.duration, position: v.currentTime });
    } catch (error) {
      log("seek-failed", { error: String(error) });
    }
  }

  function cancelRestore() {
    clearTimeout(restoreTimer);
    restoreTimer = 0;
  }

  function fallback(v) {
    if (!state || state.fallback || state.video !== v) return;
    state.fallback = true;
    try { v.playbackRate = FALLBACK_RATE; v.muted = true; } catch (_) {}
    log("fallback-16x-muted");
    try { v.play().catch(() => {}); } catch (_) {}
  }

  function restore(reason) {
    if (!state) return;
    cancelRestore();
    clearTimeout(seekTimer);
    seekTimer = 0;
    const old = state;
    state = null;
    try {
      if (old.video.isConnected) {
        old.video.playbackRate = old.rate;
        old.video.muted = old.muted;
      }
    } catch (_) {}
    log("ad-finished-restored", { reason, rate: old.rate, muted: old.muted, fallback: old.fallback });
  }

  function tick() {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      if (state) restore("navigation");
      log("navigation");
    }
    const v = video();
    const ad = v && isAd(v);
    if (v && !ad && !state) {
      cleanBaseline = { video: v, rate: v.playbackRate || 1, muted: v.muted };
    }
    if (ad) {
      startAd(v);
      cancelRestore();
      // Keep trying after metadata becomes available.  YouTube can expose
      // the ad marker before it exposes a finite media duration.
      if (state && Number.isFinite(v.duration) && v.duration > 0 &&
          v.currentTime < v.duration - SEEK_EPSILON) {
        seekToEnd(v);
      }
      if (state && performance.now() - state.startedAt >= FALLBACK_AFTER_MS) {
        const nearEnd = Number.isFinite(v.duration) && v.currentTime >= v.duration - 0.2;
        const seekStalled = state.seekAt > 0 && performance.now() - state.seekAt >= 900;
        if (!nearEnd || seekStalled || v.ended === false && v.currentTime < 0.1) fallback(v);
      }
    } else if (state) {
      // The ad marker briefly disappears while YouTube swaps player DOM.
      // Debounce it so that a transient clear cannot restore state too early
      // and then capture the fallback settings as the next ad's baseline.
      if (!restoreTimer) {
        restoreTimer = setTimeout(() => {
          restoreTimer = 0;
          if (state && (!video() || !isAd(video()))) restore("ad-marker-cleared");
        }, RESTORE_DELAY_MS);
      }
    }
  }

  function start() {
    // At document_start documentElement is not guaranteed to exist.
    // Installing the observer unconditionally used to terminate the whole
    // content script on some YouTube navigations.
    const root = document.documentElement || document;
    new MutationObserver(tick).observe(root, {
      childList: true, subtree: true, attributes: true, attributeFilter: ["class"]
    });
    setInterval(tick, POLL_MS);
    document.addEventListener("loadedmetadata", tick, true);
    document.addEventListener("durationchange", tick, true);
    tick();
    log("started", { pollMs: POLL_MS });
  }

  if (document.documentElement) start();
  else document.addEventListener("DOMContentLoaded", start, { once: true });
})();
