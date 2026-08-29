const MAX_LOGS = 200;
let writeQueue = Promise.resolve();

chrome.runtime.onMessage.addListener((message, sender) => {
  if (!message || message.type !== "venue-ad-log") return;
  const entry = {
    at: new Date().toISOString(),
    tabId: sender.tab?.id ?? null,
    ...message.entry,
  };
  // Messages can arrive concurrently from the top document and YouTube
  // frames. Serialize read-modify-write so entries are not lost.
  writeQueue = writeQueue.then(() => chrome.storage.local.get({ logs: [] }))
    .then(({ logs }) => {
      logs.push(entry);
      return chrome.storage.local.set({ logs: logs.slice(-MAX_LOGS) });
    }).catch(() => {});
});
