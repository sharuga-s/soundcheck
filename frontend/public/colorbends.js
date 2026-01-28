// ColorBends WebGL Background - shared between Flask templates
function initColorBends(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container || typeof THREE === 'undefined') return;
    
    const MAX_COLORS = 8;
    const colors = options.colors || ['#0a4d3c', '#1a6b54', '#2d8c6d', '#3fad85'];
    const speed = options.speed || 0.2;
    const rotation = options.rotation || 45;
    const autoRotate = options.autoRotate || 10;
    const scale = options.scale || 1.2;
    const frequency = options.frequency || 1.2;
    const warpStrength = options.warpStrength || 1.0;
    const mouseInfluence = options.mouseInfluence || 0.5;
    const parallax = options.parallax || 0.5;
    const noise = options.noise || 0.03;
    
    const frag = `
#define MAX_COLORS ${MAX_COLORS}
uniform vec2 uCanvas;
uniform float uTime;
uniform float uSpeed;
uniform vec2 uRot;
uniform int uColorCount;
uniform vec3 uColors[MAX_COLORS];
uniform float uScale;
uniform float uFrequency;
uniform float uWarpStrength;
uniform vec2 uPointer;
uniform float uMouseInfluence;
uniform float uParallax;
uniform float uNoise;
varying vec2 vUv;

void main() {
  float t = uTime * uSpeed;
  vec2 p = vUv * 2.0 - 1.0;
  p += uPointer * uParallax * 0.1;
  vec2 rp = vec2(p.x * uRot.x - p.y * uRot.y, p.x * uRot.y + p.y * uRot.x);
  vec2 q = vec2(rp.x * (uCanvas.x / uCanvas.y), rp.y);
  q /= max(uScale, 0.0001);
  q /= 0.5 + 0.2 * dot(q, q);
  q += 0.2 * cos(t) - 7.56;
  vec2 toward = (uPointer - rp);
  q += toward * uMouseInfluence * 0.2;

  vec3 col = vec3(0.0);

  if (uColorCount > 0) {
    vec2 s = q;
    vec3 sumCol = vec3(0.0);
    for (int i = 0; i < MAX_COLORS; ++i) {
      if (i >= uColorCount) break;
      s -= 0.01;
      vec2 r = sin(1.5 * (s.yx * uFrequency) + 2.0 * cos(s * uFrequency));
      float m0 = length(r + sin(5.0 * r.y * uFrequency - 3.0 * t + float(i)) / 4.0);
      float kBelow = clamp(uWarpStrength, 0.0, 1.0);
      float kMix = pow(kBelow, 0.3);
      float gain = 1.0 + max(uWarpStrength - 1.0, 0.0);
      vec2 disp = (r - s) * kBelow;
      vec2 warped = s + disp * gain;
      float m1 = length(warped + sin(5.0 * warped.y * uFrequency - 3.0 * t + float(i)) / 4.0);
      float m = mix(m0, m1, kMix);
      float w = 1.0 - exp(-6.0 / exp(6.0 * m));
      sumCol += uColors[i] * w;
    }
    col = clamp(sumCol, 0.0, 1.0);
  }

  if (uNoise > 0.0001) {
    float n = fract(sin(dot(gl_FragCoord.xy + vec2(uTime), vec2(12.9898, 78.233))) * 43758.5453123);
    col += (n - 0.5) * uNoise;
    col = clamp(col, 0.0, 1.0);
  }

  gl_FragColor = vec4(col, 1.0);
}
`;

    const vert = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 1.0);
}
`;

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const geometry = new THREE.PlaneGeometry(2, 2);
    
    const uColorsArray = Array.from({ length: MAX_COLORS }, () => new THREE.Vector3(0, 0, 0));
    
    const toVec3 = (hex) => {
        const h = hex.replace('#', '').trim();
        const v = h.length === 3
            ? [parseInt(h[0] + h[0], 16), parseInt(h[1] + h[1], 16), parseInt(h[2] + h[2], 16)]
            : [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
        return new THREE.Vector3(v[0] / 255, v[1] / 255, v[2] / 255);
    };
    
    const colorVecs = colors.slice(0, MAX_COLORS).map(toVec3);
    for (let i = 0; i < MAX_COLORS; i++) {
        if (i < colorVecs.length) {
            uColorsArray[i].copy(colorVecs[i]);
        }
    }
    
    const material = new THREE.ShaderMaterial({
        vertexShader: vert,
        fragmentShader: frag,
        uniforms: {
            uCanvas: { value: new THREE.Vector2(1, 1) },
            uTime: { value: 0 },
            uSpeed: { value: speed },
            uRot: { value: new THREE.Vector2(1, 0) },
            uColorCount: { value: colorVecs.length },
            uColors: { value: uColorsArray },
            uScale: { value: scale },
            uFrequency: { value: frequency },
            uWarpStrength: { value: warpStrength },
            uPointer: { value: new THREE.Vector2(0, 0) },
            uMouseInfluence: { value: mouseInfluence },
            uParallax: { value: parallax },
            uNoise: { value: noise }
        }
    });
    
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);
    
    const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    renderer.domElement.style.display = 'block';
    container.appendChild(renderer.domElement);
    
    const clock = new THREE.Clock();
    const pointerTarget = new THREE.Vector2(0, 0);
    const pointerCurrent = new THREE.Vector2(0, 0);
    
    const handleResize = () => {
        const w = container.clientWidth || 1;
        const h = container.clientHeight || 1;
        renderer.setSize(w, h, false);
        material.uniforms.uCanvas.value.set(w, h);
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    
    container.addEventListener('pointermove', (e) => {
        const rect = container.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
        pointerTarget.set(x, y);
    });
    
    const animate = () => {
        const dt = clock.getDelta();
        const elapsed = clock.elapsedTime;
        
        material.uniforms.uTime.value = elapsed;
        
        const deg = (rotation % 360) + autoRotate * elapsed;
        const rad = (deg * Math.PI) / 180;
        material.uniforms.uRot.value.set(Math.cos(rad), Math.sin(rad));
        
        pointerCurrent.lerp(pointerTarget, Math.min(1, dt * 8));
        material.uniforms.uPointer.value.copy(pointerCurrent);
        
        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    };
    
    animate();
}
