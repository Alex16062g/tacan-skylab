import { imagenRegional } from './image-source.js';
const body=new URLSearchParams(location.search).get('body')==='MARS'?'MARS':'MOON';
if (new URLSearchParams(location.search).get('embed') === '1') {
  document.body.classList.add('embedded');
  document.querySelectorAll('header, h1, .summary, figure figcaption, .sources, .resolution, details').forEach(el => { el.hidden = true; });
  const control = document.getElementById('swipe');
  control.removeAttribute('aria-labelledby');
  control.setAttribute('aria-label', 'Comparar imágenes de Tacaná y la región planetaria');
  const fuentes = document.createElement('div');
  fuentes.className = 'embedded-sources';
  fuentes.setAttribute('aria-label', 'Referencias de las imágenes');
  document.getElementById('comparison').append(fuentes);
}
const bodyName=body==='MOON'?'Luna':'Marte';
const $=id=>document.getElementById(id);
const slider=$('swipe');
document.querySelector(`[data-body="${body}"]`).setAttribute('aria-current','page');
$('retry').addEventListener('click',()=>location.reload());
function update() {
  const value=Number(slider.value);
  $('stage').style.setProperty('--split',`${value}%`);
  const text=`Tacaná ${value} % · ${bodyName} ${100-value} %`;
  $('position').textContent=text;
  slider.setAttribute('aria-valuetext',text);
  $('earth-tag').hidden=value===0;
  $('planet-tag').hidden=value===100;
}
slider.addEventListener('input',update);update();
async function load(url) {
  const response=await fetch(url,{cache:'no-store'});
  if(!response.ok)throw new Error(`${url}: ${response.status}`);
  return response.json();
}
try {
  const [sources,summary]=await Promise.all([load('./fuentes.json'),load('../comparacion_tacana/similitud_catalogo_resumen.json')]);
  const id=new URLSearchParams(location.search).get('region') ?? summary.selections[body].selected_region;
  const view = new URLSearchParams(location.search).get('view') === 'analysis' ? 'analysis' : 'full';
  $('status').textContent = 'Preparando imagen de la región…';
  const regional = await imagenRegional(body, id, view);
  sources.images[body] = regional;
  const region = { name: regional.name, primary: { similarity_percent: regional.similarity_percent } };
  const earth=sources.images.EARTH,planet=sources.images[body];
  const referencias = document.querySelector('.embedded-sources');
  if (referencias) {
    const obras = {
      EARTH: ['U.S. Geological Survey', 'Landsat 8 Collection 2 Level-2: LC08_L2SP_021050_20251126_02_T1', 'Imagen satelital; recorte RGB de 30 m'],
      MOON: ['LROC Science Operations Center', 'Moon LRO LROC WAC global morphology mosaic 100m', 'Mosaico lunar'],
      MARS: ['Murray Laboratory, California Institute of Technology', 'Global CTX Mosaic of Mars', 'Mosaico de Marte']
    };
    const fecha = new Date(sources.retrieved_utc).toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
    for (const key of ['EARTH', body]) {
      const [autor, titulo, tipo] = obras[key];
      const p = document.createElement('p'), cursiva = document.createElement('cite'), enlace = document.createElement('a');
      cursiva.textContent = titulo;
      const imagen = document.createElement('a');
      imagen.href = new URL(sources.images[key].file, location.href);
      imagen.target = '_blank'; imagen.rel = 'noopener';
      imagen.setAttribute('aria-label', `${titulo}: ver imagen utilizada`);
      imagen.append(cursiva);
      enlace.href = sources.images[key].source_url; enlace.textContent = enlace.href;
      enlace.target = '_blank'; enlace.rel = 'noopener';
      const anio = sources.images[key].publication_year ?? (key === 'EARTH' ? '2025' : key === 'MOON' ? '2014' : 's. f.');
      p.append(`${autor}. (${anio}). `, imagen, ` [${tipo}]. Recuperado el ${fecha}, de `, enlace);
      if (sources.images[key].license_url) {
        const licencia = document.createElement('a'); licencia.href = sources.images[key].license_url;
        licencia.textContent = 'Condiciones de uso'; licencia.target = '_blank'; licencia.rel = 'noopener';
        p.append(' · ', licencia);
      }
      referencias.append(p);
    }
  }
  $('title').textContent=`Tacaná y ${region.name} · ${bodyName}`;
  document.title=`${region.name}: comparación de imágenes | Tacaná`;
  $('planet').src=planet.file;
  $('planet').alt=`Imagen orbital del entorno de ${region.name}, ${bodyName}`;
  $('planet-tag').textContent=`${bodyName} · ${region.name} · ${regional.window_side_km.toLocaleString('es-MX',{maximumFractionDigits:1})} km`;
  $('earth-tag').textContent = 'Tacaná · 12 km';
  document.querySelector('.scale').hidden = true;
  document.querySelector('.summary span').textContent = 'Norte arriba · extensión indicada en cada imagen';
  $('score').textContent=Number.isFinite(region.primary.similarity_percent) ? `Índice del relieve: ${region.primary.similarity_percent.toLocaleString('es-MX',{maximumFractionDigits:2})} / 100` : 'Índice no disponible';
  const controls = document.createElement('div'); controls.className = 'image-view-controls';
  if(Number.isFinite(regional.coverage_fraction)&&regional.coverage_fraction<.9999){const notice=document.createElement('p');notice.textContent=`Cobertura disponible: ${(regional.coverage_fraction*100).toFixed(1)} %`;controls.append(notice);}
  if (controls.childElementCount) $('comparison').prepend(controls);
  for(const [image,prefix] of [[earth,'earth'],[planet,'planet']]) {
    const anchor=$(`${prefix}-source`);anchor.textContent=image.credit;anchor.href=image.source_url;
  }
  $('resolution').textContent=`${bodyName}: fuente de ${regional.native_resolution_m} m/píxel; nivel utilizado de ${regional.display_source_resolution_m.toLocaleString('es-MX',{maximumFractionDigits:1})} m/píxel.`;
  $('coordinates').textContent=`Centros (longitud, latitud): Tacaná ${earth.center.join(', ')}; ${region.name} ${planet.center.join(', ')}.`;
  $('terrain-link').href=`../comparador_3d/index.html?body=${body}`;
  $('terrain-link').hidden = id !== sources.selected_regions[body];
  await Promise.all([$('earth').decode(),$('planet').decode()]);
  $('status').hidden=true;$('comparison').hidden=false;
} catch(error) {
  console.error(error);$('status').textContent=error.message;$('retry').hidden=false;
}
