"""Compare measured terrain against Tacana, with equal-scale blocks.
Run from D:/space: python recursos/scripts/comparar_tacana.py
"""
from pathlib import Path
import ast, json, csv, hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates, binary_erosion
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'comparacion_tacana'
NAMES={'tierra_tacana':'Tacaná','luna_site01':'Luna: Connecting Ridge',
       'luna_site04':'Luna: borde de Shackleton','marte_cerberus':'Marte: Cerberus Tholi'}

def load_grids():
    # Reuse the exact resampling function without executing the old script's main body.
    tree=ast.parse((ROOT/'scripts/analizar_nasa.py').read_text(encoding='utf-8'))
    func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='common_grid')
    scope=dict(np=np,gaussian_filter=gaussian_filter,map_coordinates=map_coordinates,binary_erosion=binary_erosion)
    exec(compile(ast.Module(body=[func],type_ignores=[]),'common_grid','exec'),scope)
    grids={}
    for key in ['tierra_tacana','luna_site01','marte_cerberus']:
        with np.load(ROOT/'analisis_nasa'/f'{key}_100m.npz') as data:
            grids[key]=(data['elevacion_m'].astype(float),data['pendiente_grados'].astype(float))
    source=ROOT/'datos/nasa/luna/site04/Site04_final_adj_5mpp_surf.tif'
    z,s,_,_=scope['common_grid'](np.asarray(Image.open(source),dtype='float32'),5.,5.)
    grids['luna_site04']=(z.astype(float),s.astype(float))
    return grids

def make_blocks(key,z,s,side):
    rows=[]
    for y in range(0,z.shape[0]-side+1,side):
        for x in range(0,z.shape[1]-side+1,side):
            zz=z[y:y+side,x:x+side];ss=s[y:y+side,x:x+side]
            valid=np.isfinite(zz)&np.isfinite(ss)
            if valid.mean()<.9:
                continue
            rows.append(dict(region=key,name=NAMES[key],block_side_m=side*100,x_local_m=x*100,y_local_m=y*100,
                valid_cells=int(valid.sum()),mean_slope_deg=float(ss[valid].mean()),
                local_relief_m=float(np.percentile(zz[valid],95)-np.percentile(zz[valid],5))))
    return rows

def holm(rows):
    last=0.
    for rank,i in enumerate(np.argsort([r['p'] for r in rows])):
        last=max(last,min(1.,(len(rows)-rank)*rows[i]['p']))
        rows[i]['p_holm']=last

def save(name,rows):
    (OUT/(name+'.json')).write_text(json.dumps(rows,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    if isinstance(rows,list) and rows:
        with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    OUT.mkdir(exist_ok=True)
    grids=load_grids();blocks=[];omnibus=[];comparisons=[]
    for side in [10,20]:
        rows=[row for key,(z,s) in grids.items() for row in make_blocks(key,z,s,side)]
        blocks.extend(rows)
        for variable in ['mean_slope_deg','local_relief_m']:
            groups={key:np.array([r[variable] for r in rows if r['region']==key]) for key in grids}
            assert min(map(len,groups.values()))>=3
            test=stats.f_oneway(*groups.values(),equal_var=False)
            omnibus.append(dict(block_side_m=side*100,variable=variable,groups=4,n_blocks=sum(map(len,groups.values())),
                welch_F=float(test.statistic),p=float(test.pvalue),status='conditional exploratory ANOVA; spatial independence unproven'))
            ref=groups['tierra_tacana']
            for key,values in groups.items():
                if key=='tierra_tacana':continue
                test=stats.ttest_ind(values,ref,equal_var=False)
                va=values.var(ddof=1)/len(values);vb=ref.var(ddof=1)/len(ref)
                df=(va+vb)**2/(va**2/(len(values)-1)+vb**2/(len(ref)-1))
                delta=values.mean()-ref.mean();margin=stats.t.ppf(.975,df)*np.sqrt(va+vb)
                pooled=np.sqrt(((len(values)-1)*values.var(ddof=1)+(len(ref)-1)*ref.var(ddof=1))/(len(values)+len(ref)-2))
                g=(1-3/(4*(len(values)+len(ref))-9))*delta/pooled
                comparisons.append(dict(region=key,name=NAMES[key],variable=variable,block_side_m=side*100,
                    n_blocks=len(values),n_reference_blocks=len(ref),reference_mean=float(ref.mean()),region_mean=float(values.mean()),
                    difference_from_tacana=float(delta),absolute_mean_difference=float(abs(delta)),
                    ci95_difference_low=float(delta-margin),ci95_difference_high=float(delta+margin),
                    hedges_g=float(g),wasserstein_distance=float(stats.wasserstein_distance(values,ref)),
                    p=float(test.pvalue),status='Descriptive similarity; p and CI conditional on independent blocks. CI is not multiplicity-adjusted.'))
    holm(omnibus);holm(comparisons)
    for side in [1000,2000]:
        for variable in ['mean_slope_deg','local_relief_m']:
            selected=sorted([r for r in comparisons if r['block_side_m']==side and r['variable']==variable],key=lambda r:r['wasserstein_distance'])
            for rank,r in enumerate(selected,1):r['rank_by_distribution_distance']=rank
    save('bloques',blocks);save('anova',omnibus);save('comparaciones',comparisons)
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,variable,unit in zip(axes,['mean_slope_deg','local_relief_m'],['Pendiente media (grados)','Relieve local P95-P05 (m)']):
        keys=list(grids)
        arrays=[np.array([r[variable] for r in blocks if r['region']==key and r['block_side_m']==1000]) for key in keys]
        ax.boxplot(arrays,tick_labels=[NAMES[k].replace(': ','\n') for k in keys],showfliers=False)
        ax.tick_params(axis='x',labelsize=8)
        ax.set(ylabel=unit,title='Bloques de 1 km; malla de 100 m')
    fig.savefig(OUT/'comparacion.png',dpi=160);plt.close(fig)
    paths=[ROOT/'analisis_nasa'/f'{k}_100m.npz' for k in ['tierra_tacana','luna_site01','marte_cerberus']]
    paths.append(ROOT/'datos/nasa/luna/site04/Site04_final_adj_5mpp_surf.tif')
    provenance=[]
    for p in paths:
        with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        provenance.append(dict(file=str(p),sha256=digest))
    save('metodologia',dict(reference='Copernicus GLO-30 DSM around Tacana; approximately 14 km square; includes vegetation',
        reference_source=json.loads((ROOT/'vista_previa/tacana_fuentes.json').read_text(encoding='utf-8')),
        inputs=provenance,common_grid_m=100,block_sizes_m=[1000,2000],minimum_valid_fraction=.9,
        ranking='Wasserstein distance between block distributions, separately per variable and scale; smaller means closer, not equivalent.',
        limits=['Only three extraterrestrial local datasets tested; not all regions of either body.',
        'Blocks have identical nominal size but different total footprints and numbers of valid blocks.',
        'Different instruments, native resolutions and interpolation; Earth DSM includes vegetation.',
        'Adjacent blocks may remain correlated. Neither ANOVA nor Welch proves equivalence or eliminates spatial dependence.',
        'Absolute elevations are excluded because vertical reference surfaces differ.',
        'No combined similarity percentage or claim of habitability is made.',
        'Temperature, pressure and oxygen are not included in this terrain ranking.']))
    lines=['COMPARACION CONTRA EL TACANA','',
        'Datos de relieve; no es una comparacion de temperatura ni habitabilidad.',
        'Malla comun: 100 m. Bloques de 1 km y sensibilidad a bloques de 2 km.',
        'ANOVA de Welch: Tacana, Connecting Ridge, Shackleton y Cerberus Tholi.',
        'Las comparaciones contra Tacana usan Welch y correccion Holm sobre 12 pruebas.',
        'Orden de parecido: distancia de Wasserstein de las distribuciones de bloques. Menor distancia = mayor parecido descriptivo.',
        'Los p e intervalos son exploratorios: independencia espacial no demostrada.','']
    for r in sorted(comparisons,key=lambda r:(r['block_side_m'],r['variable'],r['rank_by_distribution_distance'])):
        lines.append(f"{r['block_side_m']} m | {r['variable']} | puesto {r['rank_by_distribution_distance']} | {r['name']}: media {r['region_mean']:.3f}, Tacana {r['reference_mean']:.3f}, diferencia {r['difference_from_tacana']:.3f}, distancia distribuciones {r['wasserstein_distance']:.3f}, p Holm {r['p_holm']:.4g}")
    lines+=['','Mayor parecido no significa igualdad. El resultado se limita a las areas y variables analizadas.']
    print('\n'.join(lines))

if __name__=='__main__':main()
