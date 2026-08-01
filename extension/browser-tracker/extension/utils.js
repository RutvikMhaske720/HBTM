const API_URL = 'http://localhost:8000/api/events';

/**
 * Sends a tracking event to the backend server.
 * @param {string} type - The category/type of the event (e.g., 'tab_created', 'mouse_click').
 * @param {object} data - The payload containing event details.
 */
async function sendEvent(type, data) {
    // Check if tracking is enabled
    const storage = await chrome.storage.local.get(['trackingEnabled']);
    if (storage.trackingEnabled === false) {
        return;
    }

    try {
        const payload = {
            type: type,
            timestamp: new Date().toISOString(),
            data: data
        };

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            console.error(`Failed to send event ${type}: ${response.statusText}`);
        }
    } catch (error) {
        console.error(`Error sending event ${type}:`, error);
    }
}
