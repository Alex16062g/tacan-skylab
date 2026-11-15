"""Process actual Diviner and MCS records, keeping missing data and coverage explicit."""
from pathlib import Path
import csv, json, re, io, hashlib
from collections import defaultdict
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'datos/nasa/ambiente'
OUT = ROOT / 'ambiente_luna_marte'

def write_json(name, data):
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def write_csv(name, rows):
    if not rows:
        return
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def sector(lat, lon):
    south=min(60,int(np.floor(lat/30))*30)
    west=int((lon%360)//60)*60
    return f'lat_{south}_{south+30}_lon_{west}_{west+60}'

def phase(hour):
    if 2.5 <= hour < 3.5:
        return 'night_02h30_03h30'
    if 14.5 <= hour < 15.5:
        return 'day_14h30_15h30'
    return f'local_hour_{int(hour):02d}_{int(hour)+1:02d}'

def moon():
    all_rows=[];cells=[]
    for path in sorted((DATA/'moon').glob('*.subset.tab')):
        arr=np.loadtxt(path,delimiter=',',ndmin=2)
        assert arr.shape==(1920,11),path
        # Each subset contains 20 latitudes x 96 local-time bins at one longitude.
        col=int(re.search(r'_col(\d+)',path.name)[1])
        assert np.allclose(arr[:,0],-179.75+col*.5)
        valid=(arr[:,10]>0)&np.isfinite(arr[:,10])
        for lon,lat,hour,*temps in arr[valid]:
            t=temps[-1]
            all_rows.append(dict(latitude_deg=float(lat),longitude_east_deg=float(lon%360),local_solar_time_h=float(hour),temperature_K=float(t),temperature_C=float(t-273.15),source_file=path.name))
        for lat in np.unique(arr[:,1]):
            for label,low,high in [('night_02h30_03h30',2.5,3.5),('day_14h30_15h30',14.5,15.5)]:
                selection=arr[valid&(arr[:,1]==lat)&(arr[:,2]>=low)&(arr[:,2]<high)]
                if len(selection)<2:
                    continue
                lon=float(selection[0,0]%360);temp=float(selection[:,10].mean())
                cells.append(dict(body='MOON',region=sector(lat,lon),phase=label,latitude_deg=float(lat),longitude_east_deg=lon,
                    temperature_C=temp-273.15,temperature_K=temp,n_source_records=len(selection),n_dates=0,
                    observation_period='2009-07-05/2015-04-01 cumulative product',source='LRO-Diviner GCP',temperature_type='surface_bolometric'))
    write_csv('luna_temperaturas_todas_horas.csv',all_rows)
    return cells,len(all_rows)

def mars():
    fmt=(DATA/'mars/MCS_DDR1.FMT').read_text()
    fields={}
    for block in re.findall(r'OBJECT\s*=\s*COLUMN(.*?)END_OBJECT\s*=\s*COLUMN',fmt,re.S):
        name=re.search(r'\bNAME\s*=\s*(\w+)',block)[1]
        start=int(re.search(r'START_BYTE\s*=\s*(\d+)',block)[1])-1
        size=int(re.search(r'\bBYTES\s*=\s*(\d+)',block)[1])
        fields[name]=(start,start+size)
    raw=[];pressure=[];atmosphere=[];groups=defaultdict(list);total=0;rejected=0
    layer_fields={}
    fmt2=(DATA/'mars/MCS_DDR2.FMT').read_text()
    for block in re.findall(r'OBJECT\s*=\s*COLUMN(.*?)END_OBJECT\s*=\s*COLUMN',fmt2,re.S):
        name=re.search(r'\bNAME\s*=\s*(\w+)',block)[1]
        start=int(re.search(r'START_BYTE\s*=\s*(\d+)',block)[1])-1
        size=int(re.search(r'\bBYTES\s*=\s*(\d+)',block)[1])
        layer_fields[name]=(start,start+size)
    for path in sorted((DATA/'mars').glob('*_DDR.TAB')):
        label=path.with_suffix('.LBL')
        if not label.exists():
            continue
        text=label.read_text()
        offset=int(re.search(r'\^TABLE\s*=\s*\([^,]+,\s*(\d+)',text)[1])-1
        size=int(re.search(r'RECORD_BYTES\s*=\s*(\d+)',text)[1])
        count=int(re.search(r'FILE_RECORDS\s*=\s*(\d+)',text)[1])
        with path.open('rb') as f:
            f.seek(offset)
            for _ in range(count):
                record=f.read(size)
                assert len(record)==size,(path,len(record),size)
                def number(name):
                    i,j=fields[name]
                    return float(record[i:j])
                total+=1
                lat,lon=number('SURF_LAT'),number('SURF_LON')%360
                hour=number('LTST')*24
                if not (-90<=lat<=90 and 0<=hour<24):
                    rejected+=1;continue
                temperature=number('T_SURF');err=number('T_SURF_ERR')
                good_geometry=number('GQUAL') in [0,1,2,6,9,12,13,16]
                good_surface=number('SURF_QUAL') in [0,1,2,3] and number('T_QUAL') in [0,1]
                day=path.name[:8]
                # Keep only retrieved pressure; do not present climatological initialization as observation.
                p=number('P_SURF');pe=number('P_SURF_ERR')
                if good_geometry and number('P_QUAL')==0 and p>0 and pe>=0:
                    pressure.append(dict(date=day,latitude_deg=lat,longitude_east_deg=lon,local_solar_time_h=hour,
                        pressure_Pa=p,pressure_uncertainty_Pa=pe,solar_longitude_deg=number('L_S'),source_file=path.name))
                # Layer i=24 has pressure 610*exp(-0.125*(24-10)) = ~106 Pa.
                frame=record[1049+23*161:1049+24*161]
                def layer(name):
                    return float(frame[slice(*layer_fields[name])])
                if good_geometry and layer('1')==0 and layer('T')>0 and layer('T_ERR')>=0 and layer('ALT')>=0:
                    atmospheric=dict(date=day,region=sector(layer('LAT'),layer('LON')),latitude_deg=layer('LAT'),longitude_east_deg=layer('LON')%360,
                        local_solar_time_h=hour,temperature_K=layer('T'),temperature_C=layer('T')-273.15,temperature_uncertainty_K=layer('T_ERR'),
                        pressure_level_Pa=layer('PRES'),altitude_km=layer('ALT'),solar_longitude_deg=number('L_S'),source_file=path.name)
                    atmosphere.append(atmospheric)
                if not (good_geometry and good_surface and temperature>0 and err>=0):
                    rejected+=1;continue
                row=dict(date=day,region=sector(lat,lon),latitude_deg=lat,longitude_east_deg=lon,local_solar_time_h=hour,
                    temperature_K=temperature,temperature_C=temperature-273.15,temperature_uncertainty_K=err,
                    solar_longitude_deg=number('L_S'),surface_quality=number('SURF_QUAL'),geometry_quality=number('GQUAL'),source_file=path.name)
                raw.append(row)
                ph=phase(hour)
                if ph:
                    key=(day[:6],sector(lat,lon),ph,int(np.floor(lat)),int(lon))
                    groups[key].append(row)
    cells=[]
    for (period,region,ph,latbin,lonbin),rows in groups.items():
        temp=float(np.mean([r['temperature_K'] for r in rows]))
        cells.append(dict(body='MARS',region=region,phase=ph,latitude_deg=latbin+.5,longitude_east_deg=lonbin+.5,
            temperature_C=temp-273.15,temperature_K=temp,n_source_records=len(rows),n_dates=len({r['date'] for r in rows}),
                    observation_period=period,source='MRO-MCS DDR; see PDS label version',temperature_type='surface_brightness'))
    atmospheric_groups=defaultdict(list)
    for row in atmosphere:
        ph=phase(row['local_solar_time_h'])
        if ph:
            atmospheric_groups[(row['date'][:6],row['region'],ph,int(np.floor(row['latitude_deg'])),int(row['longitude_east_deg']))].append(row)
    for (period,region,ph,latbin,lonbin),rows in atmospheric_groups.items():
        temp=float(np.mean([r['temperature_K'] for r in rows]))
        cells.append(dict(body='MARS',region=region,phase=ph,latitude_deg=latbin+.5,longitude_east_deg=lonbin+.5,
            temperature_C=temp-273.15,temperature_K=temp,n_source_records=len(rows),n_dates=len({r['date'] for r in rows}),
            observation_period=period,source='MRO-MCS DDR; see PDS label version',temperature_type='atmosphere_at_106Pa'))
    write_csv('marte_temperaturas_observadas.csv',raw)
    write_csv('marte_presion_observada.csv',pressure)
    write_csv('marte_temperatura_atmosferica_106Pa.csv',atmosphere)
    return cells,dict(total_profiles=total,accepted_temperature_profiles=len(raw),rejected_temperature_profiles=rejected,accepted_pressure_profiles=len(pressure),accepted_atmospheric_temperature_profiles=len(atmosphere))

def main():
    OUT.mkdir(exist_ok=True)
    moon_cells,moon_count=moon()
    mars_cells,mars_counts=mars()
    cells=moon_cells+mars_cells
    summaries=[];tests=[]
    for body in ['MOON','MARS']:
        for ph in sorted({r['phase'] for r in cells if r['body']==body}):
            groups=defaultdict(list)
            for row in cells:
                if row['body']==body and row['phase']==ph:
                    groups[(row['temperature_type'],row['observation_period'],row['region'])].append(row['temperature_C'])
            for name,vals in sorted(groups.items()):
                summaries.append(dict(body=body,phase=ph,temperature_type=name[0],observation_period=name[1],region=name[2],n_cells=len(vals),temperature_mean_C=float(np.mean(vals)),
                    temperature_min_C=float(min(vals)),temperature_max_C=float(max(vals)),temperature_sd_C=float(np.std(vals,ddof=1)) if len(vals)>1 else 0.))
            for kind,period in sorted({name[:2] for name in groups}):
                eligible={name[2]:v for name,v in groups.items() if name[:2]==(kind,period) and len(v)>=10 and np.var(v)>0}
                if len(eligible)>=2:
                    result=stats.f_oneway(*eligible.values(),equal_var=False)
                    tests.append(dict(body=body,phase=ph,temperature_type=kind,observation_period=period,n_regions=len(eligible),regions=list(eligible),welch_F=float(result.statistic),p=float(result.pvalue),
                        status='exploratory only; spatial dependence, latitude, temporal coverage and sampling differences remain'))
    from validar_anova_espacial import holm
    holm(tests,'p','p_holm')
    write_csv('temperaturas_para_python.csv',cells)
    write_json('temperaturas.json',{body:[r for r in cells if r['body']==body] for body in ['MOON','MARS']})
    write_json('resumen_temperaturas.json',summaries)
    write_json('anova_temperatura_exploratorio.json',tests)
    write_json('atmosfera_referencia.json',{
        'MOON':{'Atmosphere Type':'Exosphere','Breathable Atmosphere':False,
            'Regional Oxygen Measurements Available In This Download':False,
            'Source':'https://science.nasa.gov/moon/lunar-atmosphere/'},
        'MARS':{'Breathable Atmosphere':False,'Oxygen By Volume (%)':0.16,
            'Carbon Dioxide By Volume (%)':95,'Nitrogen By Volume (%)':2.6,'Argon By Volume (%)':1.9,
            'Scope':'Rounded atmospheric composition reported from Curiosity SAM at Gale; not a regional map or constant over time',
            'Source':'https://www.nasa.gov/missions/with-mars-methane-mystery-unsolved-curiosity-serves-scientists-a-new-one-oxygen/'},
        'ANOVA Eligible':False,'Reason':'Contextual references, not independent regional oxygen observations. No synthetic zero oxygen samples.'})
    manifest=json.loads((DATA/'manifest.json').read_text())
    report=dict(moon_valid_local_time_bins=moon_count,moon_spatial_cells_by_phase=len(moon_cells),mars_spatial_cells_by_phase=len(mars_cells),
        **mars_counts,downloaded_files=sum(e['status']=='downloaded' for e in manifest),pending_files=[e['file'] for e in manifest if e['status']!='downloaded'],
        temperature_units='Kelvin and Celsius; C = K - 273.15',moon_definition='Bolometric brightness temperature, not air temperature',
        mars_definition='Surface brightness temperatures where reported; separate atmospheric temperatures at approximately 106 Pa. Never pool temperature_type values.',
        moon_sampling='12 longitude strips at 30-degree intervals, 0.5-degree latitude cells, 96 local-time bins; not an exhaustive lunar map',
        mars_sampling='Selected days in July 2025 and October 2011; consult downloaded files and per-row periods. Not all seasons or complete spatial coverage.',
        comparison_limits=['Do not pool Moon and Mars temperatures as equivalent observations: different epochs, spectral definitions and sampling.',
        'A spatial cell has one mean per selected phase; lunar missing bins excluded, at least two valid bins required.',
        'Mars pressure rows exclude P_QUAL=9 (climatological pressure); retained P_QUAL=0 only.',
        'Raw temperature flags and uncertainties are retained; additional instrument-specific screening may be required.',
        'Regional oxygen measurements are unavailable in these downloads. A fixed oxygen reference cannot support regional ANOVA.',
        'No confirmatory ANOVA claim: spatial correlation and season/local-time confounding remain.'])
    write_json('cobertura_y_metodologia.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
