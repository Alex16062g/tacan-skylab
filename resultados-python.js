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
      throw new Error(`Formato inesperado en ${archivo}`);
    }
    return [nombre, datos];
  }));
  const nuevosResultados = Object.fromEntries(entradas);
  nuevosResultados.condiciones = Object.fromEntries(await Promise.all(['MOON', 'MARS'].map(async body => {
    const response = await fetch(new URL(`./recursos/catalogo_regiones/condiciones_${body.toLowerCase()}.json`, import.meta.url), { cache: 'no-store' });
    if (!response.ok) throw new Error(`Condiciones ${body}: HTTP ${response.status}`);
    return [body, await response.json()];
  })));
  const ubicaciones = await fetch(new URL('./img/regiones-localizacion.json', import.meta.url));
  if (!ubicaciones.ok) throw new Error('No se pudieron cargar las ubicaciones de las regiones.');
  nuevosResultados.ubicaciones = await ubicaciones.json();
  resultadosPython = nuevosResultados;
  window.resultadosPython = resultadosPython;
  return resultadosPython;
}

const numero = valor => Number.isFinite(valor)
  ? valor.toLocaleString('es-MX', { maximumFractionDigits: 3 }) : 'No disponible';
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
  panel.innerHTML = `
    <label class="comparison-label" for="region-${body}">Región</label>
    <select class="comparison-region" id="region-${body}" name="region-${body}"></select>
    <div class="similarity-summary"></div>
    <section class="comparison-conditions" aria-label="Condiciones ambientales"></section>
    <p class="comparison-reason"></p>
    <div class="comparison-values"></div>`;
  const cabecera = panel.closest('figure').querySelector('figcaption');
  if (!cabecera.querySelector('.comparison-close')) {
    const cerrar = document.createElement('button');
    cerrar.type = 'button'; cerrar.className = 'comparison-close';
    cerrar.setAttribute('aria-label', 'Cerrar comparaciones'); cerrar.textContent = '×';
    cerrar.addEventListener('click', cerrarComparaciones);
    const acciones = document.createElement('div'); acciones.className = 'comparison-actions';
    const comparar = document.createElement('button');
    comparar.type = 'button'; comparar.className = 'comparison-image-button';
    comparar.setAttribute('aria-label', `Comparar imágenes de Tacaná y ${body === 'MOON' ? 'Luna' : 'Marte'}`);
    comparar.title = 'Comparar imágenes'; comparar.setAttribute('aria-haspopup', 'dialog');
    comparar.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 2v20M8 9l-3 3 3 3m8-6 3 3-3 3"/></svg>';
    comparar.addEventListener('click', () => abrirImagenes(body));
    acciones.append(comparar, cerrar); cabecera.append(acciones);
  }
  if (!elegida) {
    panel.querySelector('.comparison-reason').textContent = 'Comparación no disponible.';
    return;
  }
  regionesSeleccionadas[body] = elegida.region;
  const selector = panel.querySelector('.comparison-region');
  for (const region of opciones) {
    const option = document.createElement('option'); option.value = region.region;
    option.textContent = `${region.name} · ${region.primary.similarity_percent.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %`;
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
  botonImagen.title = `Comparar imágenes de Tacaná y ${elegida.name}`;
  const porcentaje = valor => valor.toLocaleString('es-MX', { maximumFractionDigits: 1, minimumFractionDigits: 1 });
  const resumen = panel.querySelector('.similarity-summary');
  const puntuacion = document.createElement('strong');
  puntuacion.className = 'similarity-score';
  puntuacion.textContent = `${porcentaje(elegida.primary.similarity_percent)} / 100`;
  const alcance = document.createElement('p'); alcance.textContent = 'Índice de pendiente y desnivel';
  const cobertura = document.createElement('p'); cobertura.className = 'comparison-note';
  cobertura.textContent = `Entorno de 12 km · ${seleccion.candidate_count.toLocaleString("es-MX")} lugares comparados`;
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
    svg.setAttribute('aria-label', `Ubicación de ${ubicacion.label}. Recuadro ampliado, no a escala.`);
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
    caption.textContent = `${titulo} (${unidad}) · Similitud ${porcentaje(componente.similarity_percent)} %`;
    wrapper.setAttribute('aria-labelledby', caption.id);
    const head = document.createElement('thead');
    const headings = document.createElement('tr');
    for (const label of ['Lugar', 'Mín.', 'Máx.']) {
      const th = document.createElement('th'); th.scope = 'col'; th.textContent = label;
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
      ['En común', componente.shared_range]
    ]) {
      const row = document.createElement('tr');
      const th = document.createElement('th'); th.scope = 'row'; th.textContent = label;
      row.append(th);
      for (let i = 0; i < 2; i++) {
        const td = document.createElement('td');
        td.textContent = values ? numero(values[i]) : '—';
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
    modal.innerHTML = '<div class="image-dialog-heading"><h2 id="image-comparison-title"></h2><form method="dialog"><button autofocus aria-label="Cerrar comparador">×</button></form></div><iframe title="Comparador de imágenes satelitales"></iframe>';
    document.body.append(modal);
    modal.addEventListener('close', () => modal.querySelector('iframe').removeAttribute('src'));
  }
  modal.querySelector('h2').textContent = `Tacaná · ${body === 'MOON' ? 'Luna' : 'Marte'}`;
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
  const rango = s => s ? (s.min === s.max ? formato(s.min) : `${formato(s.min)} – ${formato(s.max)}`) : 'Sin datos';
  for (const condicion of coincidencias) {
    const wrap = document.createElement('div'); wrap.className = 'comparison-table-wrap';
    wrap.tabIndex = 0; wrap.setAttribute('role', 'region');
    const table = document.createElement('table'); table.className = 'comparison-table condition-table';
    const caption = document.createElement('caption');
    caption.id = `condition-${body}-${condicion.variable}`;
    caption.textContent = `${condicion.label} (${condicion.unit})`;
    wrap.setAttribute('aria-labelledby', caption.id);
    const head = document.createElement('thead');
    head.innerHTML = '<tr><th scope="col">Lugar</th><th scope="col">Valor / rango</th></tr>';
    const tbody = document.createElement('tbody');
    for (const [label, valor] of [
      [condicion.status === 'body_reference' ? 'Tierra' : 'Tacaná', rango(condicion.reference)],
      [body === 'MOON' ? 'Luna' : 'Marte', rango(condicion.planetary)],
      ['En común', rango({ min: condicion.range_overlap[0], max: condicion.range_overlap[1] })]
    ]) {
      const row = document.createElement('tr'), th = document.createElement('th'), td = document.createElement('td');
      th.scope = 'row'; th.textContent = label; td.textContent = valor;
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
    estado.textContent = 'Cargando comparaciones…'; p.append(estado);
  });
  solicitud = cargarResultadosPython();
  try {
    await solicitud;
    paneles.forEach(construirPanel);
  } catch (error) {
    paneles.forEach(p => {
      p.replaceChildren();
      const estado = document.createElement('p'); estado.setAttribute('role', 'status');
      estado.textContent = 'No se pudo cargar la comparación. Inténtalo de nuevo.';
      const reintentar = document.createElement('button'); reintentar.type = 'button';
      reintentar.textContent = 'Reintentar';
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


