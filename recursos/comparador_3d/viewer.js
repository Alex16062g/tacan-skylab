const body = new URLSearchParams(location.search).get('body') === 'MARS' ? 'MARS' : 'MOON';
const bodyName = body === 'MOON' ? 'Luna' : 'Marte';
const number = (value, digits = 2) => value.toLocaleString('es-MX', { maximumFractionDigits: digits });
const percent = value => value.toLocaleString('es-MX', { minimumFractionDigits: 6, maximumFractionDigits: 6 });
const $ = id => document.getElementById(id);
document.querySelector(`[data-body="${body}"]`).setAttribute('aria-current', 'page');
$('retry').addEventListener('click', () => location.reload());
const views = [];
const state = { azimuth: .65, elevation: .65, distance: 22, wire: false };
let THREE;

function draw() {
  state.elevation = Math.max(.12, Math.min(Math.PI / 2 - .01, state.elevation));
  state.distance = Math.max(10, Math.min(45, state.distance));
  for (const view of views) {
    const width = view.host.clientWidth, height = view.host.clientHeight;
    if (!width || !height) continue;
    view.renderer.setSize(width, height, false);
    view.camera.aspect = width / height;
    view.camera.position.set(
      state.distance * Math.cos(state.elevation) * Math.sin(state.azimuth),
      state.distance * Math.sin(state.elevation),
      state.distance * Math.cos(state.elevation) * Math.cos(state.azimuth));
    view.camera.lookAt(0, 0, 0);
    view.camera.updateProjectionMatrix();
    view.wire.visible = state.wire;
    view.renderer.render(view.scene, view.camera);
  }
}

function action(name) {
  if (name === 'left') state.azimuth -= .2;
  if (name === 'right') state.azimuth += .2;
  if (name === 'up') state.elevation += .12;
  if (name === 'down') state.elevation -= .12;
  if (name === 'in') state.distance /= 1.15;
  if (name === 'out') state.distance *= 1.15;
  if (name === 'top') { state.elevation = Math.PI / 2 - .01; state.azimuth = 0; }
  if (name === 'reset') Object.assign(state, { azimuth: .65, elevation: .65, distance: 22 });
  draw();
}

function controls(canvas) {
  const pointers = new Map();
  const gap = () => { const [a,b] = [...pointers.values()]; return Math.hypot(a.x-b.x,a.y-b.y); };
  canvas.addEventListener('pointerdown', event => {
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', event => {
    const old = pointers.get(event.pointerId);
    if (!old) return;
    const before = pointers.size === 2 ? gap() : null;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (before !== null) {
      const after = gap();
      if (after > 0) state.distance *= before / after;
    } else {
      state.azimuth -= (event.clientX-old.x)*.006;
      state.elevation += (event.clientY-old.y)*.006;
    }
    draw();
  });
  for (const event of ['pointerup','pointercancel','lostpointercapture']) {
    canvas.addEventListener(event, e => pointers.delete(e.pointerId));
  }
  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    state.distance *= Math.exp(Math.max(-100,Math.min(100,event.deltaY))*.002);
    draw();
  }, { passive: false });
  canvas.addEventListener('keydown', event => {
    const name = { ArrowLeft:'left', ArrowRight:'right', ArrowUp:'up', ArrowDown:'down', '+':'in', '=':'in', '-':'out', Home:'reset' }[event.key];
    if (name) { event.preventDefault(); action(name); }
  });
}

function label(scene, text, x, y, z) {
  const canvas = document.createElement('canvas'); canvas.width = 256; canvas.height = 64;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#f8fafc'; ctx.font = '36px system-ui'; ctx.textAlign = 'center';
  ctx.fillText(text,128,46);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map:new THREE.CanvasTexture(canvas), depthTest:false }));
  sprite.position.set(x,y,z); sprite.scale.set(2,.5,1); scene.add(sprite);
}

function build(host, model, low, high) {
  const renderer = new THREE.WebGLRenderer({ antialias:true, alpha:false });
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.setClearColor(0x111c26);
  const canvas = renderer.domElement;
  canvas.tabIndex = 0;
  canvas.setAttribute('role','img');
  canvas.setAttribute('aria-label', `Terreno 3D de ${model.name}. Altura relativa, escala vertical uno a uno.`);
  canvas.setAttribute('aria-describedby','controls-help');
  canvas.textContent = `Modelo de elevación de ${model.name}. Los datos están disponibles en el enlace de descarga.`;
  host.append(canvas);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42,1,.1,100);
  scene.add(new THREE.HemisphereLight(0xffffff,0x334455,2));
  const light = new THREE.DirectionalLight(0xffffff,2.4); light.position.set(-6,10,4); scene.add(light);
  const positions = [], colors = [], indices = [];
  const count = 49; // Bilinear display interpolation of the 7x7 analysis grid only.
  const dark = new THREE.Color('#21475a'), pale = new THREE.Color('#a6dce5');
  for (let row=0;row<count;row++) for (let col=0;col<count;col++) {
    const ry = row/8, rx = col/8, y0=Math.min(5,Math.floor(ry)), x0=Math.min(5,Math.floor(rx));
    const fy=ry-y0, fx=rx-x0, h=model.heights_m;
    const height = ((1-fy)*((1-fx)*h[y0][x0]+fx*h[y0][x0+1])+fy*((1-fx)*h[y0+1][x0]+fx*h[y0+1][x0+1])-model.median_m)/1000;
    positions.push(col*.25-6,height,6-row*.25);
    const color=dark.clone().lerp(pale,(height-low)/(high-low || 1));
    colors.push(color.r,color.g,color.b);
    if (row<count-1 && col<count-1) {
      const a=row*count+col;
      indices.push(a,a+1,a+count,a+1,a+count+1,a+count);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  geometry.setIndex(indices); geometry.computeVertexNormals();
  scene.add(new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({vertexColors:true, roughness:1, side:THREE.DoubleSide})));
  const wire = new THREE.LineSegments(new THREE.WireframeGeometry(geometry),new THREE.LineBasicMaterial({color:0xc6dce7,transparent:true,opacity:.18}));
  scene.add(wire);
  const floor=low-.25;
  const base=new THREE.Mesh(new THREE.PlaneGeometry(12,12),new THREE.MeshStandardMaterial({color:0x203440,side:THREE.DoubleSide}));
  base.rotation.x=-Math.PI/2; base.position.y=floor; scene.add(base);
  const north = new THREE.ArrowHelper(new THREE.Vector3(0,0,-1),new THREE.Vector3(-6.5,floor,0),2,0xffffff,.4,.25);
  scene.add(north); label(scene,'N',-6.5,floor,-2.6);
  const line=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-1,floor,6.5),new THREE.Vector3(1,floor,6.5)]);
  scene.add(new THREE.Line(line,new THREE.LineBasicMaterial({color:0xffffff})));
  label(scene,'2 km',0,floor,7.1);
  const view={renderer,scene,camera,wire,host}; views.push(view);
  controls(canvas);
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault(); $('status').textContent='La vista 3D se ha interrumpido. Recarga el comparador.'; $('status').hidden=false; $('retry').hidden=false;
  });
  return view;
}

async function init() {
  const response = await fetch(`./${body.toLowerCase()}.json`, {cache:'no-store'});
  if (!response.ok) throw new Error('No se pudieron cargar los terrenos.');
  const data = await response.json();
  for (const model of [data.reference,data.comparison]) {
    if (model.heights_m?.length!==7 || model.heights_m.some(row=>row.length!==7 || !row.every(Number.isFinite)) || !Number.isFinite(model.median_m)) throw new Error('Los datos del terreno no tienen el formato esperado.');
  }
  $('title').textContent=`Tacaná y ${data.comparison.name} · ${bodyName}`;
  document.title=`${data.comparison.name} en 3D | Tacaná`;
  $('region-name').textContent=data.comparison.name;
  $('score').textContent=`${percent(data.similarity.similarity_percent)} %`;
  $('download').href=`./${body.toLowerCase()}.json`;
  const relative = model => model.heights_m.flat().map(h=>(h-model.median_m)/1000);
  const all=[...relative(data.reference),...relative(data.comparison)];
  const low=Math.min(...all),high=Math.max(...all);
  $('color-min').textContent=`${number(low*1000)} m`; $('color-max').textContent=`${number(high*1000)} m`;
  for (const [model,prefix] of [[data.reference,'reference'],[data.comparison,'region']]) {
    $(`${prefix}-coordinates`).textContent=`${number(model.center[1],4)}° lat. · ${number(model.center[0],4)}° lon.`;
    const values=relative(model);
    $(`${prefix}-range`).textContent=`Altura relativa: ${number(Math.min(...values)*1000)} a ${number(Math.max(...values)*1000)} m`;
  }
  for (const feature of data.similarity.features) {
    const row=document.createElement('tr'), th=document.createElement('th'); th.scope='row'; th.textContent=feature.label; row.append(th);
    for (const text of [percent(feature.similarity_percent),`${number(feature.weight*100)} %`]) {
      const td=document.createElement('td');td.textContent=text;row.append(td);
    }
    $('metrics').append(row);
  }
  $('sensitivity').textContent=`Sensibilidad a escala de 3 km: ${percent(data.sensitivity.similarity_percent)} %.`;
  $('content').hidden=false;
  THREE = await import('./vendor/three.module.js');
  build($('reference'),data.reference,low,high);
  build($('comparison'),data.comparison,low,high);
  document.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',()=>action(button.dataset.action)));
  $('wire').addEventListener('click',()=>{state.wire=!state.wire;$('wire').setAttribute('aria-pressed',String(state.wire));draw();});
  const observer=new ResizeObserver(draw); views.forEach(view=>observer.observe(view.host));
  draw(); $('status').hidden=true;
}

init().catch(error=>{
  console.error(error);
  $('status').hidden=false;
  $('status').textContent='No se pudo abrir la vista 3D. Comprueba los archivos y que WebGL esté disponible en tu navegador.';
  $('retry').hidden=false;
  document.querySelectorAll('.controls button').forEach(button=>button.disabled=true);
});
