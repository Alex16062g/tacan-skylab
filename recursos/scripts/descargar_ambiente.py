"""NASA PDS environmental data. Moon files are byte-exact longitude subsets."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import requests, json, hashlib, time, threading

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'datos/nasa/ambiente'
MOON = 'https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/'
MARS = 'https://atmos.nmsu.edu/PDS/data/MROM_2227/'
LOCAL = threading.local()

def download(e):
    if not hasattr(LOCAL, 'session'):
        LOCAL.session = requests.Session()
    p = OUT / e['file']
    p.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            if not p.exists():
                h = {'Range': f"bytes={e['start']}-{e['end']}"} if 'start' in e else {}
                with LOCAL.session.get(e['url'], headers=h, timeout=(8,30), stream=True) as r:
                    r.raise_for_status()
                    if h:
                        assert r.status_code == 206
                        assert r.headers.get('Content-Range','').startswith(f"bytes {e['start']}-{e['end']}/")
                    if 'html' in r.headers.get('Content-Type',''):
                        raise ValueError('HTML instead of data')
                    temp = p.with_suffix(p.suffix + '.part')
                    with temp.open('wb') as f:
                        for chunk in r.iter_content(1024*1024):
                            f.write(chunk)
                    if h:
                        assert temp.stat().st_size == e['end']-e['start']+1
                    size = r.headers.get('Content-Length')
                    if size:
                        assert temp.stat().st_size == int(size)
                    temp.replace(p)
            with p.open('rb') as f:
                sha = hashlib.file_digest(f,'sha256').hexdigest()
            return dict(e,status='downloaded',bytes=p.stat().st_size,sha256=sha,verified_utc=datetime.now(timezone.utc).isoformat())
        except Exception as ex:
            error = str(ex)
            time.sleep(.5)
    return dict(e,status='failed',error=error)

def main():
    tasks = []
    for south in range(-90,90,10):
        band = f'{abs(south):02d}s{abs(south+10):02d}s' if south < 0 else f'{south:02d}n{south+10:02d}n'
        stem = f'global_cumul_avg_cyl_{band}_002'
        tasks.append(dict(file=f'moon/{stem}.lbl',url=MOON+stem+'.lbl'))
        for column in range(30,720,60):
            start = 113*(1+column*20*96)
            end = start+113*20*96-1
            tasks.append(dict(file=f'moon/{stem}_col{column:03d}.subset.tab',url=MOON+stem+'.tab',start=start,end=end,longitude_east_deg=-179.75+column*.5,band_south=south))
    for name in ['MCS_DDR1.FMT','MCS_DDR2.FMT']:
        tasks.append(dict(file='mars/'+name,url=MARS+'LABEL/'+name))
    for day in [1,8]:
        for hour in [0,4,8,12,16,20]:
            stem = f'202507{day:02d}{hour:02d}_DDR'
            for ext in ['TAB','LBL']:
                tasks.append(dict(file='mars/'+stem+'.'+ext,url=MARS+f'DATA/2025/202507/202507{day:02d}/'+stem+'.'+ext))
    for hour in [0,4,8,12,16,20]:
        stem = f'20111031{hour:02d}_DDR'
        for ext in ['TAB','LBL']:
            tasks.append(dict(file='mars/'+stem+'.'+ext,url='https://atmos.nmsu.edu/PDS/data/MROM_2062/DATA/2011/201110/20111031/'+stem+'.'+ext))
    # Prioritize the older surface-temperature products, then resume other files.
    tasks.sort(key=lambda e: (0 if '20111031' in e['file'] else 1, e['file']))
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(download,e) for e in tasks]
        for future in as_completed(futures):
            r = future.result()
            results.append(r)
            (OUT/'manifest.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            if len(results)%25 == 0 or r['status'] != 'downloaded':
                print(len(results),'/',len(tasks),r['status'],r['file'],flush=True)
    print('Complete',sum(e['status']=='downloaded' for e in results),'/',len(tasks),flush=True)

if __name__ == '__main__':
    main()
