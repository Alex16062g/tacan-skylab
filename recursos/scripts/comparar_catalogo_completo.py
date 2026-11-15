"""Compare every named Moon/Mars location with Tacana at a common coarse scale.

12 km neighbourhoods, 2 km analysis spacing, 3 km sensitivity. Descriptive only:
overlapping samples are not independent; this script does not report ANOVA p-values.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.stats import wasserstein_distance
from calcular_similitud import affinity
from ampliar_catalogo_regiones import sample

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT/'recursos/catalogo_regiones'
OUT = ROOT/'recursos/comparacion_tacana'
FINE = 250.0
HALF = 11000.0
WINDOW = 12000.0
RADII = {'MOON': 1737400., 'MARS': 3396000., 'EARTH': 6371008.8}
FEATURES = [('mean_slope_deg', 'Pendiente', '°'), ('local_relief_m', 'Relieve local', 'm')]
ADDITIONAL_FEATURES = [
    ('relative_height_m', 'Altura sobre la mediana del entorno', 'm'),
    ('tpi_m', 'Posición topográfica (TPI)', 'm'),
    ('tri_m', 'Rugosidad del terreno (TRI)', 'm'),
]
OFFSETS = np.arange(-HALF, HALF+FINE, FINE)
EAST, NORTH = np.meshgrid(OFFSETS, OFFSETS)


def coordinates(lat, lon, radius):
    phi = np.radians(np.asarray(lat))[:, None, None]
    lam = np.radians(np.asarray(lon))[:, None, None]
    delta = np.hypot(EAST, NORTH)/radius
    bearing = np.arctan2(EAST, NORTH)
    p = np.arcsin(np.clip(np.sin(phi)*np.cos(delta)+np.cos(phi)*np.sin(delta)*np.cos(bearing), -1, 1))
    l = lam + np.arctan2(np.sin(bearing)*np.sin(delta)*np.cos(phi), np.cos(delta)-np.sin(phi)*np.sin(p))
    return np.degrees(p), np.degrees(l) % 360


def descriptors(patches, spacing):
    patches = np.asarray(patches, dtype=float)
    if (not np.isfinite(spacing) or spacing <= 0 or
            not np.isclose(spacing/FINE, round(spacing/FINE)) or
            not np.isclose(WINDOW/spacing, round(WINDOW/spacing)) or
            WINDOW/spacing < 2 or WINDOW/2 + 1.5*spacing > HALF):
        raise ValueError('Analysis spacing must divide the window and fit the smoothing support.')
    if patches.ndim != 3 or patches.shape[1:] != EAST.shape or not np.isfinite(patches).all():
        raise ValueError('Terrain patches must be finite and match the computational grid.')
    # A 250 m computational grid is interpolation, NOT 250 m native resolution.
    smooth = gaussian_filter(patches, sigma=(0,spacing/(2*FINE),spacing/(2*FINE)),
                             mode='nearest', truncate=3.)
    offsets = np.arange(-WINDOW/2, WINDOW/2+spacing, spacing)
    indices = np.rint((offsets+HALF)/FINE).astype(int)
    z = smooth[:,indices][:,:,indices]
    gx=(z[:,1:-1,2:]-z[:,1:-1,:-2])/(2*spacing)
    gy=(z[:,2:,1:-1]-z[:,:-2,1:-1])/(2*spacing)
    slopes=np.degrees(np.arctan(np.hypot(gx,gy)))
    neighbourhoods=np.lib.stride_tricks.sliding_window_view(z,(3,3),axis=(1,2))
    relief=np.percentile(neighbourhoods,95,axis=(-1,-2))-np.percentile(neighbourhoods,5,axis=(-1,-2))
    center = z[:,1:-1,1:-1]
    relative_height = center - np.median(z,axis=(1,2))[:,None,None]
    neighbours_mean = (neighbourhoods.sum(axis=(-1,-2))-center)/8
    tpi = center-neighbours_mean
    tri = np.sqrt(np.sum((neighbourhoods-center[...,None,None])**2,axis=(-1,-2)))
    return {key:values.reshape(len(patches),-1) for key,values in {
        'mean_slope_deg':slopes, 'local_relief_m':relief,
        'relative_height_m':relative_height, 'tpi_m':tpi, 'tri_m':tri,
    }.items()}


def reference_patches():
    source=ROOT/'recursos/datos/tacana_copernicus_glo30.tif'
    image=Image.open(source)
    grid=np.asarray(image,dtype=np.float64)
    sx,sy,_=image.tag_v2[33550];tie=image.tag_v2[33922]
    keys=image.tag_v2[34735]
    if not any(keys[i:i+4]==(1025,0,1,2) for i in range(4,len(keys),4)):
        raise ValueError('Reference must use RasterPixelIsPoint.')
    lat,lon=coordinates([15.132],[-92.109],RADII['EARTH']);lon=(lon+180)%360-180
    x=(lon-(tie[3]-tie[0]*sx))/sx;y=((tie[4]+tie[1]*sy)-lat)/sy
    if x.min()<0 or y.min()<0 or x.max()>grid.shape[1]-1 or y.max()>grid.shape[0]-1:
        raise ValueError('Tacana tile does not cover smoothing support; do not extrapolate.')
    patch=map_coordinates(grid,[y,x],order=1,mode='constant',cval=np.nan,prefilter=False)
    if not np.isfinite(patch).all() or np.any(patch < -10000):
        raise ValueError('Missing or invalid Tacana reference heights.')
    return patch,source


def compare(values, reference, spacing):
    features=[]
    for variable,label,unit in FEATURES + ADDITIONAL_FEATURES:
        a=np.asarray(values[variable],float);b=np.asarray(reference[variable],float)
        if min(len(a),len(b))<3 or not np.isfinite(a).all() or not np.isfinite(b).all():
            return None
        sd=float(b.std(ddof=1))
        if sd<=0:return None
        distance=float(wasserstein_distance(a,b));low=max(a.min(),b.min());high=min(a.max(),b.max())
        included = variable in {f[0] for f in FEATURES}
        features.append(dict(variable=variable,label=label,unit=unit,weight=.5 if included else 0.,
            included_in_overall=included,
            similarity_percent=affinity(distance,sd),wasserstein_distance=distance,reference_sd=sd,
            reference_mean=float(b.mean()),region_mean=float(a.mean()),n_reference=len(b),n_region=len(a),
            shared_range=[float(low),float(high)] if low<high else None,
            samples=a.tolist()))
    return dict(grid_spacing_m=spacing,window_side_m=WINDOW,relief_neighbourhood_side_m=2*spacing,
                similarity_percent=sum(f['weight']*f['similarity_percent'] for f in features),features=features)


def write(path,value,pretty=False):
    path.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False,
                              indent=2 if pretty else None,separators=None if pretty else (',',':')),encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    patch,ref_source=reference_patches()
    references={s:{k:v[0] for k,v in descriptors(patch,s).items()} for s in [2000,3000]}
    metadata=dict(version=2,scope='named_location_neighbourhoods',experimental=True,
        generated_utc=datetime.now(timezone.utc).isoformat(),
        formula='S_j = 100/(1 + Wasserstein_j/SD_Tacana_j); S = 0.5*S_slope + 0.5*S_relief',
        primary_spacing_m=2000,sensitivity_spacing_m=3000,window_side_m=WINDOW,
        processing=dict(computational_spacing_m=FINE,smoothing_sigma='analysis_spacing / 2',
                        gaussian_truncate_sigma=3,reference_center=[-92.109,15.132],
                        slope='central differences; gradient magnitude angle in degrees',
                        relief='P95-P05 of each overlapping 3x3 coarse neighbourhood',
                        relative_height='interior elevation minus median of the full 12 km coarse grid; not absolute altitude',
                        tpi='central elevation minus mean of eight neighbouring cells',
                        tri='Riley TRI: sqrt(sum((neighbour_elevation-central_elevation)^2)) over eight neighbours',
                        additional_features_in_overall=False,
                        samples_primary=25,samples_sensitivity=9),
        method_references={'tpi_tri':'https://gdal.org/en/stable/programs/gdaldem.html',
                           'relative_height':'Project definition: elevation relative to median of each 12 km window'},
        reference=dict(source=str(ref_source.relative_to(ROOT)),sha256=hashlib.sha256(ref_source.read_bytes()).hexdigest(),
                       samples={str(s):{k:v.tolist() for k,v in r.items()} for s,r in references.items()}),
        limitations=['Experimental descriptive score, not a probability or ANOVA result.',
                     'Each score describes a 12 km neighbourhood around an official point, not the full named feature.',
                     'The 250 m grid is computational interpolation; native global DEM latitude spacing is about 1.9 km.',
                     'Nominal scales match but sensors and effective resolution still differ. No uncertainty interval is estimated.',
                     'Samples overlap, and named locations can overlap. No independence or equivalence claim; no inferential p-values.',
                     'The maximum over thousands of candidates is a search result, not validated physical equivalence.',
                     'Absolute elevation, temperature, atmosphere and seismicity are not included in this terrain score.',
                     'Relative height, TPI and TRI are supplementary correlated terrain descriptors; their weights in the overall score are zero.',
                     'These scores are not interchangeable with the previous local 100 m / 1 km block analysis.'],
        sources={},selections={},regions=[])
    for body in ['MOON','MARS']:
        path=CATALOG/f'{body.lower()}.json';catalog=json.loads(path.read_text(encoding='utf-8'))
        features=catalog['features'];results=[]
        if body=='MOON':
            source=ROOT/'recursos/datos/nasa/luna/global/ldem_16.tif'
            grid=np.asarray(Image.open(source),dtype=np.float32)*1000
            grid=np.roll(grid,-grid.shape[1]//2,axis=1)
        else:
            source=ROOT/'recursos/datos/nasa/marte/global/megt90n000fb.img'
            grid=np.asarray(np.memmap(source,dtype='>i2',shape=(5760,11520)),dtype=np.float32)
        metadata['sources'][body]=dict(source=str(source.relative_to(ROOT)),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            catalogue_ids_sha256=hashlib.sha256('\n'.join(sorted(f['id'] for f in features)).encode()).hexdigest())
        for start in range(0,len(features),32):
            batch=features[start:start+32]
            valid=[f for f in batch if f['latitude_deg'] is not None and f['longitude_east_deg'] is not None]
            for f in batch:
                if f not in valid:
                    results.append(dict(region=f['id'],body=body,name=f['name'],status='missing_coordinates',primary=None,sensitivity=None))
            if not valid:continue
            lat,lon=coordinates([f['latitude_deg'] for f in valid],[f['longitude_east_deg'] for f in valid],RADII[body])
            patches=sample(grid,lat,lon)
            scales={s:descriptors(patches,s) for s in [2000,3000]}
            for i,f in enumerate(valid):
                primary=compare({k:v[i] for k,v in scales[2000].items()},references[2000],2000)
                sensitivity=compare({k:v[i] for k,v in scales[3000].items()},references[3000],3000)
                results.append(dict(region=f['id'],name=f['name'],body=body,source_url=f['source_url'],
                    status='evaluated' if primary else 'insufficient_data',primary=primary,sensitivity=sensitivity,
                    location=dict(latitude=f['latitude_deg'],longitude=(f['longitude_east_deg']+180)%360-180,label=f['name']),
                    diameter_km=f['diameter_km'],window_larger_than_feature=f['diameter_km'] is not None and f['diameter_km']<12))
            if start%1024==0:print(body,min(start+len(batch),len(features)),'/',len(features),flush=True)
        ranked=sorted([r for r in results if r['primary']],key=lambda r:(-r['primary']['similarity_percent'],r['region']))
        for rank,r in enumerate(ranked,1):r['rank']=rank
        lookup={r['region']:r for r in results}
        for f in features:
            r=lookup[f['id']]
            f['global_similarity']=dict(status=r['status'],percent=r['primary']['similarity_percent'] if r['primary'] else None,
                rank=r.get('rank'),grid_spacing_m=2000,window_side_m=WINDOW)
        catalog['summary']['globally_compared']=len(ranked)
        write(path,catalog)
        write(OUT/f'similitud_catalogo_{body.lower()}.json',dict(body=body,regions=results))
        metadata['selections'][body]=dict(catalogued_count=len(features),candidate_count=len(ranked),
            excluded_count=len(results)-len(ranked),selected_region=ranked[0]['region'] if ranked else None,
            full_results=f'similitud_catalogo_{body.lower()}.json',
            top_regions=[dict(region=r['region'],name=r['name'],similarity_percent=r['primary']['similarity_percent']) for r in ranked[:10]])
        if ranked:
            metadata['selections'][body]['matching_regions'] = [r for r in ranked if r['primary']['similarity_percent'] > 80]
            metadata['regions'].append(ranked[0])
            print('BEST',body,ranked[0]['name'],round(ranked[0]['primary']['similarity_percent'],3),flush=True)
    write(OUT/'similitud_catalogo_resumen.json',metadata,pretty=True)
    summary=json.loads((CATALOG/'resumen.json').read_text(encoding='utf-8'))
    summary['global_similarity']=dict(source='../comparacion_tacana/similitud_catalogo_resumen.json',
        scope='12 km neighbourhoods, 2 km analysis spacing; not local 1 km blocks',
        evaluated={b:s['candidate_count'] for b,s in metadata['selections'].items()})
    write(CATALOG/'resumen.json',summary,pretty=True)


if __name__=='__main__':main()
