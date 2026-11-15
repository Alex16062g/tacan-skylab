import * as i18n from '../../idiomas/i18n.js';
export async function imagenRegional(body, id) {
  const base = new URL('./', import.meta.url);
  const response = await fetch(new URL('regiones_manifest.json', base));
  if (!response.ok) throw new Error(i18n.t('no_se_pudo_cargar_el_catalogo_de_imagenes'));
  const manifest = await response.json();
  const entry = manifest.regions[id];
  if (!entry || entry.body !== body) throw new Error(i18n.t('region_no_encontrada_punto'));
  if (!entry.metadata) throw new Error(i18n.t(entry.status === 'unavailable' ? 'imagen_no_disponible_edicion' : 'imagen_pendiente'));
  const metadata = await fetch(new URL(entry.metadata, base));
  if (!metadata.ok) throw new Error(i18n.t('no_se_pudo_cargar_la_imagen_de_esta_region'));
  const data = await metadata.json();
  data.file = new URL(data.file, base).href;
  return data;
}
