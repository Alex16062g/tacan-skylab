const body = new URLSearchParams(location.search).get('body') === 'MARS' ? 'MARS' : 'MOON';
const name = body === 'MOON' ? 'Luna' : 'Marte';
document.getElementById('title').textContent = `Catálogo de ${name}`;
document.title = `Catálogo de ${name} | Tacaná skylab`;
const file = body.toLowerCase() + '.json';
document.getElementById('download').href = file;
document.getElementById('scores').href = `../comparacion_tacana/similitud_catalogo_${body.toLowerCase()}.json`;
const status = document.getElementById('status');
const rows = document.getElementById('rows');
const previous = document.getElementById('previous');
const next = document.getElementById('next');
const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const number = value => Number.isFinite(value) ? value.toLocaleString('es-MX', { maximumFractionDigits: 3 }) : 'Sin dato';
let features = [], filtered = [], page = 0, profiles = {};
const range = s => s ? `${number(s.min)}–${number(s.max)}` : 'Sin observaciones';
document.getElementById('conditions-download').href = `condiciones_${body.toLowerCase()}.json`;
const size = 50;
function render() {
  const start = page * size;
  rows.replaceChildren();
  for (const feature of filtered.slice(start, start + size)) {
    const row = document.createElement('tr');
    const th = document.createElement('th'); th.scope = 'row';
    const link = document.createElement('a'); link.textContent = feature.name;
    link.href = `./condiciones.html?body=${body}&region=${encodeURIComponent(feature.id)}`;
    const image = document.createElement('a'); image.textContent = 'Imagen';
    image.href = `../comparador_imagenes/index.html?body=${body}&region=${encodeURIComponent(feature.id)}`;
    th.append(link, document.createElement('br'), image); row.append(th);
    const profile = profiles[feature.conditions?.profile];
    const condition = key => profile?.conditions.find(c => c.variable === key)?.planetary;
    for (const value of [range(condition('surface_day')), range(condition('surface_night')), range(condition('pressure')),
      number(condition('gravity')?.mean), number(condition('solar_flux')?.mean), number(condition('day_length')?.mean),
      `${feature.conditions?.observation_types_available ?? 0} / 4`, number(feature.global_similarity?.percent),
      feature.feature_type, number(feature.latitude_deg), number(feature.longitude_east_deg),
      number(feature.global_terrain_context?.center_elevation_m), number(feature.global_terrain_context?.slope_10km_deg)]) {
      const td = document.createElement('td'); td.textContent = value ?? 'Sin dato'; row.append(td);
    }
    rows.append(row);
  }
  status.textContent = filtered.length
    ? `${number(filtered.length)} lugares · Mostrando ${number(start + 1)}–${number(Math.min(start + size, filtered.length))} de ${number(features.length)} catalogados`
    : 'No hay lugares que coincidan con tu búsqueda.';
  document.getElementById('page-number').textContent = filtered.length ? `Página ${page + 1} de ${Math.ceil(filtered.length / size)}` : 'Sin resultados';
  previous.disabled = page === 0; next.disabled = (page + 1) * size >= filtered.length;
  document.querySelector('.table-wrapper').scrollTop = 0;
}
document.getElementById('search-form').addEventListener('submit', event => {
  event.preventDefault();
  const query = normalize(document.getElementById('query').value.trim());
  filtered = features.filter(f => normalize(`${f.name} ${f.feature_type}`).includes(query));
  page = 0; render();
});
previous.addEventListener('click', () => { page--; render(); });
next.addEventListener('click', () => { page++; render(); });
try {
  const [response, conditionsResponse] = await Promise.all([fetch(file), fetch(`condiciones_${body.toLowerCase()}.json`)]);
  if (!conditionsResponse.ok) throw new Error('Condiciones no disponibles');
  profiles = (await conditionsResponse.json()).profiles;
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data.features)) throw new Error('Formato inesperado');
  features = data.features.sort((a, b) => a.name.localeCompare(b.name, 'es') || a.id.localeCompare(b.id)); filtered = features;
  document.getElementById('search-button').disabled = false; render();
} catch (error) {
  status.textContent = 'No se pudo cargar el catálogo. Recarga la página para intentarlo de nuevo.';
  console.error(error);
}
