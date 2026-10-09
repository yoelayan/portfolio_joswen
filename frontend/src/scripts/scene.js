/**
 * Escena 3D del hero: un anillo helicoidal de pósters impresos.
 * Las portadas de los proyectos (subidas desde el admin) se proyectan sobre
 * algunos pósters; el resto usa un cartel procedural con semitonos.
 */
import * as THREE from "three";

// Trabajamos con valores sRGB "crudos" en los shaders (sin conversión lineal).
THREE.ColorManagement.enabled = false;

const canvas = document.getElementById("scene");

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const easeOut = (x) => 1 - Math.pow(1 - x, 3);

function hex3(hex) {
  const n = parseInt(String(hex).replace("#", ""), 16);
  return new THREE.Vector3(((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255);
}

const VERT = /* glsl */ `
  uniform float uCurl;
  varying vec2 vUv;
  varying float vShade;
  void main() {
    vUv = uv;
    vec3 p = position;
    float x = uv.x - 0.5;
    p.z += (x * x - 0.06) * uCurl;
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    vShade = clamp(1.0 + (mv.z + 12.0) * 0.05, 0.42, 1.0);
    gl_Position = projectionMatrix * mv;
  }
`;

const FRAG = /* glsl */ `
  uniform sampler2D uTex;
  uniform float uHasTex;
  uniform float uAspect;
  uniform float uFade;
  uniform float uSeed;
  uniform vec3 uA;
  uniform vec3 uB;
  uniform vec3 uC;
  varying vec2 vUv;
  varying float vShade;

  float halftone(vec2 uv, float scale, float v) {
    vec2 g = fract(uv * scale) - 0.5;
    float r = sqrt(clamp(v, 0.0, 1.0)) * 0.7071;
    return smoothstep(r + 0.04, r - 0.04, length(g));
  }

  vec3 poster(vec2 uv) {
    vec2 p = uv - 0.5;
    p.x *= 0.7071;
    vec3 col = uA;
    float kind = floor(uSeed * 3.0);
    if (kind < 1.0) {
      float c = smoothstep(0.30, 0.295, length(p - vec2(0.02, 0.10)));
      col = mix(col, uB, c);
      float h = halftone(uv * vec2(0.7071, 1.0), 26.0, 1.0 - uv.y);
      col = mix(col, uC, h * (1.0 - c));
    } else if (kind < 2.0) {
      float bars = step(0.5, fract(uv.y * 9.0));
      col = mix(col, uB, step(0.52, uv.y) * step(uv.x, 0.62));
      col = mix(col, uC, bars * step(uv.y, 0.4));
    } else {
      float d = length(p - vec2(-0.10, -0.15));
      float rings = step(0.5, fract(d * 9.0));
      col = mix(col, uB, rings * step(d, 0.55));
      col = mix(col, uC, smoothstep(0.12, 0.115, length(p - vec2(0.12, 0.2))));
    }
    return col;
  }

  void main() {
    vec3 col = poster(vUv);
    if (uHasTex > 0.5) {
      float pa = 0.7071;
      vec2 s = uAspect > pa ? vec2(pa / uAspect, 1.0) : vec2(1.0, uAspect / pa);
      vec2 uv = (vUv - 0.5) * s + 0.5;
      col = mix(col, texture2D(uTex, uv).rgb, uFade);
    }
    gl_FragColor = vec4(col * vShade, 1.0);
  }
`;

function boot(canvas) {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const small = matchMedia("(max-width: 720px)").matches;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
  } catch (error) {
    document.documentElement.classList.add("no-webgl");
    return;
  }
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, small ? 1.5 : 1.75));
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(0, 0, 13);

  const accent = canvas.dataset.accent || "#ff5a1f";
  const covers = safeJson(canvas.dataset.covers);
  const useSpline = canvas.dataset.spline === "1";

  // --- Pósters -------------------------------------------------------------
  const palettes = [
    ["#f3f5ff", accent, "#0b1052"],
    [accent, "#f3f5ff", "#1d2dea"],
    ["#7fe4ff", "#0b1052", accent],
    ["#0b1052", "#7fe4ff", "#f3f5ff"],
    ["#f3f5ff", "#1d2dea", "#7fe4ff"],
    ["#1d2dea", "#f3f5ff", accent],
  ];

  const group = new THREE.Group();
  group.rotation.set(0.12, 0, -0.16);
  group.visible = !useSpline;
  scene.add(group);

  const geometry = new THREE.PlaneGeometry(1.9, 2.69, 20, 1);
  const count = small ? 9 : 13;
  const posters = [];

  for (let i = 0; i < count; i++) {
    const [a, b, c] = palettes[i % palettes.length];
    const material = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      side: THREE.DoubleSide,
      uniforms: {
        uCurl: { value: 0.7 },
        uTex: { value: null },
        uHasTex: { value: 0 },
        uAspect: { value: 1 },
        uFade: { value: 0 },
        uSeed: { value: ((i * 0.37) % 1) * 0.999 },
        uA: { value: hex3(a) },
        uB: { value: hex3(b) },
        uC: { value: hex3(c) },
      },
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.userData = {
      angle: (i / count) * Math.PI * 2,
      height: (i / (count - 1) - 0.5) * 4.6 + Math.sin(i * 2.1) * 0.35,
      roll: Math.sin(i * 12.9898) * 0.12,
      fadeStart: 0,
    };
    posters.push(mesh);
    group.add(mesh);
  }

  // --- Partículas de tinta -------------------------------------------------
  const dotCanvas = document.createElement("canvas");
  dotCanvas.width = dotCanvas.height = 64;
  const ctx = dotCanvas.getContext("2d");
  ctx.beginPath();
  ctx.arc(32, 32, 30, 0, Math.PI * 2);
  ctx.fillStyle = "#fff";
  ctx.fill();
  const dotTexture = new THREE.CanvasTexture(dotCanvas);

  const dotCount = small ? 260 : 700;
  const dotPositions = new Float32Array(dotCount * 3);
  for (let i = 0; i < dotCount; i++) {
    const r = 5 + Math.random() * 9;
    const theta = Math.random() * Math.PI * 2;
    dotPositions[i * 3] = Math.cos(theta) * r;
    dotPositions[i * 3 + 1] = (Math.random() - 0.5) * 14;
    dotPositions[i * 3 + 2] = Math.sin(theta) * r - 4;
  }
  const dotGeometry = new THREE.BufferGeometry();
  dotGeometry.setAttribute("position", new THREE.BufferAttribute(dotPositions, 3));
  const dots = new THREE.Points(
    dotGeometry,
    new THREE.PointsMaterial({
      size: 0.07,
      map: dotTexture,
      color: 0xf3f5ff,
      transparent: true,
      opacity: 0.55,
      depthWrite: false,
    })
  );
  scene.add(dots);

  // --- Portadas como texturas ---------------------------------------------
  const loader = new THREE.TextureLoader();
  loader.setCrossOrigin("anonymous");
  const textures = new Map();
  if (covers.length) {
    const slots = posters.filter((_, i) => i % 2 === 0);
    slots.forEach((mesh, k) => {
      const url = covers[k % covers.length];
      if (!url) return;
      const apply = (texture) => {
        const u = mesh.material.uniforms;
        u.uTex.value = texture;
        u.uAspect.value = texture.image.width / texture.image.height;
        u.uHasTex.value = 1;
        mesh.userData.fadeStart = performance.now();
        if (reduce) {
          u.uFade.value = 1;
          draw(10);
        }
      };
      if (textures.has(url)) {
        textures.get(url).then(apply).catch(() => {});
        return;
      }
      const promise = new Promise((resolve, reject) =>
        loader.load(
          url,
          (texture) => {
            texture.minFilter = THREE.LinearMipmapLinearFilter;
            texture.anisotropy = 4;
            resolve(texture);
          },
          undefined,
          reject
        )
      );
      textures.set(url, promise);
      promise.then(apply).catch(() => {});
    });
  }

  // --- Layout y entrada ----------------------------------------------------
  const base = { x: 0, y: 0, scale: 1, radius: 4.4 };
  function layout() {
    const w = canvas.clientWidth || window.innerWidth;
    const h = canvas.clientHeight || window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    const wide = camera.aspect > 1.15;
    base.x = wide ? 2.7 : 0;
    base.y = wide ? 0 : 1.7;
    base.scale = wide ? 1 : 0.62;
    draw(reduce ? 10 : lastTime);
  }
  new ResizeObserver(layout).observe(canvas);

  // --- Interacción ---------------------------------------------------------
  const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
  if (!reduce) {
    window.addEventListener(
      "pointermove",
      (event) => {
        pointer.tx = (event.clientX / window.innerWidth) * 2 - 1;
        pointer.ty = (event.clientY / window.innerHeight) * 2 - 1;
      },
      { passive: true }
    );
  }
  let scrollP = 0;

  // --- Bucle ---------------------------------------------------------------
  let lastTime = 0;
  function draw(t) {
    lastTime = t;
    const now = performance.now();
    const enter = reduce ? 1 : easeOut(clamp((t - 0.2) / 2.4));

    group.rotation.y = (reduce ? 0.6 : t * 0.12) + (1 - enter) * Math.PI * 1.6 + scrollP * 1.4 + pointer.x * 0.25;
    group.rotation.x = 0.12 + pointer.y * 0.06;
    group.position.set(base.x, base.y + scrollP * 2.2, 0);
    group.scale.setScalar(base.scale * (1 + scrollP * 0.15));

    posters.forEach((mesh, i) => {
      const d = mesh.userData;
      const e = reduce ? 1 : easeOut(clamp((t - 0.2 - i * 0.05) / 1.6));
      const radius = base.radius * (0.3 + 0.7 * e) + scrollP * 2.4;
      const sway = reduce ? 0 : Math.sin(t * 0.6 + i) * 0.05;
      mesh.position.set(Math.sin(d.angle) * radius, d.height + Math.sin(t * 0.5 + i * 1.3) * (reduce ? 0 : 0.12), Math.cos(d.angle) * radius);
      mesh.rotation.set(0, d.angle + sway, d.roll);
      mesh.scale.setScalar(Math.max(0.001, e));
      const u = mesh.material.uniforms;
      if (u.uHasTex.value && u.uFade.value < 1) {
        u.uFade.value = reduce ? 1 : clamp((now - d.fadeStart) / 700);
      }
    });

    dots.rotation.y = reduce ? 0 : t * 0.02;
    dots.position.y = scrollP * 1.2;

    camera.position.x = pointer.x * 0.7;
    camera.position.y = -pointer.y * 0.45;
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  }

  if (reduce) {
    layout();
    return;
  }

  const hero = document.getElementById("inicio");
  let visible = true;
  let raf = 0;
  const start = performance.now();

  function frame(now) {
    if (!visible || document.hidden) {
      raf = 0;
      return;
    }
    pointer.x += (pointer.tx - pointer.x) * 0.05;
    pointer.y += (pointer.ty - pointer.y) * 0.05;
    const target = clamp(window.scrollY / window.innerHeight);
    scrollP += (target - scrollP) * 0.08;
    draw((now - start) / 1000);
    raf = requestAnimationFrame(frame);
  }
  const wake = () => {
    if (!raf && visible && !document.hidden) raf = requestAnimationFrame(frame);
  };

  if (hero && "IntersectionObserver" in window) {
    new IntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting;
        wake();
      },
      { threshold: 0 }
    ).observe(hero);
  }
  document.addEventListener("visibilitychange", wake);
  layout();
  wake();
}

function safeJson(value) {
  try {
    const parsed = JSON.parse(value || "[]");
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [];
  }
}

// Se arranca al final, cuando todas las constantes del módulo (shaders) ya están definidas.
if (canvas) boot(canvas);
