"""Reproducible crops from public-domain Landsat and LROC PDS products."""
from pathlib import Path
import json, math, hashlib, re
import requests
import numpy as np
from PIL import Image
import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import from_bounds as transform_bounds, from_origin
from rasterio.warp import reproject, Resampling, transform_bounds as project_bounds

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'recursos/comparador_imagenes'
RAW=ROOT/'recursos/datos/imagenes_abiertas'
RAW.mkdir(exist_ok=True)
STAC='https://planetarycomputer.microsoft.com/api/stac/v1'
LANDSAT_ID='LC08_L2SP_021050_20251126_02_T1'
PDS='https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DATA/BDR/WAC_GLOBAL/WAC_GLOBAL_E300S0450_100M.IMG'

def get(url, **kw):
    r=requests.get(url,timeout=90,**kw);r.raise_for_status();return r

def bounds(lon,lat,radius):
    dy=math.degrees(6000/radius);dx=dy/math.cos(math.radians(lat))
    return [lon-dx,lat-dy,lon+dx,lat+dy]

def landsat():
    url=f'{STAC}/collections/landsat-c2-l2/items/{LANDSAT_ID}'
    item=get(url).json(); (RAW/'landsat_item.json').write_text(json.dumps(item,indent=2),encoding='utf-8')
    bb=bounds(-92.109,15.132,6371008.8)
    channels=[]; qa=None
    for name in ['red','green','blue','qa_pixel']:
        cache=RAW/f'landsat_{name}.tif'
        if not cache.exists():
            signed=get('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':item['assets'][name]['href']}).json()['href']
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.TIF'):
                with rasterio.open(signed) as ds:
                    window=from_bounds(*project_bounds('EPSG:4326',ds.crs,*bb),ds.transform).round_offsets().round_lengths()
                    arr=ds.read(1,window=window); transform=ds.window_transform(window)
                    profile=ds.profile.copy();profile.update(width=arr.shape[1],height=arr.shape[0],transform=transform,count=1)
                    with rasterio.open(cache,'w',**profile) as target:target.write(arr,1)
        with rasterio.open(cache) as ds:
            arr=ds.read(1)
            result=np.zeros((1024,1024),dtype=arr.dtype)
            reproject(arr,result,src_transform=ds.transform,src_crs=ds.crs,dst_transform=transform_bounds(*bb,1024,1024),dst_crs='EPSG:4326',resampling=Resampling.nearest if name=='qa_pixel' else Resampling.bilinear)
        if name=='qa_pixel':qa=result
        else:channels.append(result.astype(float)*2.75e-5-.2)
        print('Landsat',name,flush=True)
    invalid=(qa & 63)!=0
    if invalid.mean()>.1:raise ValueError(f'Cloud/shadow/fill exceeds 10%: {invalid.mean()}')
    # Common fixed reflectance stretch and gamma; no generated detail, no cloud infill.
    rgb=np.uint8(np.clip(np.stack(channels,axis=-1)/.35,0,1)**(1/2.2)*255)
    path=OUT/'tacana.jpg';Image.fromarray(rgb).save(path,quality=95)
    return dict(file=path.name,center=[-92.109,15.132],bounds_wsen=bb,credit='USGS / NASA, Landsat 8 OLI',
        source_url=url,product_id=LANDSAT_ID,native_resolution_m=30,acquisition_date=item['properties']['datetime'],
        license='Public domain (U.S. Government work)',license_url='https://www.usgs.gov/faqs/are-there-any-restrictions-use-or-redistribution-landsat-data',
        processing='RGB B4/B3/B2 surface reflectance; scale 0.0000275, offset -0.2; fixed stretch 0–0.35 and gamma 2.2; bilinear display resampling; no generated pixels or cloud replacement.',
        qa_flagged_fraction=float(invalid.mean()),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),raw_crops=[str(p.relative_to(ROOT)) for p in RAW.glob('landsat_*.tif')])

def moon(location):
    lon,lat=location['longitude'],location['latitude']
    if not (0<lon<90 and -60<lat<0):raise ValueError('Selected region requires a different PDS tile')
    bb=bounds(lon,lat,1737400)
    label=get(PDS,headers={'Range':'bytes=0-16383'})
    if label.status_code!=206:raise ValueError('PDS range requests required')
    text=label.content.decode('ascii',errors='replace');(RAW/'moon_pds_label.txt').write_text(text,encoding='utf-8')
    value=lambda k: float(re.search(r'\b'+k+r'\s*=\s*([-\d.]+)',text)[1])
    width=int(value('LINE_SAMPLES'));record=int(value('RECORD_BYTES'));offset=(int(value('IMAGE'))-1)*record
    res=value('MAP_RESOLUTION')
    c0=math.floor(bb[0]*res);c1=math.ceil(bb[2]*res)
    r0=math.floor(-bb[3]*res);r1=math.ceil(-bb[1]*res)
    cache=RAW/f'moon_pds_rows_{r0}_{r1}.bin'
    start=offset+r0*record;end=offset+r1*record-1
    if not cache.exists():
        r=get(PDS,headers={'Range':f'bytes={start}-{end}'})
        if r.status_code!=206 or len(r.content)!=(r1-r0)*record:raise ValueError('Invalid PDS byte range')
        cache.write_bytes(r.content)
    arr=np.frombuffer(cache.read_bytes(),dtype='<f4').reshape(r1-r0,width)[:,c0:c1].copy()
    if not np.isfinite(arr).all() or arr.min()<-1e10:raise ValueError('Invalid PDS pixels')
    result=np.zeros((1024,1024),dtype='float32')
    crs='+proj=longlat +R=1737400 +no_defs'
    reproject(arr,result,src_transform=from_origin(c0/res,-r0/res,1/res,1/res),src_crs=crs,dst_transform=transform_bounds(*bb,1024,1024),dst_crs=crs,resampling=Resampling.bilinear)
    lo,hi=np.percentile(arr,[1,99]);pixels=np.uint8(np.clip((result-lo)/(hi-lo),0,1)*255)
    path=OUT/'moon.png';Image.fromarray(pixels).save(path)
    return dict(file=path.name,center=[lon,lat],bounds_wsen=bb,credit='NASA/GSFC/Arizona State University; LROC PDS',source_url=PDS,
        native_resolution_m=100,acquisition_date=None,product_id='WAC_GLOBAL_E300S0450_100M',product_version='v1.3',
        license='Public domain (LROC PDS product)',license_url='https://www.lroc.im-ldi.com/about/terms',
        processing='PDS float32 pixels; byte-range crop; display stretch P1–P99; bilinear resampling. No generated detail.',
        source_byte_range=[start,end],source_rows_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    manifest=json.loads((OUT/'fuentes.json').read_text(encoding='utf-8'))
    summary=json.loads((ROOT/'recursos/comparacion_tacana/similitud_catalogo_resumen.json').read_text(encoding='utf-8'))
    manifest['images']['EARTH']=landsat()
    manifest['images']['MOON']=moon(next(r for r in summary['regions'] if r['body']=='MOON')['location'])
    manifest['limitations']=[x for x in manifest['limitations'] if not x.startswith('Earth imagery service')]
    (OUT/'fuentes.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Public-domain Earth and Moon crops saved')
