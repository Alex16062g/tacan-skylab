"""Exploratory surface-temperature comparison; no equivalence or habitability claim."""
from pathlib import Path
import csv,json
from collections import defaultdict
import numpy as np
from PIL import Image
from scipy import stats
from comparar_tacana import holm

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'datos/tacana_temperatura'
OUT=ROOT/'comparacion_tacana'

def sector(lat,lon):
    return f'lat_{min(60,int(np.floor(lat/30))*30)}_{min(60,int(np.floor(lat/30))*30)+30}_lon_{int((lon%360)//60)*60}_{int((lon%360)//60)*60+60}'

def main():
    OUT.mkdir(exist_ok=True)
    item=json.loads((DATA/'stac_aqua.json').read_text())
    transform=item['properties']['proj:transform']
    yy,xx=np.indices(item['properties']['proj:shape'])
    lat=np.degrees((transform[5]+(yy+.5)*transform[4])/6371007.181)
    lon=np.degrees((transform[2]+(xx+.5)*transform[0])/(6371007.181*np.cos(np.radians(lat))))
    bounds=json.loads((ROOT/'vista_previa/tacana_fuentes.json').read_text(encoding='utf-8'))['sample_bounds_wsen']
    area=(lon>=bounds[0])&(lat>=bounds[1])&(lon<=bounds[2])&(lat<=bounds[3])
    reference=[];summaries=[];comparisons=[];tests=[];samples=[]
    lunar=list(csv.DictReader((ROOT/'ambiente_luna_marte/luna_temperaturas_todas_horas.csv').open(encoding='utf-8')))
    martian=list(csv.DictReader((ROOT/'ambiente_luna_marte/marte_temperaturas_observadas.csv').open(encoding='utf-8')))
    for phase,band,low,high in [('day','Day',12.,14.),('night','Night',1.,2.)]:
        raw=np.asarray(Image.open(DATA/f'LST_{band}_1km.tif'))
        quality=np.asarray(Image.open(DATA/f'QC_{band}.tif'))
        hour=np.asarray(Image.open(DATA/f'{band}_view_time.tif'))*.1
        # Include good and other-produced QA, require detailed data QA=0 and error class <=2 K.
        mask=area&(raw>=7500)&((quality&3)<=1)&(((quality>>2)&3)==0)&(((quality>>6)&3)<=1)&(hour>=low)&(hour<high)
        ref=raw[mask]*.02-273.15
        assert len(ref)>=10
        for y,x in zip(*np.where(mask)):
            reference.append(dict(phase=phase,latitude_deg=float(lat[y,x]),longitude_east_deg=float(lon[y,x]),temperature_C=float(raw[y,x]*.02-273.15),
                local_time_h=float(hour[y,x]),qc=int(quality[y,x]),period='2011-10-24/2011-10-31',source=item['id']))
        summaries.append(dict(phase=phase,n_reference_pixels=len(ref),temperature_mean_C=float(ref.mean()),temperature_sd_C=float(ref.std(ddof=1)),
            min_local_time=float(hour[mask].min()),max_local_time=float(hour[mask].max()),
            good_mandatory_QA_pixels=int(np.sum(mask&((quality&3)==0))),other_produced_QA_pixels=int(np.sum(mask&((quality&3)==1))),
            area_pixels=int(area.sum()),window_hours=[low,high]))
        for body,records in [('MOON',lunar),('MARS',martian)]:
            cells=defaultdict(list)
            for row in records:
                h=float(row['local_solar_time_h'])
                if not low<=h<high:continue
                if body=='MARS' and row['date']!='20111031':continue
                la=float(row['latitude_deg']);lo=float(row['longitude_east_deg'])%360
                key=(sector(la,lo),la,lo) if body=='MOON' else (sector(la,lo),int(np.floor(la))+.5,int(lo)+.5)
                cells[key].append(float(row['temperature_C']))
            groups=defaultdict(list)
            for (region,la,lo),values in cells.items():
                if body=='MOON' and len(values)<2:continue
                value=float(np.mean(values));groups[region].append(value)
                samples.append(dict(body=body,phase=phase,region=region,latitude_deg=la,longitude_east_deg=lo,temperature_C=value,n_source_records=len(values)))
            groups={k:np.asarray(v) for k,v in groups.items() if len(v)>=10 and np.var(v)>0}
            if not groups:continue
            test=stats.f_oneway(ref,*groups.values(),equal_var=False)
            tests.append(dict(body=body,phase=phase,groups_including_tacana=1+len(groups),welch_F=float(test.statistic),p=float(test.pvalue)))
            for region,values in groups.items():
                pair=stats.ttest_ind(values,ref,equal_var=False)
                va=values.var(ddof=1)/len(values);vb=ref.var(ddof=1)/len(ref)
                df=(va+vb)**2/(va**2/(len(values)-1)+vb**2/(len(ref)-1))
                delta=values.mean()-ref.mean();margin=stats.t.ppf(.975,df)*np.sqrt(va+vb)
                comparisons.append(dict(body=body,phase=phase,region=region,n_cells=len(values),n_reference_pixels=len(ref),
                    reference_mean_C=float(ref.mean()),region_mean_C=float(values.mean()),difference_C=float(delta),
                    ci95_difference_low=float(delta-margin),ci95_difference_high=float(delta+margin),
                    distribution_distance_C=float(stats.wasserstein_distance(values,ref)),p=float(pair.pvalue)))
    holm(tests);holm(comparisons)
    for ph in ['day','night']:
        selected=sorted([r for r in comparisons if r['phase']==ph],key=lambda r:r['distribution_distance_C'])
        for rank,r in enumerate(selected,1):r['descriptive_rank']=rank
    for name,rows in [('temperatura_referencia_tacana',reference),('temperatura_resumen_tacana',summaries),('temperatura_muestras_planetarias',samples),('temperatura_anova',tests),('temperatura_comparaciones',comparisons)]:
        (OUT/(name+'.json')).write_text(json.dumps(rows,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        if rows:
            with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    limits=['Temperature matching is descriptive, not a test of physical equivalence: MODIS land-surface, Diviner bolometric and MCS brightness temperatures have different spectral definitions.',
        'Tacana is the approximately 14 km square around the volcano, not only the summit. Its product is an 8-day clear-sky composite.',
        'Mars: October 31 2011; Earth: October 24-31 2011; Moon: cumulative 2009-2015. Seasons and illumination geometry are not controlled.',
        'Day window 12-14 local solar hours; night window 1-2. Actual within-window sampling differs.',
        'QC accepts mandatory good OR other-produced, detailed QA=0 and nominal error class <=2K. Daytime reference includes other-produced QA; do not label all pixels highest quality.',
        'Terrestrial pixels, lunar 0.5-degree samples and Martian 1-degree aggregates have different spatial supports. No resampling creates independent observations.',
        'p values and unadjusted confidence intervals assume independent units and remain exploratory; Holm corrects multiple tests, not spatial correlation.',
        'Smaller distribution distance means closer observed temperatures in the selected sample; it is not a percentage of similarity, equivalence or habitability.',
        'Oxygen and pressure are not included in this ranking; no regional terrestrial oxygen data were supplied.']
    (OUT/'temperatura_metodologia.json').write_text(json.dumps(dict(product=item['id'],source='https://doi.org/10.5067/MODIS/MYD11A2.061',mirror='Microsoft Planetary Computer',reference_bounds=bounds,limits=limits),indent=2),encoding='utf-8')
    print(json.dumps(dict(reference=summaries,anova=tests,best=[r for r in comparisons if r['descriptive_rank']==1]),indent=2))

if __name__=='__main__':main()
