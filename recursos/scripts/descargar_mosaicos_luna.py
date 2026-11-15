"""Fetch ten original WAC mosaics once, avoiding thousands of remote crop requests."""
import time,requests,os
from imagenes_catalogo import LUNAR_ORIGINALS,PDS
from pds_raster import nasa_dns,COOLDOWN,RateLimited,record_cooldown

def main():
    nasa_dns();LUNAR_ORIGINALS.mkdir(parents=True,exist_ok=True)
    tiles=[f'E300{h}{q*900+450:04d}' for h in ['N','S'] for q in range(4)]+['P900N0000','P900S0000']
    for tile in tiles:
        dest=LUNAR_ORIGINALS/f'WAC_GLOBAL_{tile}_100M.PYR.TIF'
        if dest.exists():continue
        if COOLDOWN.exists() and time.time()<float(COOLDOWN.read_text()):
            raise RateLimited('PDS cooldown remains active. Retry after '+time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime(float(COOLDOWN.read_text()))))
        part=dest.with_suffix('.part');offset=part.stat().st_size if part.exists() else 0
        with requests.get(PDS+dest.name,headers={'Range':f'bytes={offset}-'} if offset else {},stream=True,timeout=(10,90)) as response:
            if response.status_code==429:
                record_cooldown(response.headers.get('Retry-After','3600'))
                raise RateLimited('PDS requested a download pause; partial originals preserved.')
            response.raise_for_status()
            append=offset>0 and response.status_code==206
            if response.status_code==206 and not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                raise ValueError('Unexpected partial response')
            expected=int(response.headers.get('Content-Length',0));received=0
            with part.open('ab' if append else 'wb') as stream:
                for chunk in response.iter_content(1024*1024):stream.write(chunk);received+=len(chunk)
            if expected and received!=expected:raise ValueError('Incomplete original; resume later')
        os.replace(part,dest);print(dest.name,dest.stat().st_size,flush=True)

if __name__=='__main__':
    try:main()
    except RateLimited as error:raise SystemExit(str(error))
