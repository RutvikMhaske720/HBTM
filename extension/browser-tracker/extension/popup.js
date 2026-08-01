document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-btn');
    const statusText = document.getElementById('status-text');
    const indicator = document.getElementById('indicator');
    const serverStatus = document.getElementById('server-status');

    // Load initial state
    chrome.storage.local.get(['trackingEnabled'], (result) => {
        const isEnabled = result.trackingEnabled !== false; // Default true
        updateUI(isEnabled);
    });

    // Toggle logic
    toggleBtn.addEventListener('click', () => {
        chrome.storage.local.get(['trackingEnabled'], (result) => {
            const isEnabled = result.trackingEnabled !== false;
            const newState = !isEnabled;
            
            chrome.storage.local.set({ trackingEnabled: newState }, () => {
                updateUI(newState);
            });
        });
    });

    function updateUI(isEnabled) {
        if (isEnabled) {
            statusText.textContent = 'Tracking Active';
            indicator.style.backgroundColor = '#4caf50';
            toggleBtn.textContent = 'Stop Tracking';
            toggleBtn.classList.remove('inactive-btn');
            toggleBtn.classList.add('active-btn');
        } else {
            statusText.textContent = 'Tracking Paused';
            indicator.style.backgroundColor = '#f44336';
            toggleBtn.textContent = 'Start Tracking';
            toggleBtn.classList.remove('active-btn');
            toggleBtn.classList.add('inactive-btn');
        }
    }

    // Check server status
    fetch('http://localhost:8000/api/status')
        .then(response => {
            if (response.ok) {
                serverStatus.textContent = 'Online';
                serverStatus.style.color = '#4caf50';
            } else {
                throw new Error('Not ok');
            }
        })
        .catch(() => {
            serverStatus.textContent = 'Offline';
            serverStatus.style.color = '#f44336';
        });
});
