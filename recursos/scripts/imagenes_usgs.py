"""Official USGS WMS crops of the public-domain LROC WAC global mosaic."""
import io,time,math
import requests,numpy as np
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import reproject,Resampling
ENDPOINT='https://planetarymaps.usgs.gov/cgi-bin/mapserv'
PRODUCT='https://astrogeology.usgs.gov/search/map/moon_lro_lroc_wac_global_morphology_mosaic_100m'

def lunar_usgs(lon,lat,side,size):
    from imagenes_catalogo import extent,OUT
    from pds_raster import RateLimited,retry_seconds
    cooldown=OUT.parent/'usgs-cooldown.txt'
    if cooldown.exists() and float(cooldown.read_text())>time.time():
        raise RateLimited('USGS requested a temporary pause; cached images remain available.')
    radius=1737400.;intervals,south,north=extent(lon,lat,side,radius)
    spans=[]
    for w,e in intervals:
        if w<180:spans.append((w,min(180,e)))
        if e>180:spans.append((max(180,w)-360,e-360))
    dstcrs=f'+proj=aeqd +lat_0={lat} +lon_0={lon} +R={radius} +units=m +no_defs'
    dst=from_bounds(-side/2,-side/2,side/2,side/2,size,size)
    rgb=np.zeros((size,size,3),dtype='uint8');coverage=np.zeros((size,size),dtype='uint8');urls=[];resolution=100.
    for west,east in spans:
        params=dict(map='/maps/earth/moon_simp_cyl.map',service='WMS',version='1.1.1',request='GetMap',layers='LROC_WAC',styles='',srs='EPSG:4326',bbox=f'{west},{south},{east},{north}',width=1024,height=1024,format='image/png',transparent='true')
        time.sleep(1)  # One client, paced requests; respect provider rate limits.
        response=requests.get(ENDPOINT,params=params,timeout=(10,60))
        if response.status_code==429:
            cooldown.parent.mkdir(parents=True,exist_ok=True)
            cooldown.write_text(str(time.time()+retry_seconds(response.headers.get('Retry-After','3600'))))
            raise RateLimited('USGS requested a temporary pause; retry after its deadline.')
        response.raise_for_status()
        if not response.headers.get('Content-Type','').startswith('image/'):
            raise ValueError('USGS returned no raster image')
        arr=np.asarray(Image.open(io.BytesIO(response.content)).convert('RGBA'))
        transform=from_bounds(west,south,east,north,arr.shape[1],arr.shape[0])
        resolution=max(resolution,math.radians(north-south)*radius/arr.shape[0],math.radians(east-west)*radius*abs(math.cos(math.radians(lat)))/arr.shape[1])
        crs=f'+proj=longlat +R={radius} +over +no_defs'
        mask=np.zeros_like(coverage)
        reproject((arr[:,:,3]>0).astype('uint8'),mask,src_transform=transform,src_crs=crs,dst_transform=dst,dst_crs=dstcrs,resampling=Resampling.nearest)
        for band in range(3):
            out=np.zeros_like(mask)
            reproject(arr[:,:,band],out,src_transform=transform,src_crs=crs,dst_transform=dst,dst_crs=dstcrs,resampling=Resampling.bilinear)
            rgb[:,:,band][mask>0]=out[mask>0]
        coverage[mask>0]=1;urls.append(response.url)
    return rgb,coverage,urls,resolution,dstcrs
