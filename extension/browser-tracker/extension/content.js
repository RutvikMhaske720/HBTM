// --- Variables ---
let clickCount = 0;
let doubleClickCount = 0;
let rightClickCount = 0;
let totalScrollDistance = 0;
let maxScroll = 0;
let scrollStartPos = 0;
let keysPressed = 0;
let sessionStartTime = Date.now();
let lastInteractionTime = Date.now();

// --- Configuration ---
const FLUSH_INTERVAL_MS = 10000; // Send metrics every 10 seconds
let flushInterval;

// Check if tracking is enabled
chrome.storage.local.get(['trackingEnabled'], (result) => {
    if (result.trackingEnabled !== false) {
        startTracking();
    }
});

chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.trackingEnabled) {
        if (changes.trackingEnabled.newValue) {
            startTracking();
        } else {
            stopTracking();
        }
    }
});

function startTracking() {
    document.addEventListener('click', onClick);
    document.addEventListener('dblclick', onDoubleClick);
    document.addEventListener('contextmenu', onRightClick);
    document.addEventListener('scroll', onScroll);
    document.addEventListener('keydown', onKeyDown);
    
    // Track active time
    document.addEventListener('mousemove', updateInteraction);
    document.addEventListener('keypress', updateInteraction);
    
    flushInterval = setInterval(flushMetrics, FLUSH_INTERVAL_MS);
    
    // Initial scroll pos
    scrollStartPos = window.scrollY;
}

function stopTracking() {
    document.removeEventListener('click', onClick);
    document.removeEventListener('dblclick', onDoubleClick);
    document.removeEventListener('contextmenu', onRightClick);
    document.removeEventListener('scroll', onScroll);
    document.removeEventListener('keydown', onKeyDown);
    
    document.removeEventListener('mousemove', updateInteraction);
    document.removeEventListener('keypress', updateInteraction);
    
    clearInterval(flushInterval);
    flushMetrics(); // Final flush
}

function updateInteraction() {
    lastInteractionTime = Date.now();
}

function onClick() {
    clickCount++;
    updateInteraction();
}

function onDoubleClick() {
    doubleClickCount++;
    updateInteraction();
}

function onRightClick() {
    rightClickCount++;
    updateInteraction();
}

function onScroll() {
    const currentScroll = window.scrollY;
    const scrollDelta = Math.abs(currentScroll - scrollStartPos);
    totalScrollDistance += scrollDelta;
    
    if (currentScroll > maxScroll) {
        maxScroll = currentScroll;
    }
    
    scrollStartPos = currentScroll;
    updateInteraction();
}

function onKeyDown(e) {
    // Avoid sensitive fields (password fields)
    const activeEl = document.activeElement;
    if (activeEl && (activeEl.type === 'password' || activeEl.dataset.sensitive)) {
        return;
    }
    
    // Only count printable characters or significant keys if needed
    // But for simple "total keys pressed", we increment
    keysPressed++;
    updateInteraction();
}

function flushMetrics() {
    // Only send if there's activity
    if (clickCount === 0 && doubleClickCount === 0 && rightClickCount === 0 && 
        totalScrollDistance === 0 && keysPressed === 0) {
        return;
    }
    
    const timeOnPage = Date.now() - sessionStartTime;
    const idleTime = Date.now() - lastInteractionTime;
    
    const payload = {
        url: window.location.href,
        title: document.title,
        clicks: clickCount,
        doubleClicks: doubleClickCount,
        rightClicks: rightClickCount,
        scrollDistance: totalScrollDistance,
        maxScroll: maxScroll,
        keysPressed: keysPressed,
        timeOnPage: timeOnPage,
        idleTime: idleTime
    };

    // Send via standard messaging to background script
    // which in turn will use sendEvent via utils.js? 
    // Content scripts can't import utils.js cleanly without extra setup, 
    // so we just fetch directly or use runtime message.
    // We'll use fetch directly since localhost allows it.
    
    fetch('http://localhost:8000/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            type: 'page_interaction',
            timestamp: new Date().toISOString(),
            data: payload
        })
    }).catch(err => {
        // Silently fail if server is down
        console.warn('Tracker server not reachable:', err);
    });
    
    // Reset counters after flushing
    clickCount = 0;
    doubleClickCount = 0;
    rightClickCount = 0;
    totalScrollDistance = 0;
    keysPressed = 0;
}

// Flush on unload
window.addEventListener('beforeunload', () => {
    flushMetrics();
});
