"""Fetch georeferenced image windows; no generated imagery or terrain rendering."""
from pathlib import Path
import math, json, hashlib, io
from urllib.parse import urlsplit, parse_qsl
from datetime import datetime, timezone
import requests
import numpy as np
from PIL import Image
from rasterio.transform import from_bounds, from_origin
from rasterio.warp import reproject, Resampling
import rasterio

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'recursos/comparador_imagenes'
CTX='https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX1/MapServer'

def bbox(lon,lat,radius):
    dy=math.degrees(6000/radius);dx=dy/math.cos(math.radians(lat))
    return [lon-dx,lat-dy,lon+dx,lat+dy]

def fetch_image(url,params,path):
    r=requests.get(url,params=params,timeout=60);r.raise_for_status()
    if not r.headers.get('Content-Type','').startswith('image/'):raise ValueError(r.text[:200])
    image=Image.open(io.BytesIO(r.content));image.load()
    if image.size!=(1024,1024):raise ValueError('Wrong image size')
    path.write_bytes(r.content)
    return r.url

def main():
    OUT.mkdir(exist_ok=True)
    summary=json.loads((ROOT/'recursos/comparacion_tacana/similitud_catalogo_resumen.json').read_text(encoding='utf-8'))
    selected={r['body']:r for r in summary['regions']}
    from imagenes_abiertas import landsat, moon
    images={'EARTH':landsat(), 'MOON':moon(selected['MOON']['location'])}
    r=selected['MARS'];lon=r['location']['longitude'];lat=r['location']['latitude']
    bounds=bbox(lon,lat,3396190)
    info=requests.get(CTX,params={'f':'json'},timeout=30).json()['tileInfo']
    lod=next(l for l in info['lods'] if l['level']==11);res=lod['resolution'];size=info['cols']
    ox,oy=info['origin']['x'],info['origin']['y']
    west,south,east,north=bounds
    c0=math.floor((west-ox)/(res*size));c1=math.floor((east-ox)/(res*size))
    r0=math.floor((oy-north)/(res*size));r1=math.floor((oy-south)/(res*size))
    mosaic=np.zeros(((r1-r0+1)*size,(c1-c0+1)*size),dtype=np.uint8)
    sources=[];cache=OUT/'tiles';cache.mkdir(exist_ok=True)
    for row in range(r0,r1+1):
        for col in range(c0,c1+1):
            url=f'{CTX}/tile/11/{row}/{col}';path=cache/f'11_{row}_{col}.png'
            if not path.exists():
                response=requests.get(url,timeout=45);response.raise_for_status();path.write_bytes(response.content)
            image=Image.open(path).convert('RGB');arr=np.asarray(image)
            if image.size!=(size,size) or not np.all(arr[:,:,0]==arr[:,:,1]):raise ValueError('Unexpected CTX tile')
            mosaic[(row-r0)*size:(row-r0+1)*size,(col-c0)*size:(col-c0+1)*size]=arr[:,:,0]
            sources.append(dict(url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    result=np.zeros((1024,1024),dtype=np.uint8)
    crs=info['spatialReference']['wkt']
    transform=from_bounds(*bounds,1024,1024)
    reproject(mosaic,result,src_transform=from_origin(ox+c0*size*res,oy-r0*size*res,res,res),src_crs=crs,dst_transform=transform,dst_crs=crs,resampling=Resampling.bilinear)
    path=OUT/'mars.png'
    with rasterio.open(path,'w',driver='PNG',width=1024,height=1024,count=1,dtype='uint8') as dataset:dataset.write(result,1)
    images['MARS']=dict(file=path.name,center=[lon,lat],bounds_wsen=bounds,tiles=sources,credit='NASA / JPL / MSSS / Caltech Murray Lab / Esri',source_url='https://murray-lab.caltech.edu/CTX/',license='Free use for all purposes (Murray Lab Beta01); credit NASA/JPL/MSSS/The Murray Lab',license_url=CTX,product_version='Beta01 (as identified by the imagery service)',native_resolution_m=5,served_pixel_latitude_m=math.radians(res)*3396190,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),acquisition_date=None)
    manifest=dict(retrieved_utc=datetime.now(timezone.utc).isoformat(),images=images,window_side_approx_km=12,north_up=True,selected_regions={b:s['selected_region'] for b,s in summary['selections'].items()},limitations=['Different dates, sensors, illumination, atmospheric conditions and resolution.','Approximate 12 km geographic windows; longitude scale adjusted at center latitude.','Swipe does not register matching features or measure photographic similarity.','The terrain index is calculated separately from elevation models.','Acquisition dates for these mosaic extracts have not been determined.'])
    (OUT/'fuentes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('MARS downloaded; manifest saved',flush=True)

if __name__=='__main__':main()
