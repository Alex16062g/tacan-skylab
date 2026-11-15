"""Download every catalogued crop, resumably, before building the static demo."""
import json,time,argparse,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from imagenes_catalogo import generate,catalog,OUT
from pds_raster import RateLimited

def html_priority():
    summary=json.loads((Path(__file__).resolve().parents[1]/'comparacion_tacana/similitud_catalogo_resumen.json').read_text(encoding='utf-8'))
    ordered=[]
    for body in ['MOON','MARS']:
        ordered.append((body,summary['selections'][body]['selected_region']))
    for body in ['MOON','MARS']:
        ordered.extend((body,r['region']) for r in summary['selections'][body]['matching_regions'] if r['primary']['similarity_percent']>80)
    return list(dict.fromkeys(ordered))

def task(item):
    body,ident=item
    for attempt in range(3):
        try:
            data=generate(body,ident)
            return dict(region=ident,status='ready',file=data['file'])
        except RateLimited as error:
            return dict(region=ident,status='deferred',error=str(error))
        except Exception as error:
            message=str(error)
            if 'no tiene observaciones' in message:break
            time.sleep(attempt+1)
    return dict(region=ident,status='unavailable' if 'no tiene observaciones' in message else 'failed',error=message)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=2);parser.add_argument('--limit',type=int)
    parser.add_argument('--body',choices=['MOON','MARS'])
    parser.add_argument('--priority-only',action='store_true')
    parser.add_argument('--export-progress',action='store_true')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    items=[(b,f['id']) for b in ([args.body] if args.body else ['MOON','MARS']) for f in sorted(catalog(b).values(),key=lambda f:(f['longitude_east_deg'],f['latitude_deg']))]
    priority=html_priority();rank={item:i for i,item in enumerate(priority)}
    if args.priority_only:items=[item for item in items if item in rank]
    items.sort(key=lambda item:rank.get(item,len(rank)))
    if args.limit:items=items[:args.limit]
    report=OUT/'bulk-status.json';done=json.loads(report.read_text(encoding='utf-8'))['regions'] if report.exists() else {}
    items=[item for item in items if done.get(item[1],{}).get('status')!='ready']
    total=len(items);completed=0
    start=time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(task,item):item for item in items}
        for future in as_completed(jobs):
            try:r=future.result()
            except Exception as e:r=dict(region=jobs[future][1],status='failed',error=str(e))
            done[r['region']]=r
            completed+=1
            if completed%25==0 or completed==total:
                value=dict(total=sum(len(catalog(b)) for b in ['MOON','MARS']),processed=len(done),ready=sum(r['status']=='ready' for r in done.values()),elapsed_s=round(time.time()-start),regions=done)
                report.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
                print(json.dumps({k:v for k,v in value.items() if k!='regions'}),flush=True)
                if args.export_progress:
                    subprocess.run([sys.executable,str(Path(__file__).with_name('exportar_demo_estatica.py')),'--allow-incomplete'],check=True)
    if total==0 and args.export_progress:
        subprocess.run([sys.executable,str(Path(__file__).with_name('exportar_demo_estatica.py')),'--allow-incomplete'],check=True)
    print('Report:',report,flush=True)

if __name__=='__main__':main()
