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

// --- Cyberpunk 3D Terrain (Holo-Map) ---
const mapSize = 400;
const segments = 60;
const terrainGeo = new THREE.PlaneGeometry(mapSize, mapSize, segments, segments);

// Add some random noise to vertices to simulate mountains/valleys
const vertices = terrainGeo.attributes.position.array;
for (let i = 0; i < vertices.length; i += 3) {
    // Modify Z value (which will be Y after rotation)
    // Create a slight valley in the center, mountains on the edges
    const x = vertices[i];
    const y = vertices[i + 1];
    const distFromCenter = Math.sqrt(x * x + y * y);
    const noise = Math.random() * 2;
    // Taller mountains further from center
    vertices[i + 2] = (distFromCenter / 15) + noise - 5;
}
terrainGeo.computeVertexNormals();

const terrainMat = new THREE.MeshBasicMaterial({
    color: 0x004400, // Koyu yeşil
    wireframe: true,
    transparent: true,
    opacity: 0.3
});
const terrainMesh = new THREE.Mesh(terrainGeo, terrainMat);
terrainMesh.rotation.x = -Math.PI / 2;
terrainMesh.position.y = -1; // Ana gridin biraz altında
scene.add(terrainMesh);

// --- Radar Environment ---
const gridHelper = new THREE.GridHelper(MAX_RANGE * 2, 40, 0x00ff00, 0x004400);
gridHelper.position.y = 0;
gridHelper.material.opacity = 0.3;
gridHelper.material.transparent = true;
scene.add(gridHelper);

const circleMaterial = new THREE.LineBasicMaterial({ color: 0x0cf50c, transparent: true, opacity: 0.2 });
for (let i = 1; i <= 4; i++) {
    const radius = Math.floor(MAX_RANGE / 4) * i;
    const geometry = new THREE.CircleGeometry(radius, 64);
    geometry.vertices.shift();
    const circle = new THREE.LineLoop(geometry, circleMaterial);
    circle.rotation.x = -Math.PI / 2;
    scene.add(circle);
}

const baseGeo = new THREE.CylinderGeometry(5, 5, 2, 16);
const baseMat = new THREE.MeshBasicMaterial({ color: 0x0cf50c, wireframe: true });
const baseStation = new THREE.Mesh(baseGeo, baseMat);
scene.add(baseStation);

const scanGeo = new THREE.CylinderGeometry(0, MAX_RANGE, MAX_RANGE, 32, 1, true, 0, Math.PI / 4);
const scanMat = new THREE.MeshBasicMaterial({
    color: 0x0cf50c, transparent: true, opacity: 0.1,
    side: THREE.DoubleSide, depthWrite: false
});
const scanMesh = new THREE.Mesh(scanGeo, scanMat);
scanMesh.rotation.x = Math.PI / 2;
scanMesh.position.y = MAX_RANGE / 2;
const scanGroup = new THREE.Group();
scanGroup.add(scanMesh);
scene.add(scanGroup);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

// --- Dictionaries ---
const targetMeshes = {};
const targetTooltips = {};
const interceptorMeshes = {};
const explosions = []; // For particle effects

// --- Materials & Geometries ---
const normalMat = new THREE.MeshBasicMaterial({ color: 0xffff00 }); // Yellow
const kritikMat = new THREE.MeshBasicMaterial({ color: 0xff3333 }); // Red
const targetGeo = new THREE.SphereGeometry(3, 16, 16);

// Missile geometry (Neon Blue)
const missileGeo = new THREE.ConeGeometry(1.5, 6, 8);
missileGeo.rotateX(Math.PI / 2); // Point forward along Z
const missileMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); // Cyan


// --- Window Resize ---
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// --- Particle Explosion System ---
function createExplosion(x, y, z) {
    const particleCount = 200; // Artırılmış partikül sayısı (Splash Damage hissi)
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    const velArray = [];

    for (let i = 0; i < particleCount; i++) {
        posArray[i * 3] = x;
        posArray[i * 3 + 1] = y;
        posArray[i * 3 + 2] = z;
        velArray.push({
            x: (Math.random() - 0.5) * 15,
            y: (Math.random() - 0.5) * 15,
            z: (Math.random() - 0.5) * 15
        });
    }
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    const particleMat = new THREE.PointsMaterial({
        size: 3,
        color: 0xff4400, // Daha yoğun turuncu/kırmızı
        transparent: true,
        opacity: 1,
        blending: THREE.AdditiveBlending // Daha parlak patlama efekti
    });

    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);

    // Splash Damage Şok Dalgası (Genişleyen Küre)
    const waveGeo = new THREE.SphereGeometry(1, 32, 32);
    const waveMat = new THREE.MeshBasicMaterial({
        color: 0xffaa00,
        transparent: true,
        opacity: 0.5,
        wireframe: true
    });
    const waveMesh = new THREE.Mesh(waveGeo, waveMat);
    waveMesh.position.set(x, y, z);
    scene.add(waveMesh);

    explosions.push({ system: particleSystem, wave: waveMesh, velocities: velArray, age: 0 });
}

// --- Laser Weapon System (CIWS) ---
const activeLasers = [];
function createLaserBeam(startX, startY, startZ, endX, endY, endZ) {
    const material = new THREE.LineBasicMaterial({
        color: 0x33ff33, // Neon green
        linewidth: 4,
        transparent: true,
        opacity: 1
    });

    const points = [];
    points.push(new THREE.Vector3(startX, startY, startZ));
    points.push(new THREE.Vector3(endX, endY, endZ));

    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const line = new THREE.Line(geometry, material);
    scene.add(line);
    activeLasers.push({ line: line, age: 0 });
}

// --- Telemetry Chart.js ---
const ctx = document.getElementById('telemetryChart').getContext('2d');
const telemetryChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Tehdit Yoğunluğu',
            data: [],
            borderColor: '#0cf50c',
            backgroundColor: 'rgba(12, 245, 12, 0.2)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 }, // Disable animation for performance
        scales: {
            x: { display: false },
            y: {
                display: true,
                beginAtZero: true,
                grid: { color: 'rgba(12, 245, 12, 0.1)' },
                ticks: { color: '#0cf50c' }
            }
        },
        plugins: {
            legend: {
                labels: { color: '#0cf50c', font: { family: "'Share Tech Mono', monospace" } }
            }
        }
    }
});
let chartTime = 0;

// --- Animation Loop ---
function animate() {
    requestAnimationFrame(animate);
    scanGroup.rotation.y -= 0.05;
    controls.update();

    // Update Tooltips
    for (const [id, mesh] of Object.entries(targetMeshes)) {
        const tooltip = targetTooltips[id];
        if (tooltip) {
            const pos = mesh.position.clone();
            pos.project(camera);
            const x = (pos.x * .5 + .5) * window.innerWidth;
            const y = (pos.y * -.5 + .5) * window.innerHeight;
            tooltip.style.left = `${x}px`;
            tooltip.style.top = `${y}px`;
            tooltip.style.display = pos.z > 1 ? 'none' : 'block';
        }
    }

    // Update Explosions & Shockwaves
    for (let i = explosions.length - 1; i >= 0; i--) {
        let exp = explosions[i];

        // Partiküller
        let positions = exp.system.geometry.attributes.position.array;
        for (let j = 0; j < exp.velocities.length; j++) {
            positions[j * 3] += exp.velocities[j].x;
            positions[j * 3 + 1] += exp.velocities[j].y;
            positions[j * 3 + 2] += exp.velocities[j].z;
        }
        exp.system.geometry.attributes.position.needsUpdate = true;
        exp.system.material.opacity -= 0.015;

        // Şok Dalgası (Splash Radius ~ 1km -> UI Scale: 10 birim büyüyecek)
        exp.wave.scale.x += 1.0;
        exp.wave.scale.y += 1.0;
        exp.wave.scale.z += 1.0;
        exp.wave.material.opacity -= 0.02;

        exp.age++;

        if (exp.age > 60) {
            scene.remove(exp.system);
            scene.remove(exp.wave);
            explosions.splice(i, 1);
        }
    }

    // --- Jamming (Glitch) Efekti ---
    const jammingWarning = document.getElementById("jamming-warning");
    if (window.isJammingActive) {
        if (!jammingWarning) {
            const warning = document.createElement("div");
            warning.id = "jamming-warning";
            warning.className = "jamming-glitch";
            warning.innerText = "WARNING: EW JAMMING DETECTED";
            document.body.appendChild(warning);
        }
    } else {
        if (jammingWarning) {
            jammingWarning.remove();
        }
    }

    // Update Lasers
    for (let i = activeLasers.length - 1; i >= 0; i--) {
        let laser = activeLasers[i];
        laser.line.material.opacity -= 0.05; // Fade out fast (20 frames)
        laser.age++;
        if (laser.age > 20) {
            scene.remove(laser.line);
            activeLasers.splice(i, 1);
        }
    }

    renderer.render(scene, camera);
}
animate();

// --- WebSocket ---
let socket;
function connectWebSocket() {
    socket = new WebSocket("ws://localhost:8000/ws/radar");
    socket.onopen = () => {
        wsStatusEl.textContent = "CONNECTED - SECURE";
        wsStatusEl.style.color = "#0cf50c";
    };
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // Previously data was just targets list, now it's { targets:[], interceptors:[] }
        if (data.targets && data.interceptors !== undefined) {
            window.isJammingActive = data.jamming; // Update global state
            updateDashboard(data.targets, data.interceptors, data.lasers);
        } else {
            window.isJammingActive = false;
            updateDashboard(data, [], []); // Fallback
        }
    };
    socket.onclose = () => {
        wsStatusEl.textContent = "DISCONNECTED - RECONNECTING...";
        wsStatusEl.style.color = "red";
        setTimeout(connectWebSocket, 2000);
    };
}

function updateDashboard(targets, interceptors, lasers) {
    targetListEl.innerHTML = "";

    const activeTargetIds = new Set();
    const activeIntIds = new Set();

    // 1. Update Targets (Neon Spheres)
    const tooltipContainer = document.getElementById('tooltips-container');
    tooltipContainer.innerHTML = '';

    // --- Process Targets ---
    targets.forEach(t => {
        activeTargetIds.add(t.id);
        const isKritik = t.oncelik === "KRİTİK";

        // Sidebar Card
        const card = document.createElement("div");
        card.className = `target-card ${isKritik ? "kritik" : ""}`;
        card.innerHTML = `
            <div><strong class="id-badge">ID: ${t.id}</strong> [${t.tip}]</div>
            <div>RNG: ${parseFloat(t.mesafe).toFixed(1)} km | ALT: ${(parseFloat(t.irtifa) * 1000).toFixed(0)} m</div>
            <div>SPD: ${parseFloat(t.hiz).toFixed(0)} km/h | TTI: ${t.tti !== null ? parseFloat(t.tti).toFixed(1) : "N/A"}s</div>
            <div>PRIO: ${t.oncelik} | ACT: ${t.karar}</div>
        `;
        targetListEl.appendChild(card);

        // 3D Target Mesh
        const posX = t.x;
        const posY = Math.max(t.irtifa * 10, 0);
        const posZ = -t.y;

        let targetColorMat = isKritik ? kritikMat : normalMat;
        if (t.is_jammer) {
            targetColorMat = new THREE.MeshBasicMaterial({ color: 0xffa500 }); // Turuncu (Jammer)
        } else if (t.is_ghost) {
            targetColorMat = new THREE.MeshBasicMaterial({ color: 0xcc00ff }); // Mor/Pembe (Ghost)
        }

        if (targetMeshes[t.id]) {
            targetMeshes[t.id].position.set(posX, posY, posZ);
            targetMeshes[t.id].material = targetColorMat;
            targetTooltips[t.id].className = `tooltip ${isKritik ? "kritik" : ""}`;
            targetTooltips[t.id].textContent = `${t.id} [${(t.irtifa * 1000).toFixed(0)}m]`;

            // Ghost yanıp sönme (glitch) efekti
            if (t.is_ghost && Math.random() < 0.2) {
                targetMeshes[t.id].visible = false;
            } else {
                targetMeshes[t.id].visible = true;
            }
        } else {
            const mesh = new THREE.Mesh(targetGeo, targetColorMat);
            mesh.position.set(posX, posY, posZ);
            scene.add(mesh);
            targetMeshes[t.id] = mesh;

            const tooltip = document.createElement('div');
            tooltip.className = `tooltip ${isKritik ? "kritik" : ""}`;
            tooltip.textContent = `${t.id} [${(t.irtifa * 1000).toFixed(0)}m]`;
            tooltipsContainer.appendChild(tooltip);
            targetTooltips[t.id] = tooltip;
        }
    });

    // --- Process Interceptors ---
    interceptors.forEach(int => {
        activeIntIds.add(int.id);
        const posX = int.x;
        const posY = Math.max(2 * 10, 0); // Flat altitude or mapped altitude if interceptors have altitude
        const posZ = -int.y;

        let mesh = interceptorMeshes[int.id];
        if (mesh) {
            // Calculate direction to rotate the cone
            const dx = posX - mesh.position.x;
            const dy = posY - mesh.position.y;
            const dz = posZ - mesh.position.z;

            // Only update rotation if moved
            if (dx * dx + dy * dy + dz * dz > 0.01) {
                // lookAt makes the object face a point in world space. By default, it faces +Z.
                // Our cone default points +Z because we rotated it in geometry.
                mesh.lookAt(posX + dx, posY + dy, posZ + dz);
            }
            mesh.position.set(posX, posY, posZ);
        } else {
            mesh = new THREE.Mesh(missileGeo, missileMat);
            mesh.position.set(posX, posY, posZ);
            scene.add(mesh);
            interceptorMeshes[int.id] = mesh;
        }
    });

    // --- Cleanup & Explosions ---
    for (const id in targetMeshes) {
        if (!activeTargetIds.has(id)) {
            // Target disappeared. If it was being tracked by an interceptor that also disappeared, 
            // or just simply, if we remove it, create a small explosion!
            createExplosion(targetMeshes[id].position.x, targetMeshes[id].position.y, targetMeshes[id].position.z);
            scene.remove(targetMeshes[id]);
            delete targetMeshes[id];
            if (targetTooltips[id]) {
                targetTooltips[id].remove();
                delete targetTooltips[id];
            }
        }
    }

    for (const id in interceptorMeshes) {
        if (!activeIntIds.has(id)) {
            scene.remove(interceptorMeshes[id]);
            delete interceptorMeshes[id];
        }
    }

    // --- Process CIWS Lasers ---
    if (lasers) {
        lasers.forEach(lz => {
            const endX = lz.x;
            const endY = Math.max(lz.z * 10, 0); // lz.z is altitude (km)
            const endZ = -lz.y;

            // CIWS base is at origin (0, 2, 0)
            createLaserBeam(0, 2, 0, endX, endY, endZ);

            // Lazer vurduğunda ufak bir patlama da olsun
            createExplosion(endX, endY, endZ);
        });
    }

    // --- Update Chart.js ---
    telemetryChart.data.labels.push(chartTime++);
    telemetryChart.data.datasets[0].data.push(targets.length);
    if (telemetryChart.data.labels.length > 30) {
        telemetryChart.data.labels.shift();
        telemetryChart.data.datasets[0].data.shift();
    }
    telemetryChart.update();
}

// --- Interactive C2 UI Controls ---
function sendCommand(action) {
    fetch('/api/command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action: action })
    })
        .catch(err => console.error("Komut gönderim hatası:", err));
}

document.getElementById('btn-force-swarm').addEventListener('click', () => {
    sendCommand('force_swarm');
    // Görsel geri bildirim
    const btn = document.getElementById('btn-force-swarm');
    const originalText = btn.textContent;
    btn.textContent = ">>> INITIATING SWARM <<<";
    setTimeout(() => btn.textContent = originalText, 1000);
});

let autoFire = true;
document.getElementById('btn-toggle-auto').addEventListener('click', () => {
    sendCommand('toggle_auto_fire');
    autoFire = !autoFire;
    const btn = document.getElementById('btn-toggle-auto');
    if (autoFire) {
        btn.textContent = "AUTO-FIRE: ENABLED";
        btn.className = "btn active";
    } else {
        btn.textContent = "AUTO-FIRE: MANUAL OP";
        btn.className = "btn"; // Varsayılan renk (Mavi)
    }
});

window.onload = connectWebSocket;
