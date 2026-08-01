importScripts('utils.js');

// Default state
chrome.runtime.onInstalled.addListener(() => {
    chrome.storage.local.set({ trackingEnabled: true });
});

// --- Tab Tracking ---
chrome.tabs.onCreated.addListener((tab) => {
    sendEvent('tab_created', {
        tabId: tab.id,
        url: tab.url || tab.pendingUrl,
        title: tab.title,
        incognito: tab.incognito
    });
});

chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
    sendEvent('tab_removed', {
        tabId: tabId,
        windowId: removeInfo.windowId,
        isWindowClosing: removeInfo.isWindowClosing
    });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        sendEvent('tab_updated', {
            tabId: tabId,
            url: tab.url,
            title: tab.title,
            incognito: tab.incognito
        });
    }
});

chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        sendEvent('tab_activated', {
            tabId: tab.id,
            url: tab.url,
            title: tab.title,
            windowId: tab.windowId
        });
    });
});

// --- Window Tracking ---
chrome.windows.onFocusChanged.addListener((windowId) => {
    if (windowId === chrome.windows.WINDOW_ID_NONE) {
        sendEvent('window_unfocused', {});
    } else {
        chrome.windows.get(windowId, (window) => {
            sendEvent('window_focused', {
                windowId: window.id,
                incognito: window.incognito
            });
        });
    }
});

// --- Idle Tracking ---
chrome.idle.setDetectionInterval(60); // 1 minute
chrome.idle.onStateChanged.addListener((newState) => {
    sendEvent('idle_state_changed', { state: newState });
});

// --- Download Tracking ---
chrome.downloads.onCreated.addListener((downloadItem) => {
    sendEvent('download_started', {
        id: downloadItem.id,
        url: downloadItem.url,
        filename: downloadItem.filename,
        totalBytes: downloadItem.totalBytes,
        incognito: downloadItem.incognito
    });
});

chrome.downloads.onChanged.addListener((delta) => {
    if (delta.state && delta.state.current === 'complete') {
        sendEvent('download_completed', { id: delta.id });
    }
});

// --- Bookmark Tracking ---
chrome.bookmarks.onCreated.addListener((id, bookmark) => {
    sendEvent('bookmark_created', {
        id: id,
        title: bookmark.title,
        url: bookmark.url,
        parentId: bookmark.parentId
    });
});

chrome.bookmarks.onRemoved.addListener((id, removeInfo) => {
    sendEvent('bookmark_removed', {
        id: id,
        title: removeInfo.node.title,
        url: removeInfo.node.url
    });
});

// --- History Tracking ---
chrome.history.onVisited.addListener((historyItem) => {
    sendEvent('history_visited', {
        id: historyItem.id,
        url: historyItem.url,
        title: historyItem.title,
        visitCount: historyItem.visitCount,
        typedCount: historyItem.typedCount
    });
});
