"""Search the downloaded official HiRISE cumulative index; optionally download matches.
Example: python scripts/buscar_regiones.py --texto Olympus --limite 5
"""
from pathlib import Path
import argparse,json,re,csv,io
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'datos/nasa'
def read_index():
 text=(DATA/'marte/indices/DTMCUMINDEX.LBL').read_text()
 fields=[]
 for column in re.findall(r'OBJECT\s*=\s*COLUMN\b(.*?)END_OBJECT',text,re.S):
  name=re.search(r'NAME\s*=\s*(\w+)',column)[1]
  start=int(re.search(r'START_BYTE\s*=\s*(\d+)',column)[1])-1
  count=int(re.search(r'\bBYTES\s*=\s*(\d+)',column)[1])
  fields.append((name,start,count))
 length=int(re.search(r'RECORD_BYTES\s*=\s*(\d+)',text)[1]);expected=int(re.search(r'FILE_RECORDS\s*=\s*(\d+)',text)[1])
 raw=(DATA/'marte/indices/DTMCUMINDEX.TAB').read_bytes()
 assert len(raw)==length*expected,'Index length does not match its label'
 rows=[]
 for values in csv.reader(io.StringIO(raw.decode('ascii'))):
  # Some fixed-width offsets in the published label truncate product paths.
  # The archive's quoted comma delimiters preserve complete fields.
  assert len(values)==len(fields),'Column definitions do not match index'
  r={field[0]:value.strip() for field,value in zip(fields,values)}
  r['url']=urljoin('https://www.uahirise.org/PDS/',r['FILE_NAME_SPECIFICATION'])
  rows.append(r)
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--texto',default='');p.add_argument('--limite',type=int,default=10);p.add_argument('--descargar',action='store_true');p.add_argument('--exportar',action='store_true');a=p.parse_args()
 rows=read_index()
 if a.exportar:
  (DATA/'hirise_regiones.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('Índice exportado:',len(rows))
 selected=[r for r in rows if a.texto.casefold() in (r['RATIONALE_DESC']+' '+r['PRODUCT_ID']).casefold()][:a.limite]
 print(json.dumps([{k:r.get(k) for k in ['PRODUCT_ID','RATIONALE_DESC','DATA_TYPE','MAP_SCALE','MINIMUM_LATITUDE','MAXIMUM_LATITUDE','url']} for r in selected],ensure_ascii=False,indent=2))
 if a.descargar:
  from descargar_nasa import download
  manifest=DATA/'manifest.json';records=json.loads(manifest.read_text(encoding='utf-8'))
  for r in selected:
   e=dict(body='marte',group='seleccion',file='marte/seleccion/'+r['url'].rsplit('/',1)[1],url=r['url'],purpose=r['RATIONALE_DESC'])
   result=download(e);records=[x for x in records if x['file']!=result['file']]+[result]
   manifest.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
