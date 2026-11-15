"""Download a documented starter set; never claims to mirror the NASA archive.
Rerun to retry incomplete downloads. Completed files are SHA-256 checked.
"""
from pathlib import Path
import concurrent.futures, hashlib, json, time
from datetime import datetime,timezone
import requests
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'datos/nasa';OUT.mkdir(parents=True,exist_ok=True)
MOLA='https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg032/'
HIRISE='https://www.uahirise.org/PDS/DTM/ESP/ORB_044100_044199/ESP_044184_1850_ESP_044039_1850/'
LOLA='https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/'
sources=[]
def add(body,group,name,url,purpose):sources.append(dict(body=body,group=group,file=f'{body}/{group}/{name}',url=url,purpose=purpose))
add('luna','global','ldem_16.tif','https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_16.tif','Elevación LOLA global; float32 km; 16 px/grado; referencia 1737.4 km')
for stem,purpose in [('megt90n000fb','Elevación MOLA global; 32 px/grado; metros respecto al areoide GMM3'),('megc90n000fb','Conteos MOLA: identifica celdas sin observaciones directas')]:
 for ext in ['img','lbl','xml','hdr']:add('marte','global',stem+'.'+ext,MOLA+stem+'.'+ext,purpose)
for suffix,purpose in [('surf','Elevación regional LOLA 5 m/píxel; incluye interpolación'),('slp','Pendiente regional publicada, grados'),('ldec','Conteo de observaciones; máscara de soporte'),('toterr','Incertidumbre vertical RMS, metros')]:
 name=f'Site01_final_adj_5mpp_{suffix}.tif';add('luna','site01',name,LOLA+name,purpose)
add('luna','site01','README.txt','https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/README','Documentación regional')
add('marte','cerberus','DTEED_044184_1850_044039_1850_A01.IMG',HIRISE+'DTEED_044184_1850_044039_1850_A01.IMG','DTM HiRISE: Summit of One of Cerberus Tholi; escala exacta en etiqueta adjunta')
for ext in ['JP2','LBL']:
 name='ESP_044184_1850_RED_D_01_ORTHO.'+ext;add('marte','cerberus',name,HIRISE+name,'Ortoimagen HiRISE banda RED; no es elevación')
# A browse image is explicitly not a calibrated scientific image.
add('luna','imagen_contexto','lroc_color_poles_2k.tif','https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_2k.tif','Solo contexto visual NASA SVS; NO para análisis radiométrico')
for ext in ['LBL','TAB']:add('marte','indices','DTMCUMINDEX.'+ext,'https://www.uahirise.org/PDS/INDEX/DTMCUMINDEX.'+ext,'Índice acumulativo oficial de DTM y ortoimágenes HiRISE; no contiene los rasters completos')
LROC='https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DATA/MDR/WAC_HAPKE/'
add('luna','imagen_cientifica','WAC_HAPKE_566NM_E350N0450.IMG',LROC+'WAC_HAPKE_566NM_E350N0450.IMG','Mosaico LROC WAC fotométricamente normalizado I/F; 566 nm; 400 m; 0–70 N, 0–90 E; etiqueta adjunta')
add('luna','imagen_cientifica','WAC_HAPKE_README.TXT',LROC+'WAC_HAPKE_README.TXT','Documentación científica del mosaico WAC')
manifest=OUT/'manifest.json'
old={x['file']:x for x in json.loads(manifest.read_text(encoding='utf-8'))} if manifest.exists() else {}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def download(entry):
 e=entry.copy();path=OUT/e['file'];path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and e['file'] in old and old[e['file']].get('sha256')==sha(path):return old[e['file']]
 for attempt in range(3):
  try:
   with requests.get(e['url'],stream=True,timeout=(12,45)) as r:
    r.raise_for_status()
    if 'text/html' in r.headers.get('Content-Type',''):raise ValueError('HTML returned instead of data')
    size=int(r.headers.get('Content-Length',0));partial=path.with_suffix(path.suffix+'.part')
    with partial.open('wb') as f:
     for block in r.iter_content(1024*1024):f.write(block)
    if size and partial.stat().st_size!=size:raise ValueError('Incomplete Content-Length')
    partial.replace(path)
   e.update(status='downloaded',bytes=path.stat().st_size,sha256=sha(path),retrieved_utc=datetime.now(timezone.utc).isoformat())
   print('OK',e['file'],e['bytes'],flush=True);return e
  except Exception as error:
   e.update(status='pending',error=f'{type(error).__name__}: {error}')
   if isinstance(error,requests.HTTPError) and error.response.status_code==404:break
   time.sleep(1)
 print('PENDING',e['file'],flush=True);return e
if __name__=='__main__':
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for result in pool.map(download,sources):
   results.append(result)
   # Save partial progress even if the run is interrupted.
   merged={**old,**{r['file']:r for r in results}}
   manifest.write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2),encoding='utf-8')
 print('Completed',sum(r['status']=='downloaded' for r in results),'/',len(results),flush=True)
