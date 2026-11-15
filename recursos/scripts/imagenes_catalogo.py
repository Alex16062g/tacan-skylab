"""On-demand, georeferenced public imagery for every official catalogue location.

Full views use the catalogue diameter plus margin; analysis views remain 12 km.
No reconstruction of missing observations. Coverage is recorded separately.
"""
import json, math, hashlib, threading, io, os, tempfile
from pathlib import Path
from functools import lru_cache
import requests, numpy as np, tifffile
from PIL import Image
from rasterio.transform import from_origin, from_bounds
from rasterio.warp import reproject, Resampling, transform_bounds
from pds_raster import RemoteFile, window, nasa_dns

ROOT=Path(__file__).resolve().parents[2]
LEGACY_OUT=ROOT/'recursos/comparador_imagenes/regiones_catalogo'
# Generated files must not trigger Live Server's workspace watcher.
PROJECT_KEY=hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:12]
OUT=Path(os.environ.get('LOCALAPPDATA',tempfile.gettempdir()))/'SpaceTerrainCache'/PROJECT_KEY/'regiones_catalogo'
LUNAR_ORIGINALS=ROOT.parent/f'.{ROOT.name}-build-cache'/PROJECT_KEY/'lunar-originals'
PDS='https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/EXTRAS/BROWSE/WAC_GLOBAL/'
CTX='https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX1/MapServer'
LOCK=threading.RLock()

@lru_cache(maxsize=2)
def catalog(body):
    data=json.loads((ROOT/f'recursos/catalogo_regiones/{body.lower()}.json').read_text(encoding='utf-8'))
    return {f['id']:f for f in data['features']}

@lru_cache(maxsize=10)
def lunar_tile(tile):
    name=f'WAC_GLOBAL_{tile}_100M.PYR.TIF';url=PDS+name
    local=LUNAR_ORIGINALS/name
    if local.exists():
        reader=local.open('rb');reader.url=url
    else:reader=RemoteFile(url)
    return reader,tifffile.TiffFile(reader)

def extent(lon,lat,side,radius):
    angle=min(math.pi,side/math.sqrt(2)/radius)
    delta=math.degrees(angle);south=max(-90,lat-delta);north=min(90,lat+delta)
    if south<=-90 or north>=90 or angle>=math.pi/2:intervals=[(0,360)]
    else:
        dx=math.degrees(math.asin(min(1,math.sin(angle)/math.cos(math.radians(lat)))))
        w=lon-dx;e=lon+dx
        intervals=[(w,e)] if w>=0 and e<=360 else [(w+360,360),(0,e)] if w<0 else [(w,360),(0,e-360)]
    return intervals,south,north

def lunar(lon,lat,side,size):
    radius=1737400.;intervals,south,north=extent(lon,lat,side,radius)
    tiles=[]
    if north>60:tiles.append(('P900N0000',None))
    if south<-60:tiles.append(('P900S0000',None))
    if south<60 and north>-60:
        for w,e in intervals:
            for q in range(4):
                a=max(w,q*90);b=min(e,(q+1)*90)
                if a>=b:continue
                for hemi,low,high in [('N',max(0,south),min(60,north)),('S',max(-60,south),min(0,north))]:
                    if low<high:tiles.append((f'E300{hemi}{q*900+450:04d}',(a,low,b,high)))
    dstcrs=f'+proj=aeqd +lat_0={lat} +lon_0={lon} +R={radius} +units=m +no_defs'
    dst=from_bounds(-side/2,-side/2,side/2,side/2,size,size)
    result=np.zeros((size,size),dtype='uint8');coverage=np.zeros_like(result);urls=[];effective=100
    for tile,geobb in tiles:
        reader,tiff=lunar_tile(tile);tags=tiff.geotiff_metadata
        level=max(0,min(len(tiff.pages)-1,int(math.log2(max(1,side/size/100)))))
        page=tiff.pages[level];factor=tiff.pages[0].imagewidth/page.imagewidth
        effective=max(effective,100*factor)
        sx,sy,_=tags['ModelPixelScale'];tie=tags['ModelTiepoint'];sx*=factor;sy*=factor
        originx=tie[3];originy=tie[4]
        if tile.startswith('E'):
            scale=math.pi*radius/180
            box=tuple(v*scale for v in geobb)
            srccrs=f'+proj=longlat +R={radius} +over +no_defs'
        else:
            srccrs=f'+proj=stere +lat_0={90 if tile[4]=="N" else -90} +lon_0=0 +k=1 +R={radius} +units=m +no_defs'
            box=transform_bounds(dstcrs,srccrs,-side/2,-side/2,side/2,side/2,densify_pts=40)
        x0=max(0,math.floor((box[0]-originx)/sx)-2);x1=min(page.imagewidth,math.ceil((box[2]-originx)/sx)+2)
        y0=max(0,math.floor((originy-box[3])/sy)-2);y1=min(page.imagelength,math.ceil((originy-box[1])/sy)+2)
        if x0>=x1 or y0>=y1:continue
        arr=window(page,reader,x0,y0,x1,y1)
        src=from_origin(originx+x0*sx,originy-y0*sy,sx,sy)
        if tile.startswith('E'):src=from_origin(src.c/scale,src.f/scale,sx/scale,sy/scale)
        partial=np.zeros_like(result);mask=np.zeros_like(result)
        reproject(arr,partial,src_transform=src,src_crs=srccrs,dst_transform=dst,dst_crs=dstcrs,resampling=Resampling.bilinear)
        reproject(np.ones_like(arr),mask,src_transform=src,src_crs=srccrs,dst_transform=dst,dst_crs=dstcrs,resampling=Resampling.nearest)
        result[mask>0]=partial[mask>0];coverage[mask>0]=1
        urls.append(reader.url)
    return np.dstack([result]*3),coverage,urls,effective,dstcrs

@lru_cache(maxsize=1)
def mars_info():
    r=requests.get(CTX,params={'f':'json'},timeout=30);r.raise_for_status();return r.json()['tileInfo']

def martian(lon,lat,side,size):
    radius=3396190.;info=mars_info();intervals,south,north=extent(lon,lat,side,radius)
    target=math.degrees(side/size/radius)
    lod=min(info['lods'],key=lambda x:abs(math.log(x['resolution']/target)))
    res=lod['resolution'];px=info['cols'];ox=info['origin']['x'];oy=info['origin']['y']
    dstcrs=f'+proj=aeqd +lat_0={lat} +lon_0={lon} +R={radius} +units=m +no_defs'
    dst=from_bounds(-side/2,-side/2,side/2,side/2,size,size)
    result=np.zeros((size,size,3),dtype='uint8');coverage=np.zeros((size,size),dtype='uint8');urls=[]
    # Service uses -180..180, split explicitly at its longitude seam.
    spans=[]
    for w,e in intervals:
        if w<180:spans.append((w,min(e,180)))
        if e>180:spans.append((max(w,180)-360,e-360))
    # Near a pole a small ground footprint spans many longitudes. Use a
    # coarser real overview instead of truncating the requested footprint.
    def tile_count(resolution):
        rows=math.floor((oy-south)/(px*resolution))-max(0,math.floor((oy-north)/(px*resolution)))+1
        return rows*sum(math.floor((e-ox)/(px*resolution))-math.floor((w-ox)/(px*resolution))+1 for w,e in spans)
    for candidate in sorted(info['lods'],key=lambda x:x['resolution']):
        if candidate['resolution']>=res and tile_count(candidate['resolution'])<=64:
            lod=candidate;res=lod['resolution'];break
    for w,e in spans:
        c0=math.floor((w-ox)/(px*res));c1=math.floor((e-ox)/(px*res))
        r0=max(0,math.floor((oy-min(north,90))/(px*res)));r1=math.floor((oy-max(south,-90))/(px*res))
        if (c1-c0+1)*(r1-r0+1)>400:raise ValueError('La región requiere una escala de mosaico más amplia.')
        for row in range(r0,r1+1):
            for col in range(c0,c1+1):
                u=f'{CTX}/tile/{lod["level"]}/{row}/{col}'
                cache=OUT/f'ctx_{lod["level"]}_{row}_{col}.jpg'
                if not cache.exists():
                    r=requests.get(u,timeout=(5,40))
                    if r.status_code==404:continue
                    r.raise_for_status()
                    temporary=cache.with_suffix(f'.{os.getpid()}.part');temporary.write_bytes(r.content);os.replace(temporary,cache)
                arr=np.asarray(Image.open(cache).convert('RGB'));mask=np.any(arr>0,axis=2).astype('uint8')
                src=from_origin(ox+col*px*res,oy-row*px*res,res,res)
                src_crs=f'+proj=longlat +R={radius} +over +no_defs'
                projected=np.zeros((size,size),dtype='uint8')
                reproject(mask,projected,src_transform=src,src_crs=src_crs,dst_transform=dst,dst_crs=dstcrs,resampling=Resampling.nearest)
                for band in range(3):
                    temp=np.zeros_like(projected)
                    reproject(arr[:,:,band],temp,src_transform=src,src_crs=src_crs,dst_transform=dst,dst_crs=dstcrs,resampling=Resampling.bilinear)
                    result[:,:,band][projected>0]=temp[projected>0]
                coverage[projected>0]=1;urls.append(u)
    return result,coverage,urls,math.radians(res)*radius,dstcrs

def generate(body,ident,view='full'):
    if body not in ['MOON','MARS'] or view not in ['full','analysis']:raise ValueError('Solicitud no válida')
    f=catalog(body).get(ident)
    if not f:raise ValueError('Región no encontrada')
    lat=f['latitude_deg'];lon=f['longitude_east_deg']
    if lat is None or lon is None:raise ValueError('Sin coordenadas oficiales')
    diameter=f.get('diameter_km');side=12000 if view=='analysis' else max(12000,(diameter or 0)*1250)
    # A local azimuthal view cannot represent more than a hemisphere reliably.
    radius=1737400 if body=='MOON' else 3396190
    if side/math.sqrt(2)>math.pi*radius*.95:raise ValueError('La extensión requiere una vista global; no se presenta un recorte parcial como completo.')
    key=hashlib.sha256(json.dumps([ident,lat,lon,side,view,'v1']).encode()).hexdigest()[:16]
    OUT.mkdir(parents=True,exist_ok=True);meta=OUT/f'{key}.json';png=OUT/f'{key}.png'
    with LOCK:
        if meta.exists() and png.exists():return json.loads(meta.read_text(encoding='utf-8'))
        old_meta=LEGACY_OUT/meta.name;old_png=LEGACY_OUT/png.name
        if old_meta.exists() and old_png.exists():return json.loads(old_meta.read_text(encoding='utf-8'))
        from imagenes_usgs import lunar_usgs
        rgb,mask,urls,res,crs=(lunar_usgs if body=='MOON' else martian)(lon%360,lat,side,512)
        fraction=float(mask.mean())
        if fraction==0:raise ValueError('El mosaico no tiene observaciones en esta región.')
        Image.fromarray(np.dstack([rgb,mask*255])).save(png)
        license_url='https://astrogeology.usgs.gov/search/map/moon_lro_lroc_wac_global_morphology_mosaic_100m' if body=='MOON' else CTX
        data=dict(region=ident,body=body,name=f['name'],file=f'regiones_catalogo/{png.name}',center=[lon,lat],
            window_side_km=side/1000,view=view,diameter_km=diameter,extent_basis='catalogue diameter +25% margin' if diameter and view=='full' else '12 km analysis window',
            coverage_fraction=fraction,coverage_status='complete_raster' if fraction>=.9999 else 'partial_raster',
            source_url=urls[0],source_urls=urls,native_resolution_m=100 if body=='MOON' else 5,display_source_resolution_m=res,
            license='Public domain (PDS)' if body=='MOON' else 'Free use for all purposes; attribution required',license_url=license_url,
            credit='NASA/GSFC/Arizona State University; distributed by USGS (LROC_WAC WMS)' if body=='MOON' else 'NASA/JPL/MSSS/The Murray Lab',
            projection=crs,processing='Azimuthal equidistant, north up; bilinear display resampling; transparent missing pixels; no synthetic infill. Diameter is an extent proxy, not an official boundary.',
            similarity_percent=(f.get('global_similarity') or {}).get('percent'),sha256=hashlib.sha256(png.read_bytes()).hexdigest())
        meta.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');return data

if __name__=='__main__':
    nasa_dns()
    import sys
    d=generate(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'full')
    print(json.dumps(d,ensure_ascii=True),flush=True)
