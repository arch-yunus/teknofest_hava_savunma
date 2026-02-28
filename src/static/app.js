const wsStatusEl = document.getElementById('ws-status');
const targetListEl = document.getElementById('target-list');
const tooltipsContainer = document.getElementById('tooltips-container');

const MAX_RANGE = 200.0; // Same as Python simulation

// --- Three.js Setup ---
const canvasContainer = document.getElementById('canvas-container');
const scene = new THREE.Scene();

// Camera
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 150, 200); // Look from an angle

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
canvasContainer.appendChild(renderer.domElement);

// Controls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxPolarAngle = Math.PI / 2 - 0.05; // Don't allow going below ground

// --- Radar Environment ---
// Grid Helper
const gridHelper = new THREE.GridHelper(MAX_RANGE * 2, 40, 0x00ff00, 0x004400);
gridHelper.position.y = 0;
// Make the grid transparent
gridHelper.material.opacity = 0.3;
gridHelper.material.transparent = true;
scene.add(gridHelper);

// Sector Circles (Range Rings)
const circleMaterial = new THREE.LineBasicMaterial({ color: 0x0cf50c, transparent: true, opacity: 0.2 });
for (let i = 1; i <= 4; i++) {
    const radius = Math.floor(MAX_RANGE / 4) * i;
    const geometry = new THREE.CircleGeometry(radius, 64);
    geometry.vertices.shift(); // Remove center vertex
    const circle = new THREE.LineLoop(geometry, circleMaterial);
    circle.rotation.x = -Math.PI / 2;
    scene.add(circle);
}

// Center Base Station
const baseGeo = new THREE.CylinderGeometry(5, 5, 2, 16);
const baseMat = new THREE.MeshBasicMaterial({ color: 0x0cf50c, wireframe: true });
const baseStation = new THREE.Mesh(baseGeo, baseMat);
scene.add(baseStation);

// Radar Scan Cone
const scanGeo = new THREE.CylinderGeometry(0, MAX_RANGE, MAX_RANGE, 32, 1, true, 0, Math.PI / 4);
// Custom material for scanning effect
const scanMat = new THREE.MeshBasicMaterial({
    color: 0x0cf50c,
    transparent: true,
    opacity: 0.1,
    side: THREE.DoubleSide,
    depthWrite: false
});
const scanMesh = new THREE.Mesh(scanGeo, scanMat);
// Rotate cone to lie on its side
scanMesh.rotation.x = Math.PI / 2;
scanMesh.position.y = MAX_RANGE / 2;
const scanGroup = new THREE.Group();
scanGroup.add(scanMesh);
scene.add(scanGroup);


// --- Lighting ---
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

// --- Dictionary to store target meshes and UI tooltips ---
const targetMeshes = {};
const targetTooltips = {};

// --- Materials ---
const normalMat = new THREE.MeshBasicMaterial({ color: 0xffff00 }); // Yellow
const kritikMat = new THREE.MeshBasicMaterial({ color: 0xff3333 }); // Red

// Sphere Geometry for targets
const targetGeo = new THREE.SphereGeometry(3, 16, 16);


// --- Window Resize ---
window.addEventListener('resize', onWindowResize, false);
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

// --- Animation Loop ---
function animate() {
    requestAnimationFrame(animate);

    // Rotate scanner
    scanGroup.rotation.y -= 0.05;

    controls.update();

    // Update tooltip positions (project 3D to 2D screen space)
    for (const [id, mesh] of Object.entries(targetMeshes)) {
        const tooltip = targetTooltips[id];
        if (tooltip) {
            // Get screen coordinates
            const pos = mesh.position.clone();
            pos.project(camera);

            // Convert to CSS coordinates
            const x = (pos.x * .5 + .5) * window.innerWidth;
            const y = (pos.y * -.5 + .5) * window.innerHeight;

            tooltip.style.left = `${x}px`;
            tooltip.style.top = `${y}px`;

            // Hide if behind camera
            if (pos.z > 1) {
                tooltip.style.display = 'none';
            } else {
                tooltip.style.display = 'block';
            }
        }
    }

    renderer.render(scene, camera);
}
animate();


// --- WebSocket Logic ---
let socket;

function connectWebSocket() {
    socket = new WebSocket("ws://localhost:8000/ws/radar");

    socket.onopen = function (e) {
        wsStatusEl.textContent = "CONNECTED - SECURE";
        wsStatusEl.style.color = "#0cf50c";
    };

    socket.onmessage = function (event) {
        const targetData = JSON.parse(event.data);
        updateDashboard(targetData);
    };

    socket.onclose = function (event) {
        wsStatusEl.textContent = "DISCONNECTED - RECONNECTING...";
        wsStatusEl.style.color = "red";
        setTimeout(connectWebSocket, 2000);
    };
}

function updateDashboard(targets) {
    // 1. Update Sidebar
    targetListEl.innerHTML = "";

    // Keep track of active IDs to remove dead ones
    const activeIds = new Set();

    targets.forEach(t => {
        activeIds.add(t.id);

        // --- UI Sidebar Card ---
        const isKritik = t.oncelik === "KRİTİK";
        const card = document.createElement("div");
        card.className = `target-card ${isKritik ? "kritik" : ""}`;
        card.innerHTML = `
            <div><strong class="id-badge">ID: ${t.id}</strong> [${t.tip}]</div>
            <div>RNG: ${parseFloat(t.mesafe).toFixed(1)} km | ALT: ${(parseFloat(t.irtifa) * 1000).toFixed(0)} m</div>
            <div>SPD: ${parseFloat(t.hiz).toFixed(0)} km/h | TTI: ${t.tti !== null ? parseFloat(t.tti).toFixed(1) : "N/A"}s</div>
            <div>PRIO: ${t.oncelik} | ACT: ${t.karar}</div>
        `;
        targetListEl.appendChild(card);

        // --- 3D Mesh Update ---
        // Coordinates in simulation mapped directly to Three.js coordinates
        // Assuming simulation origin is (0,0,0) center of radar
        // Y in sim is North (Z in Threejs, negative into screen), Z in sim is Altitude (Y in Three.js)
        const posX = t.x;
        const posY = Math.max(t.irtifa * 10, 0); // Scale altitude slightly for visibility
        const posZ = -t.y;

        if (targetMeshes[t.id]) {
            // Update existing
            targetMeshes[t.id].position.set(posX, posY, posZ);
            targetMeshes[t.id].material = isKritik ? kritikMat : normalMat;

            // Update Tooltip Text
            targetTooltips[t.id].className = `tooltip ${isKritik ? "kritik" : ""}`;
            targetTooltips[t.id].textContent = `${t.id} [${(t.irtifa * 1000).toFixed(0)}m]`;
        } else {
            // Create new
            const mesh = new THREE.Mesh(targetGeo, isKritik ? kritikMat : normalMat);
            mesh.position.set(posX, posY, posZ);
            scene.add(mesh);
            targetMeshes[t.id] = mesh;

            // Create Tooltip
            const tooltip = document.createElement('div');
            tooltip.className = `tooltip ${isKritik ? "kritik" : ""}`;
            tooltip.textContent = `${t.id} [${(t.irtifa * 1000).toFixed(0)}m]`;
            tooltipsContainer.appendChild(tooltip);
            targetTooltips[t.id] = tooltip;
        }
    });

    // Cleanup dead targets
    for (const id in targetMeshes) {
        if (!activeIds.has(id)) {
            scene.remove(targetMeshes[id]);
            delete targetMeshes[id];

            // Remove tooltip
            if (targetTooltips[id]) {
                targetTooltips[id].remove();
                delete targetTooltips[id];
            }
        }
    }
}

// Start connection when page loads
window.onload = connectWebSocket;
