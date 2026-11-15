export async function imagenRegional(body, id) {
  const base = new URL('./', import.meta.url);
  const response = await fetch(new URL('regiones_manifest.json', base));
  if (!response.ok) throw new Error('No se pudo cargar el catálogo de imágenes.');
  const manifest = await response.json();
  const entry = manifest.regions[id];
  if (!entry || entry.body !== body) throw new Error('Región no encontrada.');
  if (!entry.metadata) throw new Error(entry.message || 'La fuente no ofrece una imagen disponible de esta región.');
  const metadata = await fetch(new URL(entry.metadata, base));
  if (!metadata.ok) throw new Error('No se pudo cargar la imagen de esta región.');
  const data = await metadata.json();
  data.file = new URL(data.file, base).href;
  return data;
}
