// Haseen Kids - Content Script
(function() {
    // If inside a YouTube video page, hide ads containers immediately
    if (window.location.hostname.includes("youtube.com")) {
        const style = document.createElement("style");
        style.textContent = `
            .video-ads, .ytp-ad-module, ytd-ad-slot-renderer,
            #player-ads, ytd-banner-promo-renderer { display: none !important; }
        `;
        document.documentElement.appendChild(style);
    }
})();
