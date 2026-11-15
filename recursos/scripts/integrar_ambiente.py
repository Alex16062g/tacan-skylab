"""Combine environmental evidence without mixing surface, air, level or global constants."""
from pathlib import Path
from collections import defaultdict
import csv, json, hashlib, math
import requests
import numpy as np
from comparar_temperatura_tacana import sector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'recursos/comparacion_tacana'
RAW=ROOT/'recursos/datos/tacana_ambiente'
LABELS={'T2M':'Temperatura del aire a 2 m','T2M_MIN':'Mínima diaria del aire a 2 m',
        'T2M_MAX':'Máxima diaria del aire a 2 m','RH2M':'Humedad relativa a 2 m',
        'PS':'Presión superficial','WS2M':'Viento a 2 m','PRECTOTCORR':'Precipitación diaria',
        'ALLSKY_SFC_SW_DWN':'Energía solar diaria en superficie',
        'TOA_SW_DWN':'Energía solar diaria sobre la atmósfera'}

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def stats(values):
    a=np.asarray([float(v) for v in values if v is not None and math.isfinite(float(v))],float)
    return dict(n=len(a),min=float(a.min()),max=float(a.max()),mean=float(a.mean()),
                sd=float(a.std(ddof=1)) if len(a)>1 else None) if len(a) else None

def main():
    RAW.mkdir(exist_ok=True)
    if not (RAW/'power_daily.json').exists():
        params=dict(parameters=','.join(LABELS),community='RE',longitude=-92.109,latitude=15.132,
                    start='20111024',end='20111031',format='JSON',**{'time-standard':'UTC'})
        r=requests.get('https://power.larc.nasa.gov/api/temporal/daily/point',params=params,timeout=60);r.raise_for_status()
        write(RAW/'power_daily.json',r.json());write(RAW/'source.json',dict(url=r.url))
    power=read(RAW/'power_daily.json');parameters=power['properties']['parameter']
    daily=[];power_summary=[]
    for key,label in LABELS.items():
        samples=[]
        for date,value in parameters[key].items():
            if value==power['header']['fill_value'] or not math.isfinite(value):continue
            samples.append(value);daily.append(dict(date=date,variable=key,value=value,unit=power['parameters'][key]['units']))
        power_summary.append(dict(variable=key,label=label,unit=power['parameters'][key]['units'],statistics=stats(samples)))
    summary=read(OUT/'similitud_catalogo_resumen.json')
    reference=read(OUT/'temperatura_referencia_tacana.json')
    samples=read(OUT/'temperatura_muestras_planetarias.json')
    comparisons=read(OUT/'temperatura_comparaciones.json')
    pressure=list(csv.DictReader((ROOT/'recursos/ambiente_luna_marte/marte_presion_observada.csv').open(encoding='utf-8')))
    atmosphere=list(csv.DictReader((ROOT/'recursos/ambiente_luna_marte/marte_temperatura_atmosferica_106Pa.csv').open(encoding='utf-8')))
    grouped={}
    for key,rows,value in [('pressure',pressure,'pressure_Pa'),('air_106Pa',atmosphere,'temperature_C')]:
        groups=defaultdict(list)
        for row in rows:
            groups[(sector(float(row['latitude_deg']),float(row['longitude_east_deg'])),row['date'])].append(row)
        grouped[key]=[dict(sector=s,date=d,statistics=stats([r[value] for r in rs]),samples=rs) for (s,d),rs in sorted(groups.items())]
    result=dict(version=1,environmental_similarity_percent=None,
        reference_power=dict(source=read(RAW/'source.json')['url'],header=power['header'],
            coordinates=power['geometry']['coordinates'],cell_elevation_m=power['geometry']['coordinates'][2],
            summit_elevation_m=4064,period='2011-10-24 / 2011-10-31',
            scope='NASA POWER grid cell; not summit measurements or climate normals',
            statistics=power_summary,daily_records=daily),
        atmosphere_context=read(ROOT/'recursos/ambiente_luna_marte/atmosfera_referencia.json'),
        thermal_methodology=read(OUT/'temperatura_metodologia.json'),
        existing_thermal_comparisons=comparisons,
        existing_thermal_anova=read(OUT/'temperatura_anova.json'),
        mars_pressure_by_sector_date=grouped['pressure'],
        mars_atmospheric_temperature_by_sector_date=grouped['air_106Pa'],bodies={},
        limitations=['No environmental score is added to the terrain index.',
                    'POWER grid elevation is not the Tacana summit. Eight days are not a climate normal.',
                    'Planetary temperature and pressure sectors are 30 degrees latitude by 60 degrees longitude, not 12 km named regions.',
                    'Surface brightness, bolometric, air at 2 m and atmosphere at 106 Pa are distinct variables.',
                    'Daily horizontal solar energy in kWh/m2/day is not normal-incidence extraterrestrial irradiance in W/m2.',
                    'No local Moon/Mars surface solar, humidity, precipitation or wind observations in the downloaded inputs.',
                    'Thermal ANOVA results are exploratory: different dates, sensors, spatial supports and correlated samples.'])
    for r in summary['regions']:
        body=r['body'];s=sector(r['location']['latitude'],r['location']['longitude']);thermal=[]
        for phase in ['day','night']:
            a=[v['temperature_C'] for v in reference if v['phase']==phase]
            b=[v['temperature_C'] for v in samples if v['body']==body and v['region']==s and v['phase']==phase]
            pair=next((v for v in comparisons if v['body']==body and v['region']==s and v['phase']==phase),None)
            thermal.append(dict(phase=phase,unit='°C',tacana=stats(a),planetary=stats(b),
                status='sector_context_only' if b else 'no_sector_observations_in_time_window',
                comparison=pair,reference_period='2011-10-24 / 2011-10-31',
                planetary_period='2009-07-05 / 2015-04-01 (acumulado)' if body=='MOON' else '2011-10-31'))
        irradiance=1361. if body=='MOON' else 586.2
        result['bodies'][body]=dict(selected_region=r['region'],name=r['name'],sector=s,thermal=thermal,
            pressure=[v for v in grouped['pressure'] if v['sector']==s] if body=='MARS' else [],
            atmospheric_temperature_106Pa=[v for v in grouped['air_106Pa'] if v['sector']==s] if body=='MARS' else [],
            solar_reference=dict(earth_W_m2=1361.,body_W_m2=irradiance,difference_W_m2=irradiance-1361.,
                scope='Reference extraterrestrial irradiance, normal to solar rays; not local surface radiation',
                source=f'https://nssdc.gsfc.nasa.gov/planetary/factsheet/{"moon" if body=="MOON" else "mars"}fact.html'))
    sources=[RAW/'power_daily.json',OUT/'temperatura_muestras_planetarias.json',OUT/'temperatura_referencia_tacana.json',
             ROOT/'recursos/ambiente_luna_marte/marte_presion_observada.csv',ROOT/'recursos/ambiente_luna_marte/marte_temperatura_atmosferica_106Pa.csv']
    result['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    write(OUT/'ambiente_integrado.json',result)
    print(json.dumps(dict(power_daily_records=len(daily),thermal_tests=len(comparisons),pressure_sector_dates=len(grouped['pressure']),atmospheric_sector_dates=len(grouped['air_106Pa']))))

if __name__=='__main__':main()
