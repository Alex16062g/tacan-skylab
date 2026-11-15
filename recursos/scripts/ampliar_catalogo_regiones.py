"""Full named-feature inventory from IAU/USGS, enriched with NASA global context.

No local similarity score is inferred from sparse metadata or coarse global DEMs.
Run with --actualizar to refresh the official KMZ snapshots.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import hashlib
import json
import math
import re
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'recursos/datos/nomenclatura'
OUT = ROOT / 'recursos/catalogo_regiones'
URL = 'https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/{}_nomenclature_center_pts.kmz'
BODY = {'MOON': ('Luna', 1737400.), 'MARS': ('Marte', 3396000.)}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def number(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def read_features(body):
    with zipfile.ZipFile(RAW / f'{body}.kmz') as archive:
        root = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.kml'))))
    features = {}
    for point in root.findall('.//{*}Placemark'):
        attrs = {n.attrib['name']: n.text for n in point.findall('.//{*}SimpleData')}
        link = attrs.get('link', '').replace('http://', 'https://')
        match = re.search(r'/Feature/(\d+)', link)
        key = f'{body}:{match[1]}' if match else f'{body}:{point.attrib["id"]}'
        if key in features:
            if features[key]['official_attributes'] != attrs:
                raise ValueError(f'Conflicting records for {key}; do not silently merge.')
            features[key]['source_entries'].append(point.attrib['id'])
            continue
        features[key] = dict(id=key, body=body, name=point.findtext('{*}name'),
                             feature_id=int(match[1]) if match else None,
                             feature_type=attrs.get('type'), feature_code=attrs.get('code'),
                             latitude_deg=number(attrs.get('center_lat')),
                             longitude_east_deg=number(attrs.get('center_lon')),
                             diameter_km=number(attrs.get('diameter')),
                             approval=attrs.get('approval'), approval_date=attrs.get('approvaldt'),
                             source_url=link, source_entries=[point.attrib['id']], official_attributes=attrs)
    return list(features.values())


def sample(grid, lat, lon):
    """Bilinear interpolation, periodic longitude, clamped latitude (no pole wrap)."""
    height, width = grid.shape
    y = np.clip((90 - np.asarray(lat)) * height / 180 - .5, 0, height - 1)
    x = np.mod(np.asarray(lon), 360) * width / 360 - .5
    x0 = np.floor(x).astype(int); fraction = x - x0
    left = map_coordinates(grid, [y, x0 % width], order=1, mode='nearest', prefilter=False)
    right = map_coordinates(grid, [y, (x0 + 1) % width], order=1, mode='nearest', prefilter=False)
    return left * (1 - fraction) + right * fraction


def destination(lat, lon, east_m, north_m, radius):
    """Spherical geodesic offset; remains finite at the poles."""
    phi, lam = np.radians(lat), np.radians(lon)
    delta = math.hypot(east_m, north_m) / radius
    bearing = math.atan2(east_m, north_m)
    p = np.arcsin(np.clip(np.sin(phi)*math.cos(delta) + np.cos(phi)*math.sin(delta)*math.cos(bearing), -1, 1))
    l = lam + np.arctan2(math.sin(bearing)*math.sin(delta)*np.cos(phi), math.cos(delta)-np.sin(phi)*np.sin(p))
    return np.degrees(p), np.degrees(l) % 360


def enrich_global(body, features):
    if body == 'MOON':
        path = ROOT / 'recursos/datos/nasa/luna/global/ldem_16.tif'
        grid = np.asarray(Image.open(path), dtype=np.float32) * 1000
        grid = np.roll(grid, -grid.shape[1]//2, axis=1)
        source = 'https://svs.gsfc.nasa.gov/4720/'
        datum = 'Esfera lunar de radio 1737.4 km'
    else:
        path = ROOT / 'recursos/datos/nasa/marte/global/megt90n000fb.img'
        grid = np.asarray(np.memmap(path, dtype='>i2', shape=(5760,11520)), dtype=np.float32)
        source = 'https://pds-geosciences.wustl.edu/missions/mgs/megdr.html'
        datum = 'Areoide GMM3; consultar etiqueta MOLA'
    valid = [f for f in features if f['latitude_deg'] is not None and f['longitude_east_deg'] is not None]
    lat = np.array([f['latitude_deg'] for f in valid]); lon = np.array([f['longitude_east_deg'] for f in valid])
    radius = BODY[body][1]; step = 10000.
    center = sample(grid, lat, lon)
    patch = np.array([sample(grid, *destination(lat, lon, i*step, j*step, radius))
                      for j in range(-2,3) for i in range(-2,3)])
    gx = (patch[13] - patch[11]) / (2*step)
    gy = (patch[17] - patch[7]) / (2*step)
    slopes = np.degrees(np.arctan(np.hypot(gx, gy)))
    relief = np.percentile(patch,95,axis=0)-np.percentile(patch,5,axis=0)
    pixel_m = 2*math.pi*radius / grid.shape[0] / 2
    for i, f in enumerate(valid):
        f['global_terrain_context'] = dict(center_elevation_m=round(float(center[i]),3),
                slope_10km_deg=round(float(slopes[i]),5), relief_p95_p05_40km_m=round(float(relief[i]),3),
                native_latitude_pixel_m=round(pixel_m,2), vertical_reference=datum,
                covers_feature=False, sample_count=25,
                feature_smaller_than_nominal_pixel=f['diameter_km'] is not None and f['diameter_km']*1000<pixel_m,
                source_url=source, source_file=str(path.relative_to(ROOT)))
    return dict(source_file=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                source_url=source, features_with_context=len(valid))


def thermal_context(feature, temperatures):
    lat, lon = feature['latitude_deg'], feature['longitude_east_deg']
    if lat is None or lon is None:
        return []
    south = min(60, int(math.floor(lat/30))*30); west = int((lon%360)//60)*60
    sector = f'lat_{south}_{south+30}_lon_{west}_{west+60}'
    return [dict(phase=r['phase'], sector=sector, sector_mean_C=r['region_mean_C'], n_cells=r['n_cells'],
                 measurement_scope='Sector de 30 x 60 grados; no medición específica de este accidente geográfico')
            for r in temperatures if r['body']==feature['body'] and r['region']==sector]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--actualizar', action='store_true');args=parser.parse_args()
    RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    manifest_path = RAW/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    for body in BODY:
        path=RAW/f'{body}.kmz'
        if args.actualizar or not path.exists():
            response=requests.get(URL.format(body),timeout=(15,90));response.raise_for_status()
            payload=response.content
            import io
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                assert any(n.endswith('.kml') for n in z.namelist())
            path.write_bytes(payload)
            manifest[body]=dict(downloaded_utc=datetime.now(timezone.utc).isoformat(),last_modified=response.headers.get('Last-Modified'))
        manifest.setdefault(body,{})
        manifest[body].update(url=URL.format(body),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    save(manifest_path,manifest)
    temperatures=json.loads((ROOT/'recursos/comparacion_tacana/temperatura_comparaciones.json').read_text(encoding='utf-8'))
    all_features=[];summaries={};dem_sources={}
    for body in BODY:
        features=read_features(body)
        dem_sources[body]=enrich_global(body,features)
        for f in features:
            f['thermal_sector_context']=thermal_context(f,temperatures)
            f['local_similarity'] = dict(status='not_evaluated', percent=None,
                 reason='El DEM global y el contexto térmico no tienen la escala del índice local de Tacaná.')
        features.sort(key=lambda f:(f['name'].casefold(),f['id']))
        summaries[body]=dict(named_features=len(features),source_entries=sum(len(f['source_entries']) for f in features),
                            exact_duplicates_merged=sum(len(f['source_entries'])-1 for f in features),
                            with_global_terrain=sum('global_terrain_context' in f for f in features),
                            with_thermal_sector_context=sum(bool(f['thermal_sector_context']) for f in features),
                            feature_types=dict(sorted(Counter(f['feature_type'] for f in features).items())),
                            full_catalog_url=f'./recursos/catalogo_regiones/{body.lower()}.json')
        save(OUT/f'{body.lower()}.json',dict(body=body,summary=summaries[body],features=features))
        all_features.extend(features)
        print(body,summaries[body]['named_features'],'features',summaries[body]['with_global_terrain'],'with NASA global context',flush=True)
    metadata=dict(generated_utc=datetime.now(timezone.utc).isoformat(),
        scope='Todos los accidentes con nombre de los KMZ oficiales de Luna y Marte; no incluye todos los lugares sin nombre ni nombres informales.',
        nomenclature_authority='IAU WGPSN / USGS Gazetteer of Planetary Nomenclature',
        official_catalog='https://planetarynames.wr.usgs.gov/GIS_Downloads',
        coordinate_system='Latitud planetocéntrica; longitud positiva al este. KMZ Moon LOLA2011; Mars MDIM2.1.',
        sources=manifest,global_dem_sources=dem_sources,bodies=summaries,
        methods=dict(elevation='Interpolación bilineal en el punto de referencia del catálogo, no promedio de toda la región.',
                     slope='Diferencias centrales en cuatro destinos geodésicos a 10 km; derivado global descriptivo, no pendiente local a 100 m.',
                     relief='P95-P05 de 25 muestras separadas 10 km en una cuadrícula geodésica local de 40 km de lado.',
                     temperatures='Asociación contextual al sector geográfico existente; no se atribuye su media al accidente individual.'),
        limitations=['Los centros del catálogo no son polígonos ni delimitaciones geológicas.',
                     'Los archivos globales incluyen interpolación; 25 muestras no equivalen a 25 mediciones independientes.',
                     'La ventana de contexto puede exceder el tamaño del accidente; se conservan también los accidentes pequeños.',
                     'Los valores globales no se mezclan con los bloques locales de 1 km para asignar porcentajes.',
                     'Las regiones de estudio Connecting Ridge y Site04 son recortes de investigación, no sinónimos exactos de accidentes IAU.'])
    save(OUT/'resumen.json',metadata)
    save(OUT/'regiones.geojson',dict(type='FeatureCollection',features=[dict(type='Feature',id=f['id'],
            geometry=dict(type='Point',coordinates=[((f['longitude_east_deg']+180)%360)-180,f['latitude_deg']]),
            properties={k:f[k] for k in ['id','body','name','feature_type','diameter_km','source_url']})
            for f in all_features if f['latitude_deg'] is not None and f['longitude_east_deg'] is not None]))


if __name__=='__main__':main()
