// Haseen Kids - background service worker (Manifest V3)
// Responsibilities:
//   1. Ask the local Haseen proxy what to do with every top-level navigation.
//   2. Route YouTube watch pages into the built-in ad-free player (no blocking,
//      no parent-approval wait screen).
//   3. Turn a hard proxy error (blocked CONNECT) into the friendly Arabic
//      block page instead of a raw browser error.

const PROXY = "http://127.0.0.1:8089";

// Browser internals are not web pages - never touch them.
const SKIP = /^(chrome|edge|brave|about|devtools|chrome-extension|extension|moz-extension):/i;

async function ask(url) {
  try {
    const r = await fetch(`${PROXY}/should_redirect?u=${encodeURIComponent(url)}`, { cache: "no-store" });
    if (!r.ok) return null;
    return await r.json();
  } catch (e) {
    // Proxy not running: fail open so the child is never stuck offline.
    return null;
  }
}

chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  if (details.frameId !== 0) return;          // top-level navigations only
  const url = details.url || "";
  if (!url.startsWith("http") || SKIP.test(url)) return;
  if (url.startsWith(PROXY)) return;          // our own pages

  const verdict = await ask(url);
  if (!verdict) return;

  if (verdict.action === "REDIRECT_YOUTUBE" && verdict.redirect) {
    chrome.tabs.update(details.tabId, { url: verdict.redirect });
    return;
  }

  if (verdict.blocked && verdict.block_page) {
    chrome.tabs.update(details.tabId, { url: verdict.block_page });
  }
});

// A blocked HTTPS CONNECT fails at the network layer; show the Arabic block
// page instead of ERR_TUNNEL_CONNECTION_FAILED.
chrome.webNavigation.onErrorOccurred.addListener(async (details) => {
  if (details.frameId !== 0) return;
  const url = details.url || "";
  if (!url.startsWith("http")) return;

  const verdict = await ask(url);
  if (verdict && verdict.block_page) {
    chrome.tabs.update(details.tabId, { url: verdict.block_page });
  }
});

// Toolbar popup asks for live proxy status
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "status") {
    fetch(`${PROXY}/status`).then(r => r.json())
      .then(d => sendResponse({ online: true, data: d }))
      .catch(() => sendResponse({ online: false }));
    return true; // keep the channel open for the async reply
  }
});
