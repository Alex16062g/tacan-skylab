"""Download and crop Copernicus DSM from Microsoft Planetary Computer.

GeoTIFF RasterPixelIsPoint: tiepoint is the sample center, without half-pixel shift.
The browser receives original samples, not interpolated/synthetic terrain.
"""
from pathlib import Path
import base64, hashlib, json, math
from datetime import datetime, timezone
import numpy as np
from PIL import Image
import requests

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'datos/tacana_copernicus_glo30.tif'
ITEM='Copernicus_DSM_COG_10_N15_00_W093_00_DEM'
STAC='https://planetarycomputer.microsoft.com/api/stac/v1'
if not SOURCE.exists():
    r=requests.get(f'{STAC}/collections/cop-dem-glo-30/items/{ITEM}',timeout=60)
    r.raise_for_status();item=r.json()
    (ROOT/'datos/tacana_stac.json').write_text(json.dumps(item,indent=2),encoding='utf-8')
    r=requests.get('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':item['assets']['data']['href']},timeout=60)
    r.raise_for_status()
    with requests.get(r.json()['href'],stream=True,timeout=120) as response:
        response.raise_for_status()
        partial=SOURCE.with_suffix('.part')
        with partial.open('wb') as output:
            for chunk in response.iter_content(1024*1024):output.write(chunk)
        partial.replace(SOURCE)

center_lon,center_lat=-92.109,15.132  # Smithsonian GVP catalogue position
bbox=[center_lon-.065,center_lat-.063,center_lon+.065,center_lat+.063]
im=Image.open(SOURCE)
sx,sy,_=im.tag_v2[33550];tie=im.tag_v2[33922]
origin_x=tie[3]-tie[0]*sx;origin_y=tie[4]+tie[1]*sy
keys=im.tag_v2[34735]
assert any(keys[i:i+4]==(1025,0,1,2) for i in range(4,len(keys),4)), 'Expected point samples'
c0=math.ceil((bbox[0]-origin_x)/sx);c1=math.floor((bbox[2]-origin_x)/sx)
r0=math.ceil((origin_y-bbox[3])/sy);r1=math.floor((origin_y-bbox[1])/sy)
assert 0<=c0<c1<im.width and 0<=r0<r1<im.height
heights=np.asarray(im.crop((c0,r0,c1+1,r1+1)),dtype='<f4')
assert np.isfinite(heights).all() and (heights>0).all()
lat=origin_y-np.arange(r0,r1+1)*sy;lon=origin_x+np.arange(c0,c1+1)*sx
# WGS84 local tangent approximation; horizontal/vertical units both meters.
phi=math.radians(center_lat);a=6378137.;e2=6.69437999014e-3
n=a/math.sqrt(1-e2*math.sin(phi)**2);m=a*(1-e2)/(1-e2*math.sin(phi)**2)**1.5
x=(lon-center_lon)*math.pi/180*n*math.cos(phi)
z=-(lat-center_lat)*math.pi/180*m
low,high=float(heights.min()),float(heights.max())
ref=(low+high)/2;scale=max(float(x[-1]-x[0]),float(z[-1]-z[0]))/2
metadata={
 'name':'Volcán Tacaná','location':'Frontera Chiapas, México / Guatemala',
 'catalog_position':{'latitude':center_lat,'longitude':center_lon,'elevation_m':4064,'source':'https://volcano.si.edu/volcano.cfm?vn=341130'},
 'dataset':'Copernicus DEM GLO-30 (DSM)','provider':'Microsoft Planetary Computer / Azure',
 'item_id':ITEM,'item_url':f'{STAC}/collections/cop-dem-glo-30/items/{ITEM}',
 'dataset_url':'https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-30',
 'documentation':'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM',
 'source_file':SOURCE.name,'sha256':hashlib.file_digest(SOURCE.open('rb'),'sha256').hexdigest(),
 'processed_utc':datetime.now(timezone.utc).isoformat(),
 'horizontal_crs':'WGS84 EPSG:4326','vertical_reference':'EGM2008; metros (documentación Copernicus)',
 'native_spacing_arcseconds':[sx*3600,sy*3600],
 'local_spacing_m':[float(x[1]-x[0]),float(z[1]-z[0])],
 'sample_bounds_wsen':[float(lon[0]),float(lat[-1]),float(lon[-1]),float(lat[0])],
 'raster_shape':list(heights.shape),'elevation_range_m':[low,high],
 'processing':'Recorte sin remuestreo. Un vértice por muestra original. X este, Z sur; aproximación métrica local WGS84. Elevación centrada visualmente; escala vertical 1× por defecto.',
 'limitations':'DSM de superficie, incluye vegetación e infraestructura; no equivale a terreno desnudo ni a medición topográfica de la cumbre. Colores por elevación, no imagen satelital.',
 'attribution':'produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved'
}
out=ROOT/'vista_previa'
(out/'tacana_fuentes.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
np.save(ROOT/'datos/tacana_alturas.npy',heights)
payload={'width':len(lon),'height':len(lat),'heights':base64.b64encode(heights.tobytes()).decode(),'x0':float(x[0]/scale),'z0':float(z[0]/scale),'dx':float((x[1]-x[0])/scale),'dz':float((z[1]-z[0])/scale),'reference':ref,'scale':scale,'min':low,'max':high}
(out/'tacana3d.js').write_text('window.TACANA_DATA='+json.dumps(payload,separators=(',',':'))+';',encoding='utf-8')
print(json.dumps({k:metadata[k] for k in ['raster_shape','local_spacing_m','elevation_range_m','sample_bounds_wsen']},indent=2))
peak=np.unravel_index(heights.argmax(),heights.shape)
print('Máximo DSM:',lat[peak[0]],lon[peak[1]],high)
