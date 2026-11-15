from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import json,requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'datos/nasa';OUT.mkdir(parents=True,exist_ok=True)
pages=[
 ('marte','MOLA global y polar','https://pds-geosciences.wustl.edu/missions/mgs/megdr.html'),
 ('luna','LOLA regiones 5 m','https://pgda.gsfc.nasa.gov/products/78'),
 ('luna','LOLA polo sur multiescala','https://pgda.gsfc.nasa.gov/products/90'),
 ('luna','LROC WAC imágenes científicas','https://data.lroc.im-ldi.com/lroc/view_rdr/WAC_HAPKE'),
 ('marte','HiRISE índice acumulativo DTM y ortoimágenes','https://www.uahirise.org/PDS/INDEX/'),
 ('luna','LOLA archivo científico','https://pds-geosciences.wustl.edu/missions/lro/lola.htm'),
]
def gather(p):
 body,family,url=p
 try:
  for attempt in range(3):
   try:
    r=requests.get(url,timeout=(10,30));r.raise_for_status();break
   except requests.RequestException:
    if attempt==2:raise
  soup=BeautifulSoup(r.text,'html.parser');rows=[];seen=set()
  for a in soup.find_all('a',href=True):
   h=urljoin(url,a['href'])
   keep=(family.startswith('MOLA') and ('/meg0' in h or '/meg128' in h or '/polar/' in h)) or ('LOLA_5mpp/' in h and '/Clones/' not in h) or (family.endswith('multiescala') and h.lower().endswith('.tif')) or ('/view_rdr_product/WAC_HAPKE_' in h) or ('DTMCUMINDEX.' in h) or (family.endswith('científico') and '/lrolol_1xxx/data/' in h)
   if keep and h not in seen:rows.append(dict(body=body,family=family,name=a.get_text(' ',strip=True),url=h,status='catalogued_not_downloaded'));seen.add(h)
  return dict(body=body,family=family,source=url,entries=rows,status='catalogued')
 except Exception as e:return dict(body=body,family=family,source=url,status='pending',error=str(e),entries=[])
if __name__=='__main__':
 results=list(ThreadPoolExecutor(3).map(gather,pages))
 catalog={'scope':'Índice seleccionado de elevación, pendientes, soporte e imágenes. No es una réplica completa de todas las misiones NASA. Estado de descargas separado en manifest.json.','families':results,'discovery':[{'name':'NASA PDS buscador','url':'https://pds.nasa.gov/datasearch/data-search/'},{'name':'Moon Orbital Data Explorer','url':'https://ode.rsl.wustl.edu/moon/'},{'name':'Mars Orbital Data Explorer','url':'https://ode.rsl.wustl.edu/mars/'},{'name':'HiRISE catálogo de DTM','url':'https://www.uahirise.org/dtm/'},{'name':'LROC imágenes y DTM NAC','url':'https://data.lroc.im-ldi.com/lroc/search'}]}
 (OUT/'catalogo.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
 print([(r['family'],r['status'],len(r['entries'])) for r in results],flush=True)
