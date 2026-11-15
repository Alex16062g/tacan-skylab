"""Open Landsat map context; does not change the 12 km analysis/comparison crop."""
from imagenes_abiertas import *

def generar():
    item=json.loads((RAW/'landsat_item.json').read_text(encoding='utf-8'))
    # 60 km wide, preserving the same geographic centre and native 30 m detail.
    bb=bounds(-92.109,15.132,6371008.8/5)
    size=2048;channels=[];valid=np.ones((size,size),dtype=bool)
    for name in ['red','green','blue']:
        cache=RAW/f'contexto_{name}.tif'
        if not cache.exists():
            signed=get('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':item['assets'][name]['href']}).json()['href']
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.TIF'):
                with rasterio.open(signed) as ds:
                    window=from_bounds(*project_bounds('EPSG:4326',ds.crs,*bb),ds.transform).round_offsets().round_lengths()
                    arr=ds.read(1,window=window,boundless=True,fill_value=0)
                    profile=ds.profile.copy();profile.update(width=arr.shape[1],height=arr.shape[0],transform=ds.window_transform(window),count=1)
                    with rasterio.open(cache,'w',**profile) as target:target.write(arr,1)
        with rasterio.open(cache) as ds:
            result=np.zeros((size,size),dtype='uint16')
            reproject(ds.read(1),result,src_transform=ds.transform,src_crs=ds.crs,dst_transform=transform_bounds(*bb,size,size),dst_crs='EPSG:4326',src_nodata=0,dst_nodata=0,resampling=Resampling.bilinear)
        valid &= result>0
        channels.append(result.astype(float)*2.75e-5-.2)
        print('Map context:',name,flush=True)
    rgb=np.uint8(np.clip(np.stack(channels,axis=-1)/.35,0,1)**(1/2.2)*255)
    # Fade only the outer 5 km of the visual layer, including any scene edge.
    from scipy.ndimage import distance_transform_edt
    distance=distance_transform_edt(np.pad(valid,1))[1:-1,1:-1]
    opacity=np.clip((distance-1)/(size*5/60),0,1)
    alpha=np.uint8(opacity**2*(3-2*opacity)*255)
    path=OUT/'tacana_contexto.png';Image.fromarray(np.dstack([rgb,alpha])).save(path)
    metadata=dict(file=path.name,bounds_wsen=bb,product_id=LANDSAT_ID,native_resolution_m=30,
        window_side_approx_km=60,processing='Landsat B4/B3/B2; same fixed RGB stretch as comparison. Outer 5 km alpha feather for map display only. No infill or generated terrain.',
        sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (OUT/'contexto_fuentes.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print('Map context saved',flush=True)

if __name__=='__main__':generar()
