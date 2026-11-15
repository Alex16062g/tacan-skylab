"""Download the independently published USGS global WAC mosaic, resumably."""
import os,time,json,hashlib,requests
from imagenes_catalogo import LUNAR_ORIGINALS
URL='https://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LROC-WAC_Mosaic_global_100m_June2013.tif'
FILE=LUNAR_ORIGINALS/'Lunar_LRO_LROC-WAC_Mosaic_global_100m_June2013.tif'
PAGE='https://astrogeology.usgs.gov/search/map/moon_lro_lroc_wac_global_morphology_mosaic_100m'

def main():
    FILE.parent.mkdir(parents=True,exist_ok=True)
    if FILE.exists():print('Original already available:',FILE,flush=True);return
    part=FILE.with_suffix('.part');offset=part.stat().st_size if part.exists() else 0
    with requests.get(URL,headers={'Range':f'bytes={offset}-'} if offset else {},stream=True,timeout=(15,90)) as r:
        r.raise_for_status()
        append=offset>0 and r.status_code==206
        if r.status_code==206 and not r.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
            raise ValueError('Unexpected range; original not modified.')
        if not append:offset=0
        size=int(r.headers.get('Content-Length',0));received=0;t=time.time()
        with part.open('ab' if append else 'wb') as f:
            for block in r.iter_content(4*1024*1024):
                f.write(block);received+=len(block)
                if time.time()-t>20:
                    print(f'USGS {offset+received:,} / {offset+size:,} bytes',flush=True);t=time.time()
        if size and received!=size:raise ValueError('Incomplete download; run again to resume.')
        resolved=r.url
    os.replace(part,FILE)
    with FILE.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    FILE.with_suffix('.json').write_text(json.dumps(dict(source_url=URL,resolved_url=resolved,catalogue_url=PAGE,sha256=digest,size_bytes=FILE.stat().st_size,license='Public domain',use_constraints='Please cite authors',credit='NASA/GSFC/Arizona State University; distributed by USGS',edition='June 2013'),indent=2),encoding='utf-8')
    print('Downloaded and hashed:',FILE,flush=True)

if __name__=='__main__':main()
