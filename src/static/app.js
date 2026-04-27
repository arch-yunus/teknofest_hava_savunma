const wsStatusEl = document.getElementById('ws-status');
const targetListEl = document.getElementById('target-list');
const tooltipsContainer = document.getElementById('tooltips-container');

let MAX_RANGE = 200.0;
let COMP_MODE = false;
let chartTime = 0;

// --- Three.js Advanced Setup ---
const canvasContainer = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x060608, 0.002);

// Camera
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 5000);
camera.position.set(200, 250, 400);

// Renderer with Bloom-friendly settings
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ReinhardToneMapping;
canvasContainer.appendChild(renderer.domElement);

// Controls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxPolarAngle = Math.PI / 2 - 0.05;

// --- Digital Holographic World ---
const terrainSize = 1000;
const terrainSegments = 50;
const terrainGeo = new THREE.PlaneGeometry(terrainSize, terrainSize, terrainSegments, terrainSegments);

// Procedural Terrain Noise (Holographic Mountains)
const posAttr = terrainGeo.attributes.position;
for (let i = 0; i < posAttr.count; i++) {
    const x = posAttr.getX(i);
    const y = posAttr.getY(i);
    const dist = Math.sqrt(x*x + y*y);
    const z = (Math.sin(x/50) * Math.cos(y/50) * 15) + (dist > 300 ? (dist-300)/2 : 0);
    posAttr.setZ(i, z);
}
terrainGeo.computeVertexNormals();

const terrainMat = new THREE.MeshBasicMaterial({ 
    color: 0x00f3ff, 
    wireframe: true, 
    transparent: true, 
    opacity: 0.05 
});
const terrainMesh = new THREE.Mesh(terrainGeo, terrainMat);
terrainMesh.rotation.x = -Math.PI / 2;
terrainMesh.position.y = -10;
scene.add(terrainMesh);

// Grid Helper (Subtle secondary grid)
const gridHelper = new THREE.GridHelper(1000, 50, 0x00f3ff, 0x002233);
gridHelper.position.y = -0.5;
gridHelper.material.transparent = true;
gridHelper.material.opacity = 0.1;
scene.add(gridHelper);

// --- Radar Pulse Effect ---
const pulseGeo = new THREE.RingGeometry(0, 5, 64);
const pulseMat = new THREE.MeshBasicMaterial({ 
    color: 0x00f3ff, 
    transparent: true, 
    opacity: 0.5, 
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending
});
const pulseMesh = new THREE.Mesh(pulseGeo, pulseMat);
pulseMesh.rotation.x = -Math.PI / 2;
scene.add(pulseMesh);

// Compass Circles
const createCircle = (radius, color, opacity) => {
    const geo = new THREE.RingGeometry(radius - 0.5, radius + 0.5, 128);
    const mat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: opacity, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = -Math.PI / 2;
    return mesh;
};

const circles = [100, 200, 300, 400];
circles.forEach(r => scene.add(createCircle(r, 0x00f3ff, 0.1)));

// --- Center Hologram ---
const baseGeo = new THREE.CylinderGeometry(5, 8, 2, 6, 1, true);
const baseMat = new THREE.MeshBasicMaterial({ color: 0x00ffaa, wireframe: true, transparent: true, opacity: 0.5 });
const baseStation = new THREE.Mesh(baseGeo, baseMat);
scene.add(baseStation);

// Volumetric Scanner
const scanGeo = new THREE.CylinderGeometry(0, 400, 400, 32, 1, true, 0, Math.PI / 6);
const scanMat = new THREE.MeshBasicMaterial({
    color: 0x00f3ff,
    transparent: true,
    opacity: 0.1,
    side: THREE.DoubleSide,
    depthWrite: false,
    blending: THREE.AdditiveBlending
});
const scanMesh = new THREE.Mesh(scanGeo, scanMat);
scanMesh.rotation.x = Math.PI / 2;
scanMesh.position.y = 200;
const scanGroup = new THREE.Group();
scanGroup.add(scanMesh);
scene.add(scanGroup);

// --- Lighting ---
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0x00f3ff, 1, 500);
pointLight.position.set(0, 100, 0);
scene.add(pointLight);

// --- Dictionaries ---
const targetMeshes = {};
const targetTooltips = {};
const interceptorMeshes = {};
const explosions = [];

const normalMat = new THREE.MeshPhongMaterial({ color: 0xffbb00, shininess: 80, emissive: 0x221100 });
const kritikMat = new THREE.MeshPhongMaterial({ color: 0xff3131, shininess: 80, emissive: 0x330000 });
const friendMat = new THREE.MeshPhongMaterial({ color: 0x00ffaa, shininess: 80, emissive: 0x002200 });

const uavGeo = new THREE.TetrahedronGeometry(3);
const missileGeo = new THREE.ConeGeometry(1.5, 6, 4);

// --- UI Logic Synchronization ---
function updateMetrics(data) {
    if (data.ammo !== undefined) {
        document.getElementById('battery-bar').style.width = `${data.ammo}%`;
        document.getElementById('battery-percent').textContent = `${data.ammo}%`;
        if (data.ammo < 30) document.getElementById('battery-bar').className = "bar red";
    }
    
    // Simulated CPU load for visual "show"
    const cpuLoad = 10 + Math.random() * 15;
    document.getElementById('cpu-bar').style.width = `${cpuLoad}%`;
    document.getElementById('cpu-percent').textContent = `${Math.floor(cpuLoad)}%`;
}

// --- WebSocket ---
let socket;
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    socket = new WebSocket(`${protocol}//${host}/ws/radar`);

    socket.onopen = () => {
        wsStatusEl.textContent = "BAĞLANTI AKTİF";
        wsStatusEl.className = "status-online";
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        updateMetrics(data);
        
        if (data.auto_fire !== undefined) {
            const hudMode = document.getElementById('hud-mode');
            if (hudMode) {
                hudMode.textContent = data.auto_fire ? "OTONOM" : "MANUEL";
                hudMode.classList.toggle('gold-text', !data.auto_fire);
            }
            const btn = document.getElementById('btn-toggle-auto');
            btn.textContent = `OTONOM MOD: ${data.auto_fire ? 'AÇIK' : 'KAPALI'}`;
            btn.classList.toggle('active', data.auto_fire);
        }

        if (data.stage) {
            document.getElementById('hud-stage').textContent = `FAZ-${data.stage}`;
            document.getElementById('comp-hud').classList.remove('hidden');
        }

        updateRadar(data.targets || [], data.interceptors || [], data.lasers || []);
        updateTargetList(data.targets || []);

        if (data.score) {
            document.getElementById('hud-score').textContent = data.score.total_score;
        }

        if (data.stage !== undefined) {
            const stages = {
                0: "BEKLEMEDE",
                1: "AŞAMA 1: DURAN HEDEF",
                2: "AŞAMA 2: SÜRÜ SALDIRISI",
                3: "AŞAMA 3: KATMANLI SAVUNMA"
            };
            document.getElementById('hud-stage').textContent = stages[data.stage] || "BİLİNMİYOR";
        }

        if (data.strategic) {
            document.getElementById('hud-directive').textContent = data.strategic.directive || "ANALİZ...";
            const netStatus = data.strategic.network ? 
                Object.values(data.strategic.network).every(v => v === "CONNECTED" || v === "SYNCHRONIZED") ? "AKTİF" : "SINIRLI" 
                : "BAĞLANTI YOK";
            document.getElementById('hud-network').textContent = `AĞ: GÖK-VATAN (${netStatus})`;
        }
    };

    socket.onclose = () => {
        wsStatusEl.textContent = "BAĞLANTI KESİLDİ - YENİLENİYOR...";
        wsStatusEl.className = "status-offline";
        setTimeout(connectWebSocket, 2000);
    };
}

function updateRadar(targets, interceptors, lasers) {
    const activeTargetIds = new Set();
    const activeIntIds = new Set();

    targets.forEach(t => {
        activeTargetIds.add(t.id);
        const posX = t.x;
        const posY = Math.max(t.irtifa * 10, 2);
        const posZ = -t.y;

        let mat = t.oncelik === "KRİTİK" ? kritikMat : (t.is_dost ? friendMat : normalMat);
        let geo = t.tip === "FÜZE" || t.tip === "BALİSTİK" ? missileGeo : uavGeo;
        
        if (targetMeshes[t.id]) {
            targetMeshes[t.id].position.set(posX, posY, posZ);
            targetMeshes[t.id].material = mat;
        } else {
            const mesh = new THREE.Mesh(geo, mat);
            mesh.position.set(posX, posY, posZ);
            scene.add(mesh);
            targetMeshes[t.id] = mesh;

            const tooltip = document.createElement('div');
            tooltip.className = "tooltip";
            tooltipsContainer.appendChild(tooltip);
            targetTooltips[t.id] = tooltip;
        }
        
        // Advanced Data Tag
        const distKm = t.mesafe.toFixed(2);
        const altM = (t.irtifa * 1000).toFixed(0);
        const speedKmh = (Math.random() * 200 + 400).toFixed(0);

        targetTooltips[t.id].innerHTML = `
            <div class="tag-id">${t.id}</div>
            <div class="tag-data">
                <span>RNG: ${distKm}km</span>
                <span>ALT: ${altM}m</span>
                <span>SPD: ${speedKmh}kph</span>
            </div>
            <div class="tag-footer">${t.tip}</div>
        `;
        targetTooltips[t.id].setAttribute('data-priority', t.oncelik);
    });

    // Cleanup disappeared targets
    for (const id in targetMeshes) {
        if (!activeTargetIds.has(id)) {
            createExplosion(targetMeshes[id].position.x, targetMeshes[id].position.y, targetMeshes[id].position.z);
            scene.remove(targetMeshes[id]);
            delete targetMeshes[id];
            targetTooltips[id].remove();
            delete targetTooltips[id];
        }
    }

    // Interceptors (Simplified logic for now)
    interceptors.forEach(int => {
        activeIntIds.add(int.id);
        if (!interceptorMeshes[int.id]) {
            const intMesh = new THREE.Mesh(
                new THREE.ConeGeometry(1, 4, 8),
                new THREE.MeshBasicMaterial({ color: 0xffffff })
            );
            scene.add(intMesh);
            interceptorMeshes[int.id] = intMesh;
        }
        interceptorMeshes[int.id].position.set(int.x, 5, -int.y);
    });

    for (const id in interceptorMeshes) {
        if (!activeIntIds.has(id)) {
            scene.remove(interceptorMeshes[id]);
            delete interceptorMeshes[id];
        }
    }
}

function updateTargetList(targets) {
    targetListEl.innerHTML = "";
    const selector = document.getElementById('target-selector');
    const currentSelected = selector.value;
    selector.innerHTML = '<option value="">-- HEDEF KİLİTLE --</option>';

    targets.forEach(t => {
        // Update Sidebar List
        const card = document.createElement('div');
        card.className = `target-card ${t.oncelik === "KRİTİK" ? 'kritik' : ''}`;
        card.innerHTML = `
            <div class="card-row">
                <span class="id-badge">${t.id}</span>
                <span class="status-indicator active">TAKİPTE</span>
            </div>
            <div class="card-main">
                <div class="data-group">
                    <label>MESAFE</label>
                    <value>${(t.mesafe).toFixed(2)}km</value>
                </div>
                <div class="data-group">
                    <label>İRTİFA</label>
                    <value>${(t.irtifa * 1000).toFixed(0)}m</value>
                </div>
            </div>
            <div class="card-footer">
                <span>TİP: ${t.tip}</span>
                <span>KARAR: ${t.karar || "ANALİZ"}</span>
            </div>
        `;
        targetListEl.appendChild(card);

        // Update Target Selector Dropdown
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = `HEDEF ${t.id} (${t.tip})`;
        if (t.id === currentSelected) opt.selected = true;
        selector.appendChild(opt);
    });
}

// --- Explosions ---
function createExplosion(x, y, z) {
    const geo = new THREE.SphereGeometry(1, 8, 8);
    const mat = new THREE.MeshBasicMaterial({ color: 0xff4400, transparent: true, opacity: 0.8 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(x, y, z);
    scene.add(mesh);
    explosions.push({ mesh, age: 0 });
}

// --- Animation Loop ---
function animate() {
    requestAnimationFrame(animate);
    
    // Radar Pulse Animation
    pulseMesh.scale.addScalar(0.08);
    pulseMesh.material.opacity -= 0.01;
    if (pulseMesh.material.opacity <= 0) {
        pulseMesh.scale.set(1, 1, 1);
        pulseMesh.material.opacity = 0.5;
    }

    scanGroup.rotation.y -= 0.03;
    controls.update();

    // Tooltip & Reticle Projection
    for (const id in targetMeshes) {
        const mesh = targetMeshes[id];
        const pos = mesh.position.clone().project(camera);
        const x = (pos.x * 0.5 + 0.5) * window.innerWidth;
        const y = (pos.y * -0.5 + 0.5) * window.innerHeight;
        
        const tooltip = targetTooltips[id];
        tooltip.style.left = `${x}px`;
        tooltip.style.top = `${y}px`;
        tooltip.style.display = pos.z > 1 ? 'none' : 'block';

        // Rotate target meshes for dynamic feel
        mesh.rotation.y += 0.05;
        mesh.rotation.x += 0.02;

        // Camera Follow Logic
        if (currentCameraMode === 'FOLLOW' && id === followedTargetId) {
            const targetPos = mesh.position;
            const offset = new THREE.Vector3(50, 40, 50);
            camera.position.lerp(targetPos.clone().add(offset), 0.1);
            controls.target.lerp(targetPos, 0.1);
        }
    }

    // Reset follow if target lost
    if (currentCameraMode === 'FOLLOW' && followedTargetId && !targetMeshes[followedTargetId]) {
        followedTargetId = null;
        setCameraMode('TACTICAL');
    }

    // Explosion Animation
    for (let i = explosions.length - 1; i >= 0; i--) {
        const exp = explosions[i];
        exp.age++;
        exp.mesh.scale.multiplyScalar(1.1);
        exp.mesh.material.opacity -= 0.02;
        if (exp.age > 40) {
            scene.remove(exp.mesh);
            explosions.splice(i, 1);
        }
    }

    renderer.render(scene, camera);
}

// --- Handlers ---
document.getElementById('btn-toggle-auto').addEventListener('click', () => sendCommand('toggle_auto_fire'));
document.getElementById('btn-toggle-emission').addEventListener('click', () => sendCommand('toggle_radar_emission'));

function sendCommand(action, data = {}) {
    fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...data })
    });
}

// Window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Boot Sequence
function startBootSequence() {
    const bootOverlay = document.getElementById('boot-overlay');
    if (!bootOverlay) return;
    setTimeout(() => {
        bootOverlay.style.opacity = '0';
        setTimeout(() => bootOverlay.style.display = 'none', 500);
    }, 1000);
}

connectWebSocket();
animate();
startBootSequence();

// --- Camera Controls ---
let currentCameraMode = 'TACTICAL';
let followedTargetId = null;

function setCameraMode(mode) {
    currentCameraMode = mode;
    document.querySelectorAll('.camera-modes .btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`btn-cam-${mode.toLowerCase()}`).classList.add('active');

    switch(mode) {
        case 'TACTICAL':
            camera.position.set(200, 250, 400);
            controls.target.set(0, 0, 0);
            break;
        case 'TOP':
            camera.position.set(0, 600, 1);
            controls.target.set(0, 0, 0);
            break;
        case 'BASE':
            camera.position.set(20, 15, 60);
            controls.target.set(0, 50, -100);
            break;
        case 'FOLLOW':
            // Logic handled in animate loop
            break;
    }
}

document.getElementById('btn-cam-tactical').addEventListener('click', () => setCameraMode('TACTICAL'));
document.getElementById('btn-cam-top').addEventListener('click', () => setCameraMode('TOP'));
document.getElementById('btn-cam-base').addEventListener('click', () => setCameraMode('BASE'));
document.getElementById('btn-cam-follow').addEventListener('click', () => {
    setCameraMode('FOLLOW');
    const ids = Object.keys(targetMeshes);
    if (ids.length > 0) followedTargetId = ids[0];
});

// Add missing event listeners from HTML
const stages = [1, 2, 3];
stages.forEach(s => {
    document.getElementById(`btn-stage-${s}`).addEventListener('click', () => sendCommand(`set_stage_${s}`));
});
document.getElementById('btn-force-swarm').addEventListener('click', () => sendCommand('force_swarm'));
document.getElementById('btn-force-hypersonic').addEventListener('click', () => sendCommand('force_hypersonic'));
document.getElementById('btn-trigger-emp').addEventListener('click', () => sendCommand('trigger_emp'));
document.getElementById('btn-estop').addEventListener('click', () => sendCommand('trigger_estop'));
document.getElementById('btn-manual-fire').addEventListener('click', () => {
    const targetId = document.getElementById('target-selector').value;
    sendCommand('manual_fire', { target_id: targetId });
});
document.getElementById('btn-start-mission').addEventListener('click', () => {
    const missionId = document.getElementById('mission-selector').value;
    if (missionId) sendCommand('start_mission', { mission_id: missionId });
});
