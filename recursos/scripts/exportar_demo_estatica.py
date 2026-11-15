"""Package a standalone GitHub Pages demo from local scientific results and crops."""
import argparse,json,shutil,hashlib
from pathlib import Path
from PIL import Image
from imagenes_catalogo import ROOT,OUT,LEGACY_OUT,catalog

DEST=ROOT/'recursos/github-pages'
STATIC_ADAPTER='''export async function imagenRegional(body, id) {
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
'''

def copy(relative):
    source=ROOT/relative;target=DEST/relative
    if target.exists() and target.stat().st_size==source.stat().st_size and target.stat().st_mtime_ns==source.stat().st_mtime_ns:
        return
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-incomplete',action='store_true',help='Local preview only; final package requires every region processed.')
    args=parser.parse_args();DEST.mkdir(parents=True,exist_ok=True)
    for name in ['index.html','style.css','mapa.js','resultados-python.js','ecuaciones.md','REFERENCIAS.md']:copy(name)
    for folder in ['img','datos','recursos/catalogo_regiones','recursos/comparacion_tacana','recursos/comparador_3d','recursos/sismos']:
        for source in (ROOT/folder).rglob('*'):
            if folder=='datos' and source.suffix=='.csv':continue
            if source.is_file() and (source.suffix in ['.html','.js','.css','.json','.geojson','.md','.csv','.txt'] or source.name in ['LICENSE','COPYING','NOTICE'] or folder=='img'):
                copy(source.relative_to(ROOT))
    # The public demo uses only the filtered GeoJSON. Keep the original
    # national and Chiapas CSV files locally, outside the published bundle.
    for name in ['SSNMX_catalogo_20200101_20261114.csv','SSNMX_catalogo_20200101_20261114_CHIS.csv']:
        old=DEST/'datos'/name
        if old.is_file():old.unlink()
    for name in ['index.html','style.css','viewer.js','fuentes.json','tacana.jpg','moon.png','mars.png']:
        copy('recursos/comparador_imagenes/'+name)
    copy('recursos/LICENCIAS_DATOS.md')
    # The climate page links to this observed series and its provenance.
    copy('recursos/datos/tacana_ambiente/power_daily.json')
    copy('recursos/datos/tacana_ambiente/source.json')
    comparator=DEST/'recursos/comparador_imagenes';images=comparator/'regiones_catalogo';images.mkdir(exist_ok=True)
    (comparator/'image-source.js').write_text(STATIC_ADAPTER,encoding='utf-8')
    available={}
    for folder in [LEGACY_OUT,OUT]:
        for path in folder.glob('*.json'):
            if path.name=='bulk-status.json':continue
            try:
                data=json.loads(path.read_text(encoding='utf-8'))
                if data.get('view')=='full' and (folder/Path(data['file']).name).is_file():available[data['region']]=(data,folder/Path(data['file']).name)
            except (ValueError,KeyError):continue
    bulk=json.loads((OUT/'bulk-status.json').read_text(encoding='utf-8')) if (OUT/'bulk-status.json').exists() else {'regions':{}}
    # The initial comparisons already have genuine 12 km crops. Reuse only
    # their exact region IDs; never assign these images to another location.
    originals=json.loads((ROOT/'recursos/comparador_imagenes/fuentes.json').read_text(encoding='utf-8'))
    for body,ident in originals['selected_regions'].items():
        if ident in available:continue
        f=catalog(body)[ident];data=dict(originals['images'][body])
        data.update(region=ident,body=body,name=f['name'],window_side_km=originals['window_side_approx_km'],view='analysis',
            diameter_km=f.get('diameter_km'),extent_basis='Existing 12 km analysis crop, not full feature extent',
            display_source_resolution_m=data.get('served_pixel_latitude_m',data['native_resolution_m']),coverage_fraction=None,
            similarity_percent=(f.get('global_similarity') or {}).get('percent'))
        available[ident]=(data,ROOT/'recursos/comparador_imagenes'/data['file'])
    regions={};ready=0;missing=[];unavailable=[]
    for body in ['MOON','MARS']:
        for ident,f in catalog(body).items():
            entry=dict(body=body,name=f['name']);regions[ident]=entry
            if ident not in available:
                state=bulk['regions'].get(ident,{})
                if state.get('status')=='unavailable':
                    unavailable.append(ident);entry['message']='La imagen no está disponible en esta edición. Consulta el estado de las fuentes.'
                else:missing.append(ident);entry['message']='Imagen pendiente de preparación.'
                entry['status']=state.get('status','pending');continue
            original,source=available[ident];data=dict(original)
            if 'planetarymaps.usgs.gov' in data.get('source_url',''):
                data['publication_year']=2013
                data['product_page']='https://astrogeology.usgs.gov/search/map/moon_lro_lroc_wac_global_morphology_mosaic_100m'
                data['use_constraints']='Public domain; please cite authors'
            name=source.stem;target=images/f'{name}.webp'
            if not target.exists():
                with Image.open(source) as image:image.save(target,'WEBP',quality=85,method=6)
            data['original_png_sha256']=data['sha256'];data['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
            data['file']=f'regiones_catalogo/{target.name}';data['display_encoding']='WebP quality 85; visualisation only; scientific calculations unchanged'
            (images/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            entry.update(status='ready',metadata=f'regiones_catalogo/{name}.json');ready+=1
    manifest=dict(total=len(regions),ready=ready,unavailable=len(unavailable),pending=len(missing),regions=regions)
    (comparator/'regiones_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (DEST/'.nojekyll').touch()
    size=sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file())
    from preparar_imagenes_estaticas import html_priority
    priority=html_priority()
    priority_status=dict(total=len(priority),ready=sum(regions[ident]['status']=='ready' for _,ident in priority),pending=[ident for _,ident in priority if regions[ident]['status']!='ready'])
    report=dict(total=len(regions),ready=ready,pending=missing,unavailable=unavailable,size_bytes=size,within_pages_1GB=size<1_000_000_000,complete=not missing and not unavailable)
    report['html_priority']=priority_status
    report['html_images_complete']=priority_status['ready']==priority_status['total']
    (DEST/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    printable={k:v if not isinstance(v,list) else len(v) for k,v in report.items()}
    printable['html_priority']={k:len(v) if isinstance(v,list) else v for k,v in priority_status.items()}
    print(json.dumps(printable),flush=True)
    if not args.allow_incomplete and (missing or unavailable):raise SystemExit('Images remain unavailable or pending; inspect build-report.json before publishing.')
    if size>=1_000_000_000:raise SystemExit('Package exceeds the GitHub Pages size limit.')

if __name__=='__main__':main()
