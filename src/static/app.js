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
    const particleCount = 50;
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    const velArray = [];

    for (let i = 0; i < particleCount; i++) {
        posArray[i * 3] = x;
        posArray[i * 3 + 1] = y;
        posArray[i * 3 + 2] = z;
        velArray.push({
            x: (Math.random() - 0.5) * 10,
            y: (Math.random() - 0.5) * 10,
            z: (Math.random() - 0.5) * 10
        });
    }
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    const particleMat = new THREE.PointsMaterial({
        size: 2,
        color: 0xffaa00,
        transparent: true,
        opacity: 1
    });

    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);
    explosions.push({ system: particleSystem, velocities: velArray, age: 0 });
}

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

    // Update Explosions
    for (let i = explosions.length - 1; i >= 0; i--) {
        let exp = explosions[i];
        let positions = exp.system.geometry.attributes.position.array;

        for (let j = 0; j < exp.velocities.length; j++) {
            positions[j * 3] += exp.velocities[j].x;
            positions[j * 3 + 1] += exp.velocities[j].y;
            positions[j * 3 + 2] += exp.velocities[j].z;
        }
        exp.system.geometry.attributes.position.needsUpdate = true;
        exp.system.material.opacity -= 0.02;
        exp.age++;

        if (exp.age > 50) {
            scene.remove(exp.system);
            explosions.splice(i, 1);
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
            updateDashboard(data.targets, data.interceptors);
        } else {
            updateDashboard(data, []); // Fallback
        }
    };
    socket.onclose = () => {
        wsStatusEl.textContent = "DISCONNECTED - RECONNECTING...";
        wsStatusEl.style.color = "red";
        setTimeout(connectWebSocket, 2000);
    };
}

function updateDashboard(targets, interceptors) {
    targetListEl.innerHTML = "";

    const activeTargetIds = new Set();
    const activeIntIds = new Set();

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

        if (targetMeshes[t.id]) {
            targetMeshes[t.id].position.set(posX, posY, posZ);
            targetMeshes[t.id].material = isKritik ? kritikMat : normalMat;
            targetTooltips[t.id].className = `tooltip ${isKritik ? "kritik" : ""}`;
            targetTooltips[t.id].textContent = `${t.id} [${(t.irtifa * 1000).toFixed(0)}m]`;
        } else {
            const mesh = new THREE.Mesh(targetGeo, isKritik ? kritikMat : normalMat);
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
}

window.onload = connectWebSocket;
