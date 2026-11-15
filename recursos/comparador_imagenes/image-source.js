// Local development adapter. The static exporter replaces this module.
export async function imagenRegional(body, id, view) {
  // Prefer the exported local assets: viewing an existing crop must not
  // depend on Python or make another request to the archive.
  const prepared = new URL('../github-pages/recursos/comparador_imagenes/', import.meta.url);
  try {
    const response = await fetch(new URL('regiones_manifest.json', prepared));
    if (response.ok) {
      const manifest = await response.json();
      const entry = manifest.regions[id];
      if (entry?.body === body && entry.metadata) {
        const metadata = await fetch(new URL(entry.metadata, prepared));
        if (metadata.ok) {
          const data = await metadata.json();
          if (view !== 'analysis' || data.window_side_km === 12) {
            data.file = new URL(data.file, prepared).href;
            return data;
          }
        }
      }
    }
  } catch { /* The local exporter may not have run yet. */ }
  const service = new URL(location.origin);
  if (service.port === '5500') service.port = '8000';
  const endpoint = new URL('/api/region-image', service);
  endpoint.search = new URLSearchParams({ body, region: id, view });
  const response = await fetch(endpoint);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'No se pudo obtener el recorte.');
  data.file = new URL(`/recursos/comparador_imagenes/${data.file}`, service).href;
  return data;
}
