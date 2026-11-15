import * as i18n from './idiomas/i18n.js';
const base = new URL('./recursos/comparacion_tacana/', import.meta.url);

// Datos numéricos originales de Python, disponibles para otras funciones.
export let resultadosPython = null;

export async function cargarResultadosPython() {
  const archivos = {
    anovaTemperatura: 'temperatura_anova.json',
    comparacionesTemperatura: 'temperatura_comparaciones.json',
    referenciaTacana: 'temperatura_resumen_tacana.json',
    anovaRelieve: 'anova.json',
    comparacionesRelieve: 'comparaciones.json',
    bloquesRelieve: 'bloques.json',
    similitud: 'similitud_catalogo_resumen.json',
    metodologiaTemperatura: 'temperatura_metodologia.json'
  };
  const entradas = await Promise.all(Object.entries(archivos).map(async ([nombre, archivo]) => {
    const respuesta = await fetch(new URL(archivo, base), { cache: 'no-store' });
    if (!respuesta.ok) throw new Error(`${archivo}: HTTP ${respuesta.status}`);
    const datos = await respuesta.json();
    if (!['metodologiaTemperatura', 'similitud'].includes(nombre) && !Array.isArray(datos)) {
      throw new Error(i18n.t("formato_inesperado_en_0", [archivo]));
    }
    return [nombre, datos];
  }));
  const nuevosResultados = Object.fromEntries(entradas);
  nuevosResultados.condiciones = Object.fromEntries(await Promise.all(['MOON', 'MARS'].map(async body => {
    const response = await fetch(new URL(`./recursos/catalogo_regiones/condiciones_${body.toLowerCase()}.json`, import.meta.url), { cache: 'no-store' });
    if (!response.ok) throw new Error(i18n.t("condiciones_0_http_1", [body, response.status]));
    return [body, await response.json()];
  })));
  const ubicaciones = await fetch(new URL('./img/regiones-localizacion.json', import.meta.url));
  if (!ubicaciones.ok) throw new Error(i18n.t("no_se_pudieron_cargar_las_ubicaciones_de_las_regiones"));
  nuevosResultados.ubicaciones = await ubicaciones.json();
  resultadosPython = nuevosResultados;
  window.resultadosPython = resultadosPython;
  return resultadosPython;
}

const numero = valor => Number.isFinite(valor)
  ? valor.toLocaleString(i18n.locale(), { maximumFractionDigits: 3 }) : i18n.t("no_disponible");
const rangoCompartidoValido = rango => Array.isArray(rango) && rango.length === 2
  && rango.every(Number.isFinite) && rango[0] <= rango[1];
const paneles = [...document.querySelectorAll('.planet-comparison')];
let solicitud = null;
let activador = null;
const regionesSeleccionadas = {};

function cerrarComparaciones() {
  paneles.forEach(p => { p.hidden = true; });
  document.querySelector('.planet-map-previews').classList.remove('comparisons-open');
  document.querySelector('.planet-map-previews').hidden = true;
  activador?.setAttribute('aria-expanded', 'false');
  activador?.focus();
}

function construirPanel(panel) {
  const body = panel.dataset.body;
  const seleccion = resultadosPython.similitud.selections[body];
  const opciones = (seleccion.matching_regions ?? resultadosPython.similitud.regions.filter(r => r.body === body))
    .filter(r => r.primary?.similarity_percent > 80)
    .sort((a, b) => b.primary.similarity_percent - a.primary.similarity_percent);
  const elegida = opciones.find(r => r.region === regionesSeleccionadas[body]) ?? opciones[0];
  i18n.html(panel, `
<label class="comparison-label" data-i18n="region" for="region-${body}">Region</label>
<select class="comparison-region" id="region-${body}" name="region-${body}"></select>
<div class="similarity-summary"></div>
<section aria-label="Environmental conditions" class="comparison-conditions" data-i18n-attrs="aria-label:condiciones_ambientales"></section>
<p class="comparison-reason"></p>
<div class="comparison-values"></div>`);
  const cabecera = panel.closest('figure').querySelector('figcaption');
  if (!cabecera.querySelector('.comparison-close')) {
    const cerrar = document.createElement('button');
    cerrar.type = 'button'; cerrar.className = 'comparison-close';
    i18n.attr(cerrar, 'aria-label', () => i18n.t("cerrar_comparaciones")); i18n.text(cerrar, () => '×');
    cerrar.addEventListener('click', cerrarComparaciones);
    const acciones = document.createElement('div'); acciones.className = 'comparison-actions';
    const comparar = document.createElement('button');
    comparar.type = 'button'; comparar.className = 'comparison-image-button';
    i18n.attr(comparar, 'aria-label', () => i18n.t("comparar_imagenes_de_tacana_y_0", [body === 'MOON' ? i18n.t("luna") : i18n.t("marte")]));
    i18n.attr(comparar, "title", () => i18n.t("comparar_imagenes")); comparar.setAttribute('aria-haspopup', 'dialog');
    i18n.html(comparar, '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 2v20M8 9l-3 3 3 3m8-6 3 3-3 3"/></svg>');
    comparar.addEventListener('click', () => abrirImagenes(body));
    acciones.append(comparar, cerrar); cabecera.append(acciones);
  }
  if (!elegida) {
    i18n.text(panel.querySelector('.comparison-reason'), () => i18n.t("comparacion_no_disponible"));
    return;
  }
  regionesSeleccionadas[body] = elegida.region;
  const selector = panel.querySelector('.comparison-region');
  for (const region of opciones) {
    const option = document.createElement('option'); option.value = region.region;
    i18n.text(option, () => `${region.name} · ${region.primary.similarity_percent.toLocaleString(i18n.locale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %`);
    selector.append(option);
  }
  selector.value = elegida.region;
  selector.addEventListener('change', () => {
    regionesSeleccionadas[body] = selector.value;
    construirPanel(panel);
    panel.querySelector('.comparison-region').focus({ preventScroll: true });
  });
  const botonImagen = cabecera.querySelector('.comparison-image-button');
  botonImagen.disabled = false;
  i18n.attr(botonImagen, "title", () => i18n.t("comparar_imagenes_de_tacana_y_0", [elegida.name]));
  const porcentaje = valor => valor.toLocaleString(i18n.locale(), { maximumFractionDigits: 1, minimumFractionDigits: 1 });
  const resumen = panel.querySelector('.similarity-summary');
  const puntuacion = document.createElement('strong');
  puntuacion.className = 'similarity-score';
  i18n.text(puntuacion, () => `${porcentaje(elegida.primary.similarity_percent)} / 100`);
  const alcance = document.createElement('p'); i18n.text(alcance, () => i18n.t("indice_de_pendiente_y_desnivel"));
  const cobertura = document.createElement('p'); cobertura.className = 'comparison-note';
  i18n.text(cobertura, () => i18n.t("entorno_de_12_km_0_lugares_comparados", [seleccion.candidate_count.toLocaleString(i18n.locale())]));
  resumen.append(puntuacion, alcance, cobertura);
  const ubicacion = elegida.location;
  mostrarCondiciones(panel, body, ubicacion);
  const svg = panel.closest('figure').querySelector('.region-locator');
  svg.replaceChildren();
  if (ubicacion) {
    const x = (ubicacion.longitude + 180) * 2;
    const y = (90 - ubicacion.latitude) * 2;
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    // Recuadro localizador ampliado: no representa la extensión de la muestra.
    for (const [key, value] of Object.entries({ x: Math.max(3, Math.min(669, x - 24)), y: Math.max(3, Math.min(321, y - 18)), width: 48, height: 36, rx: 4 })) {
      rect.setAttribute(key, value);
    }
    svg.append(rect);
    i18n.attr(svg, 'aria-label', () => i18n.t("ubicacion_de_0_recuadro_ampliado_no_a_escala", [ubicacion.label]));
    svg.removeAttribute('hidden');

  }
  panel.querySelector('.comparison-reason').remove();
  const destino = panel.querySelector('.comparison-values');
  const componentes = elegida.primary.features.filter(c => rangoCompartidoValido(c.shared_range)).sort((a, b) =>
    b.weight - a.weight || b.similarity_percent - a.similarity_percent);
  for (const componente of componentes) {
    const { variable, label: titulo, unit: unidad } = componente;
    const wrapper = document.createElement('div');
    wrapper.className = 'comparison-table-wrap';
    wrapper.tabIndex = 0;
    wrapper.setAttribute('role', 'region');
    const table = document.createElement('table');
    table.className = 'comparison-table';
    const caption = document.createElement('caption');
    caption.id = `comparison-${body}-${variable}`;
    i18n.text(caption, () => i18n.t("0_1_similitud_2", [titulo, unidad, porcentaje(componente.similarity_percent)]));
    wrapper.setAttribute('aria-labelledby', caption.id);
    const head = document.createElement('thead');
    const headings = document.createElement('tr');
    for (const label of [i18n.t("lugar"), i18n.t("min"), i18n.t("max")]) {
      const th = document.createElement('th'); th.scope = 'col'; i18n.text(th, () => label);
      headings.append(th);
    }
    head.append(headings);
    const tbody = document.createElement('tbody');
    const reference = resultadosPython.similitud.reference.samples[String(elegida.primary.grid_spacing_m)][variable];
    const range = samples => samples?.length && samples.every(Number.isFinite)
      ? [Math.min(...samples), Math.max(...samples)] : null;
    for (const [label, values] of [
      ['Tacaná', range(reference)],
      [elegida.name, range(componente.samples)],
      [i18n.t("en_comun"), componente.shared_range]
    ]) {
      const row = document.createElement('tr');
      const th = document.createElement('th'); th.scope = 'row'; i18n.text(th, () => label);
      row.append(th);
      for (let i = 0; i < 2; i++) {
        const td = document.createElement('td');
        i18n.text(td, () => values ? numero(values[i]) : '—');
        row.append(td);
      }
      tbody.append(row);
    }
    table.append(caption, head, tbody);
    wrapper.append(table); destino.append(wrapper);
  }

}

function abrirImagenes(body) {
  const regionId = regionesSeleccionadas[body];
  let modal = document.getElementById('image-comparison-dialog');
  if (!modal) {
    modal = document.createElement('dialog'); modal.id = 'image-comparison-dialog';
    modal.setAttribute('aria-labelledby', 'image-comparison-title');
    i18n.html(modal, "<div class=\"image-dialog-heading\"><h2 id=\"image-comparison-title\"></h2><form method=\"dialog\"><button aria-label=\"Close comparison\" autofocus=\"\" data-i18n-attrs=\"aria-label:cerrar_comparador\">×</button></form></div><iframe data-i18n-attrs=\"title:comparador_de_imagenes_satelitales\" title=\"Satellite image comparison\"></iframe>");
    document.body.append(modal);
    modal.addEventListener('close', () => modal.querySelector('iframe').removeAttribute('src'));
  }
  i18n.text(modal.querySelector('h2'), () => `Tacaná · ${body === 'MOON' ? i18n.t("luna") : i18n.t("marte")}`);
  modal.querySelector('iframe').src = new URL(`./recursos/comparador_imagenes/index.html?body=${body}&region=${encodeURIComponent(regionId)}&embed=1`, import.meta.url);
  modal.showModal();
}

function mostrarCondiciones(panel, body, ubicacion) {
  const destino = panel.querySelector('.comparison-conditions');
  const lat = Math.min(60, Math.floor(ubicacion.latitude / 30) * 30);
  const lon = Math.floor(((ubicacion.longitude % 360 + 360) % 360) / 60) * 60;
  const perfil = resultadosPython.condiciones[body].profiles[`lat_${lat}_${lat + 30}_lon_${lon}_${lon + 60}`];
  const coincidencias = (perfil?.conditions ?? []).filter(c =>
    c.reference && c.planetary && rangoCompartidoValido(c.range_overlap));
  if (!coincidencias.length) { destino.hidden = true; return; }
  const formato = n => Number.isFinite(n) && n !== 0 && Math.abs(n) < .001 ? n.toExponential(2) : numero(n);
  const rango = s => s ? (s.min === s.max ? formato(s.min) : `${formato(s.min)} – ${formato(s.max)}`) : i18n.t("sin_datos");
  for (const condicion of coincidencias) {
    const wrap = document.createElement('div'); wrap.className = 'comparison-table-wrap';
    wrap.tabIndex = 0; wrap.setAttribute('role', 'region');
    const table = document.createElement('table'); table.className = 'comparison-table condition-table';
    const caption = document.createElement('caption');
    caption.id = `condition-${body}-${condicion.variable}`;
    i18n.text(caption, () => `${condicion.label} (${condicion.unit})`);
    wrap.setAttribute('aria-labelledby', caption.id);
    const head = document.createElement('thead');
    i18n.html(head, "<tr><th data-i18n=\"lugar\" scope=\"col\">Location</th><th data-i18n=\"valor_rango\" scope=\"col\">Value / range</th></tr>");
    const tbody = document.createElement('tbody');
    for (const [label, valor] of [
      [condicion.status === 'body_reference' ? i18n.t("tierra") : 'Tacaná', rango(condicion.reference)],
      [body === 'MOON' ? i18n.t("luna") : i18n.t("marte"), rango(condicion.planetary)],
      [i18n.t("en_comun"), rango({ min: condicion.range_overlap[0], max: condicion.range_overlap[1] })]
    ]) {
      const row = document.createElement('tr'), th = document.createElement('th'), td = document.createElement('td');
      th.scope = 'row'; i18n.text(th, () => label); i18n.text(td, () => valor);
      row.append(th, td); tbody.append(row);
    }
    table.append(caption, head, tbody); wrap.append(table);
    destino.append(wrap);
  }
}

export async function abrirComparaciones(boton) {
  activador = boton;
  activador?.setAttribute('aria-expanded', 'true');
  document.querySelector('.planet-map-previews').classList.add('comparisons-open');
  document.querySelector('.planet-map-previews').hidden = false;
  paneles.forEach(p => { p.hidden = false; });
  if (resultadosPython) {
    paneles.forEach(p => { if (!p.querySelector('.comparison-region')) construirPanel(p); });
    return;
  }
  if (solicitud) return;
  paneles.forEach(p => {
    p.replaceChildren();
    const estado = document.createElement('p');
    estado.setAttribute('role', 'status');
    i18n.text(estado, () => i18n.t("cargando_comparaciones")); p.append(estado);
  });
  solicitud = cargarResultadosPython();
  try {
    await solicitud;
    paneles.forEach(construirPanel);
  } catch (error) {
    paneles.forEach(p => {
      p.replaceChildren();
      const estado = document.createElement('p'); estado.setAttribute('role', 'status');
      i18n.text(estado, () => i18n.t("no_se_pudo_cargar_la_comparacion_intentalo_de_nuevo"));
      const reintentar = document.createElement('button'); reintentar.type = 'button';
      i18n.text(reintentar, () => i18n.t("reintentar"));
      reintentar.addEventListener('click', () => abrirComparaciones(activador));
      p.append(estado, reintentar);
    });
    console.error(error);
  } finally { solicitud = null; }
}

document.querySelector('.planet-map-previews').addEventListener('keydown', e => {
  if (e.key === 'Escape') { e.stopPropagation(); cerrarComparaciones(); }
});
window.cargarResultadosPython = cargarResultadosPython;


