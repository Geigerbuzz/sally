// WebSocket Client for Real-Time Updates

const socketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const socketUrl = `${socketProtocol}//${window.location.hostname}:8000/ws/client-${Math.floor(Math.random() * 1000)}`;

let socket;

function connectWebSocket() {
    console.log("Connecting to WebSocket...");
    socket = new WebSocket(socketUrl);

    socket.onopen = () => {
        console.log("WebSocket Connected");
    };

    socket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleServerMessage(message);
        } catch (e) {
            console.error("Failed to parse WebSocket message:", e);
        }
    };

    socket.onclose = () => {
        console.log("WebSocket Disconnected. Reconnecting in 3s...");
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (error) => {
        console.error("WebSocket Error:", error);
        socket.close();
    };
}

function handleServerMessage(message) {
    if (message.type === 'widget_update') {
        updateWidgetUI(message);
    }
}

function updateWidgetUI(message) {
    const { widget_id, data } = message;

    // Example: Update "Listings" Widget
    if (widget_id === 'w-listings' && data.action === 'add') {
        const numEl = document.querySelector('#w-listings .live-num');
        if (numEl) {
            let current = parseInt(numEl.innerText);
            numEl.innerText = current + data.change;
            console.log(`Updated Listings: +${data.change}`);

            // Visual Flash
            numEl.style.color = '#32d74b';
            setTimeout(() => numEl.style.color = '', 500);
        }
    }

    // Example: Update "Revenue" Widget
    if (widget_id === 'w-revenue' && data.revenue_add) {
        const numEl = document.querySelector('#w-revenue .live-num');
        if (numEl) {
            // Very simple parsing for "$4.2M" format mock
            // In real app, store raw value in data attribute
            console.log(`Revenue Bump: $${data.revenue_add}`);

            // Just flash for now as the format is string-heavy
            numEl.style.color = '#32d74b';
            setTimeout(() => numEl.style.color = '', 500);
        }
    }
}

// Start connection on load
document.addEventListener('DOMContentLoaded', connectWebSocket);
