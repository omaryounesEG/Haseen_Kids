// Haseen Kids - Background Interceptor & Heartbeat
const DAEMON_URL = "http://127.0.0.1:8089";

// Listen to navigation events
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
    if (details.frameId !== 0) return; // Only main frame

    const url = details.url.toLowerCase();

    // 1. Intercept YouTube Watch Links
    if (url.includes("youtube.com/watch") || url.includes("youtu.be/") || url.includes("youtube.com/shorts/")) {
        // Redirect to local proxy clean player handler
        const redirectUrl = `${DAEMON_URL}/intercept_youtube?url=${encodeURIComponent(details.url)}`;
        chrome.tabs.update(details.tabId, { url: redirectUrl });
    }
});

// Periodic heartbeat to Core Daemon (reporting active tab and title)
setInterval(() => {
    chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
        if (tabs && tabs.length > 0 && tabs[0].url) {
            const activeTab = tabs[0];
            fetch(`${DAEMON_URL}/heartbeat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: activeTab.url,
                    title: activeTab.title || "",
                    timestamp: Date.now()
                })
            }).catch(() => {
                // Daemon offline, ignore
            });
        }
    });
}, 4000);
