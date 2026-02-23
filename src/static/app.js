const wsStatusEl = document.getElementById('ws-status');
const targetListEl = document.getElementById('target-list');
const blipsContainer = document.getElementById('blips-container');

// Coordinate conversion: From GökKalkan (-max_range to max_range) to CSS (0% to 100%)
// Assuming a default max range of 200km. If changed in config, we can adjust here.
const MAX_RANGE = 200.0;

let socket;

function connectWebSocket() {
    socket = new WebSocket("ws://localhost:8000/ws/radar");

    socket.onopen = function(e) {
        wsStatusEl.textContent = "CONNECTED - SECURE";
        wsStatusEl.style.color = "#08ff08";
    };

    socket.onmessage = function(event) {
        const targetData = JSON.parse(event.data);
        updateDashboard(targetData);
    };

    socket.onclose = function(event) {
        wsStatusEl.textContent = "DISCONNECTED - RECONNECTING...";
        wsStatusEl.style.color = "red";
        setTimeout(connectWebSocket, 2000);
    };

    socket.onerror = function(error) {
        console.error("WebSocket Error:", error);
    };
}

function updateDashboard(targets) {
    // 1. Update the sidebar list
    targetListEl.innerHTML = "";
    // 2. Clear old blips
    blipsContainer.innerHTML = "";

    targets.forEach(t => {
        // Create sidebar card
        const card = document.createElement("div");
        card.className = `target-card ${t.oncelik === "KRİTİK" ? "kritik" : ""}`;
        card.innerHTML = `
            <div><strong class="id-badge">ID: ${t.id}</strong> [${t.tip}]</div>
            <div>RNG: ${parseFloat(t.mesafe).toFixed(1)} km | ALT: ${parseFloat(t.irtifa).toFixed(1)} km</div>
            <div>SPD: ${parseFloat(t.hiz).toFixed(1)} km/h | TTI: ${t.tti !== null ? parseFloat(t.tti).toFixed(1) : "N/A"}s</div>
            <div>PRIO: ${t.oncelik} | ACT: ${t.karar}</div>
        `;
        targetListEl.appendChild(card);

        // Convert coordinates for the radar circle
        // Radar center is at 50%, 50%
        // x goes right, y goes up (but in DOM y goes down, so we subtract)
        const percentX = 50 + (t.x / MAX_RANGE) * 50;
        const percentY = 50 - (t.y / MAX_RANGE) * 50;

        // Draw blip on radar
        const blip = document.createElement("div");
        blip.className = `blip ${t.oncelik === "KRİTİK" ? "kritik" : ""}`;
        blip.style.left = `${percentX}%`;
        blip.style.top = `${percentY}%`;

        // Add label to blip
        const label = document.createElement("div");
        label.className = "blip-label";
        label.textContent = `${t.id} (${parseFloat(t.irtifa).toFixed(0)}m)`;
        blip.appendChild(label);

        blipsContainer.appendChild(blip);
    });
}

// Start connection when page loads
window.onload = connectWebSocket;
