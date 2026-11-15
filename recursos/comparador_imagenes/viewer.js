import * as i18n from '../../idiomas/i18n.js';
import { imagenRegional } from './image-source.js';
const body=new URLSearchParams(location.search).get('body')==='MARS'?'MARS':'MOON';
if (new URLSearchParams(location.search).get('embed') === '1') {
  document.body.classList.add('embedded');
  document.querySelectorAll('header, h1, .summary, figure figcaption, .sources, .resolution, details').forEach(el => { el.hidden = true; });
  const control = document.getElementById('swipe');
  control.removeAttribute('aria-labelledby');
  i18n.attr(control, 'aria-label', () => i18n.t("comparar_imagenes_de_tacana_y_la_region_planetaria"));
  const fuentes = document.createElement('div');
  fuentes.className = 'embedded-sources';
  i18n.attr(fuentes, 'aria-label', () => i18n.t("referencias_de_las_imagenes"));
  document.getElementById('comparison').append(fuentes);
}
const bodyName=body==='MOON'?i18n.t("luna"):i18n.t("marte");
const $=id=>document.getElementById(id);
const slider=$('swipe');
document.querySelector(`[data-body="${body}"]`).setAttribute('aria-current','page');
$('retry').addEventListener('click',()=>location.reload());
function update() {
  const value=Number(slider.value);
  $('stage').style.setProperty('--split',`${value}%`);
  const text=() => `Tacaná ${value} % · ${i18n.localize(bodyName)} ${100-value} %`;
  i18n.text($('position'), () => text());
  i18n.attr(slider, 'aria-valuetext', () => text());
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
  i18n.text($('status'), () => i18n.t("preparando_imagen_de_la_region"));
  const regional = await imagenRegional(body, id, view);
  sources.images[body] = regional;
  const region = { name: regional.name, primary: { similarity_percent: regional.similarity_percent } };
  const earth=sources.images.EARTH,planet=sources.images[body];
  const referencias = document.querySelector('.embedded-sources');
  if (referencias) {
    const obras = {
      EARTH: ['U.S. Geological Survey', 'Landsat 8 Collection 2 Level-2: LC08_L2SP_021050_20251126_02_T1', i18n.t("imagen_satelital_recorte_rgb_de_30_m")],
      MOON: ['LROC Science Operations Center', 'Moon LRO LROC WAC global morphology mosaic 100m', i18n.t("mosaico_lunar")],
      MARS: ['Murray Laboratory, California Institute of Technology', 'Global CTX Mosaic of Mars', i18n.t("mosaico_de_marte")]
    };
    const fecha = () => i18n.date(sources.retrieved_utc, { day: 'numeric', month: 'long', year: 'numeric' });
    for (const key of ['EARTH', body]) {
      const [autor, titulo, tipo] = obras[key];
      const p = document.createElement('p'), cursiva = document.createElement('cite'), enlace = document.createElement('a');
      i18n.text(cursiva, () => titulo);
      const imagen = document.createElement('a');
      imagen.href = new URL(sources.images[key].file, location.href);
      imagen.target = '_blank'; imagen.rel = 'noopener';
      i18n.attr(imagen, 'aria-label', () => i18n.t("0_ver_imagen_utilizada", [titulo]));
      imagen.append(cursiva);
      enlace.href = sources.images[key].source_url; i18n.text(enlace, () => enlace.href);
      enlace.target = '_blank'; enlace.rel = 'noopener';
      const anio = sources.images[key].publication_year ?? (key === 'EARTH' ? '2025' : key === 'MOON' ? '2014' : i18n.t("s_f"));
      p.append(i18n.node(() => `${autor}. (${i18n.localize(anio)}). `), imagen, i18n.node(() => i18n.t("retrieved", [tipo, fecha()])), enlace);
      if (sources.images[key].license_url) {
        const licencia = document.createElement('a'); licencia.href = sources.images[key].license_url;
        i18n.text(licencia, () => i18n.t("condiciones_de_uso")); licencia.target = '_blank'; licencia.rel = 'noopener';
        p.append(' · ', licencia);
      }
      referencias.append(p);
    }
  }
  i18n.text($('title'), () => i18n.t("tacana_y_0_1", [region.name, bodyName]));
  i18n.title(() => i18n.t("0_comparacion_de_imagenes_tacana", [region.name]));
  $('planet').src=planet.file;
  i18n.attr($('planet'), "alt", () => i18n.t("imagen_orbital_del_entorno_de_0_1", [region.name, bodyName]));
  i18n.text($('planet-tag'), () => `${i18n.localize(bodyName)} · ${region.name} · ${regional.window_side_km.toLocaleString(i18n.locale(),{maximumFractionDigits:1})} km`);
  i18n.text($('earth-tag'), () => 'Tacaná · 12 km');
  document.querySelector('.scale').hidden = true;
  i18n.text(document.querySelector('.summary span'), () => i18n.t("norte_arriba_extension_indicada_en_cada_imagen"));
  i18n.text($('score'), () => Number.isFinite(region.primary.similarity_percent) ? i18n.t("indice_del_relieve_0_100", [region.primary.similarity_percent.toLocaleString(i18n.locale(),{maximumFractionDigits:2})]) : i18n.t("indice_no_disponible"));
  const controls = document.createElement('div'); controls.className = 'image-view-controls';
  if(Number.isFinite(regional.coverage_fraction)&&regional.coverage_fraction<.9999){const notice=document.createElement('p');i18n.text(notice, () => i18n.t("cobertura_disponible_0", [(regional.coverage_fraction*100).toFixed(1)]));controls.append(notice);}
  if (controls.childElementCount) $('comparison').prepend(controls);
  for(const [image,prefix] of [[earth,'earth'],[planet,'planet']]) {
    const anchor=$(`${prefix}-source`);i18n.text(anchor, () => image.credit);anchor.href=image.source_url;
  }
  i18n.text($('resolution'), () => i18n.t("0_fuente_de_1_m_pixel_nivel_utilizado_de_2_m_pixel", [bodyName, regional.native_resolution_m, regional.display_source_resolution_m.toLocaleString(i18n.locale(),{maximumFractionDigits:1})]));
  i18n.text($('coordinates'), () => i18n.t("centros_longitud_latitud_tacana_0_1_2", [earth.center.join(', '), region.name, planet.center.join(', ')]));
  $('terrain-link').href=`../comparador_3d/index.html?body=${body}`;
  $('terrain-link').hidden = id !== sources.selected_regions[body];
  await Promise.all([$('earth').decode(),$('planet').decode()]);
  $('status').hidden=true;$('comparison').hidden=false;
} catch(error) {
  console.error(error);i18n.text($('status'), () => error.message);$('retry').hidden=false;
}
