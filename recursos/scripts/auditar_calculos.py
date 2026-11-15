"""Reproducible numerical audit; not scientific or institutional certification."""
import json, hashlib, sys
from pathlib import Path
import numpy as np
import scipy
from scipy import stats
from comparar_catalogo_completo import descriptors, EAST, NORTH, compare
from calcular_similitud import affinity
from comparar_tacana import holm
from ampliar_catalogo_regiones import sample
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'recursos/comparacion_tacana'
checks=[]
def check(name,condition,details=None):
    checks.append(dict(name=name,passed=bool(condition),details=details))
def close(a,b):return bool(np.allclose(a,b,rtol=1e-10,atol=1e-10))
def w1(a,b):
    a=np.sort(a);b=np.sort(b);x=np.unique(np.r_[a,b])
    return float(np.sum(np.abs(np.searchsorted(a,x[:-1],side='right')/len(a)-np.searchsorted(b,x[:-1],side='right')/len(b))*np.diff(x)))
def welch(groups):
    n=np.array([len(g) for g in groups]);m=np.array([np.mean(g) for g in groups]);v=np.array([np.var(g,ddof=1) for g in groups]);k=len(n)
    w=n/v;mean=np.sum(w*m)/sum(w);c=np.sum((1-w/sum(w))**2/(n-1))
    f=np.sum(w*(m-mean)**2)/(k-1)/(1+2*(k-2)*c/(k*k-1))
    return float(f),float(stats.f.sf(f,k-1,(k*k-1)/(3*c)))
check('affinity known cases',close([affinity(0,2),affinity(2,2),affinity(6,2)],[100,50,25]))
check('affinity extreme finite inputs',np.isfinite(affinity(1e308,1e-308)) and affinity(1e308,1e-308)>=0)
for distance,sd in [(-1,1),(1,0),(np.nan,1),(1,np.inf)]:
    try:affinity(distance,sd);rejected=False
    except ValueError:rejected=True
    check(f'invalid affinity rejected {distance} {sd}',rejected)
grid=np.arange(32,dtype=float).reshape(4,8)
check('longitude seam periodic',close(sample(grid,np.array([0.,0.,0.]),np.array([-1.,359.,719.])),sample(grid,np.array([0.,0.,0.]),np.array([359.,359.,359.]))))
check('pole clamp no north south wrap',close(sample(grid,np.array([90.,-90.]),np.array([22.5,22.5])),[0,24]))
for spacing in [2000,3000]:
    flat=descriptors(np.zeros((1,*EAST.shape)),spacing)
    check(f'flat terrain {spacing}',all(close(v,0) for v in flat.values()))
    plane=descriptors((.1*EAST+.2*NORTH)[None],spacing)
    check(f'analytic plane slope {spacing}',close(plane['mean_slope_deg'],np.degrees(np.arctan(np.hypot(.1,.2)))) )
    check(f'analytic plane TPI {spacing}',close(plane['tpi_m'],0))
    expected=np.sqrt(sum((spacing*(.1*x+.2*y))**2 for x in [-1,0,1] for y in [-1,0,1]))
    check(f'analytic plane Riley TRI {spacing}',close(plane['tri_m'],expected))
    shifted=descriptors((.1*EAST+.2*NORTH+10000)[None],spacing)
    check(f'vertical datum shift invariant {spacing}',all(close(plane[k],shifted[k]) for k in plane))
    try:descriptors(np.full((1,*EAST.shape),np.nan),spacing);rejected=False
    except ValueError:rejected=True
    check(f'missing terrain rejected {spacing}',rejected)
p=[{'p':.01},{'p':.04},{'p':.03}];holm(p)
check('Holm known case',close([r['p_holm'] for r in p],[.03,.06,.06]))
summary=json.loads((OUT/'similitud_catalogo_resumen.json').read_text(encoding='utf-8'))
counts={};sensitivity={};failures=[]
for body in ['MOON','MARS']:
    rows=json.loads((OUT/f'similitud_catalogo_{body.lower()}.json').read_text(encoding='utf-8'))['regions']
    evaluated=[r for r in rows if r['primary']];counts[body]=len(evaluated)
    for r in evaluated:
        for key,spacing in [('primary',2000),('sensitivity',3000)]:
            result=r[key]
            if not result:continue
            ref=summary['reference']['samples'][str(spacing)];total=0
            for f in result['features']:
                a=np.asarray(f['samples']);b=np.asarray(ref[f['variable']]);d=w1(a,b);sd=np.std(b,ddof=1)
                score=100/(1+d/sd)
                expected_weight=.5 if f['variable'] in ['mean_slope_deg','local_relief_m'] else 0.
                if not(close(d,f['wasserstein_distance']) and close(sd,f['reference_sd']) and close(score,f['similarity_percent']) and close(f['weight'],expected_weight) and np.isfinite(a).all()):failures.append([r['region'],key,f['variable']])
                total+=f['weight']*score
            if not close(total,result['similarity_percent']):failures.append([r['region'],key,'total'])
    primary=sorted(evaluated,key=lambda r:-r['primary']['similarity_percent'])
    secondary=sorted([r for r in evaluated if r['sensitivity']],key=lambda r:-r['sensitivity']['similarity_percent'])
    deltas=[abs(r['primary']['similarity_percent']-r['sensitivity']['similarity_percent']) for r in secondary]
    sensitivity[body]=dict(primary_winner=primary[0]['name'],secondary_winner=secondary[0]['name'],median_absolute_change=float(np.median(deltas)),maximum_absolute_change=float(max(deltas)),above80_primary=sum(r['primary']['similarity_percent']>80 for r in primary),above80_secondary=sum(r['sensitivity']['similarity_percent']>80 for r in secondary))
    check(f'{body} winner agrees with summary',primary[0]['region']==summary['selections'][body]['selected_region'])
check('all stored catalogue distances, dispersions and scores',not failures,dict(counts=counts,failures=failures[:20]))
blocks=json.loads((OUT/'bloques.json').read_text(encoding='utf-8'))
rows=json.loads((OUT/'anova.json').read_text(encoding='utf-8'))
for row in rows:
    selected=[b for b in blocks if b['block_side_m']==row['block_side_m']]
    groups=[np.array([b[row['variable']] for b in selected if b['region']==name]) for name in sorted(set(b['region'] for b in selected))]
    f,p=welch(groups)
    check(f"local Welch {row['block_side_m']} {row['variable']}",close(f,row['welch_F']) and np.isclose(p,row['p'],rtol=1e-9,atol=0))
def read(name):return json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))
def paircheck(a,b,row,label,distance_key):
    va=np.var(a,ddof=1)/len(a);vb=np.var(b,ddof=1)/len(b)
    df=(va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1))
    delta=np.mean(a)-np.mean(b);se=np.sqrt(va+vb)
    p=2*stats.t.sf(abs(delta/se),df);margin=stats.t.ppf(.975,df)*se
    check(label,close([delta-margin,delta+margin,w1(a,b)],[row['ci95_difference_low'],row['ci95_difference_high'],row[distance_key]]) and np.isclose(p,row['p'],rtol=1e-9,atol=0))
for row in read('comparaciones'):
    def vals(region):return np.array([b[row['variable']] for b in blocks if b['block_side_m']==row['block_side_m'] and b['region']==region])
    paircheck(vals(row['region']),vals('tierra_tacana'),row,f"terrain pair {row['region']} {row['block_side_m']} {row['variable']}",'wasserstein_distance')
thermal_ref=read('temperatura_referencia_tacana');thermal_samples=read('temperatura_muestras_planetarias')
def thermal_groups(body,phase):
    selected=[r for r in thermal_samples if r['body']==body and r['phase']==phase]
    groups={name:np.array([r['temperature_C'] for r in selected if r['region']==name]) for name in set(r['region'] for r in selected)}
    return {k:v for k,v in groups.items() if len(v)>=10 and np.var(v)>0}
for row in read('temperatura_anova'):
    ref=np.array([r['temperature_C'] for r in thermal_ref if r['phase']==row['phase']])
    f,p=welch([ref,*thermal_groups(row['body'],row['phase']).values()])
    check(f"thermal Welch {row['body']} {row['phase']}",close(f,row['welch_F']) and np.isclose(p,row['p'],rtol=1e-9,atol=0))
for row in read('temperatura_comparaciones'):
    ref=np.array([r['temperature_C'] for r in thermal_ref if r['phase']==row['phase']])
    a=thermal_groups(row['body'],row['phase'])[row['region']]
    paircheck(a,ref,row,f"thermal pair {row['body']} {row['phase']} {row['region']}",'distribution_distance_C')
for name in ['anova','comparaciones','temperatura_anova','temperatura_comparaciones']:
    rows=read(name);order=np.argsort([r['p'] for r in rows]);expected=np.maximum.accumulate([min(1.,(len(rows)-i)*rows[j]['p']) for i,j in enumerate(order)])
    check(f'persisted Holm {name}',np.allclose(expected,[rows[j]['p_holm'] for j in order],rtol=1e-9,atol=0))
for body,item in summary['sources'].items():
    path=ROOT/item['source']
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    check(f'{body} source hash',digest==item['sha256'])
ref=summary['reference']
with (ROOT/ref['source']).open('rb') as stream:check('Tacana source hash',hashlib.file_digest(stream,'sha256').hexdigest()==ref['sha256'])
result=dict(scope='Numerical audit of stored full-catalogue scores, local and thermal Welch ANOVA, pairwise p-values and confidence intervals, Holm corrections and synthetic terrain operators. Not an end-to-end reprocessing.',python=sys.version,numpy=np.__version__,scipy=scipy.__version__,checks=checks,sensitivity=sensitivity,passed=all(c['passed'] for c in checks),limitations=['Spatial independence not demonstrated','Index has no external calibration; 80 is a project threshold','Thermal measurements differ in physical definition and temporal support','No uncertainty propagation or equivalence margins validated','Source hashes demonstrate consistency, not original acquisition correctness'])
(OUT/'auditoria_numerica.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
raise SystemExit(0 if result['passed'] else 1)
