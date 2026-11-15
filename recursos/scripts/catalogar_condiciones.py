"""Condition profiles for every named location, with explicit support and no composite score."""
from pathlib import Path
from collections import defaultdict
import json, hashlib
from integrar_ambiente import stats
from comparar_temperatura_tacana import sector

ROOT=Path(__file__).resolve().parents[2]
CAT=ROOT/'recursos/catalogo_regiones'
DATA=ROOT/'recursos/comparacion_tacana'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
def point(v):return dict(min=v,max=v,mean=v,n=1)
def entry(key,label,unit,reference,planetary,scope,source,period='',status=None):
    return dict(variable=key,label=label,unit=unit,reference=reference,planetary=planetary,
        scope=scope,source=source,period=period,
        status=status or ('descriptive_context' if planetary else 'missing_planetary_data'),
        difference=(planetary['mean']-reference['mean']) if planetary and reference else None,
        range_overlap=([max(reference['min'],planetary['min']),min(reference['max'],planetary['max'])]
                       if reference and planetary and max(reference['min'],planetary['min'])<=min(reference['max'],planetary['max']) else None),
        eligible_for_local_anova=False)

def main():
    env=read(DATA/'ambiente_integrado.json')
    samples=read(DATA/'temperatura_muestras_planetarias.json');refs=read(DATA/'temperatura_referencia_tacana.json')
    thermal=defaultdict(list)
    for r in samples:thermal[(r['body'],r['region'],r['phase'])].append(r['temperature_C'])
    extra=read(ROOT/'recursos/ambiente_luna_marte/temperaturas.json')
    extended=defaultdict(list)
    for b,rows in extra.items():
        for r in rows:extended[(b,r['region'],r['phase'],r['observation_period'],r['temperature_type'])].append(r['temperature_C'])
    power={x['variable']:x for x in env['reference_power']['statistics']}
    all_profiles={};counts={}
    for body in ['MOON','MARS']:
        catalog=read(CAT/f'{body.lower()}.json');features=catalog['features']
        keys=sorted({sector(f['latitude_deg'],f['longitude_east_deg']) for f in features if f['latitude_deg'] is not None and f['longitude_east_deg'] is not None})
        facts=f'https://nssdc.gsfc.nasa.gov/planetary/factsheet/{"moon" if body=="MOON" else "mars"}fact.html'
        profiles={}
        for s in keys:
            rows=[]
            for phase,label in [('day','Temperatura superficial diurna'),('night','Temperatura superficial nocturna')]:
                rows.append(entry(f'surface_{phase}',label,'°C',stats([r['temperature_C'] for r in refs if r['phase']==phase]),
                    stats(thermal[(body,s,phase)]),'Sector 30° × 60°; Tacaná: ventana MODIS de ~14 km',
                    '../comparacion_tacana/temperatura_metodologia.json',
                    ('Luna 2009–2015; Tacaná 24–31 oct. 2011' if body=='MOON' else 'Marte 31 oct. 2011; Tacaná 24–31 oct. 2011')+('; 12–14 h solares' if phase=='day' else '; 1–2 h solares')))
            pressure=next((x for x in env['mars_pressure_by_sector_date'] if x['sector']==s and x['date']=='20111031'),None) if body=='MARS' else None
            refp=next(x['value'] for x in env['reference_power']['daily_records'] if x['variable']=='PS' and x['date']=='20111031')
            ps={k:(v/1000 if k!='n' and v is not None else v) for k,v in pressure['statistics'].items()} if pressure else None
            rows.append(entry('pressure','Presión superficial','kPa',point(refp),ps,'Sector MCS; Tacaná: celda POWER a 1 508 m',
                '../comparacion_tacana/ambiente_integrado.json','31 oct. 2011; MCS: distintas horas, POWER: promedio diario'))
            air=[x for x in env['mars_atmospheric_temperature_by_sector_date'] if x['sector']==s] if body=='MARS' else []
            for key in ['T2M','T2M_MIN','T2M_MAX','RH2M','WS2M','PRECTOTCORR','ALLSKY_SFC_SW_DWN','TOA_SW_DWN']:
                r=power[key]
                rows.append(entry(key,r['label'],r['unit'],r['statistics'],None,
                    'Tacaná: celda POWER, no cima; sin contraparte local planetaria',env['reference_power']['source'],
                    '24–31 oct. 2011', 'not_applicable_2m_air' if body=='MOON' and key in ['T2M','T2M_MIN','T2M_MAX','RH2M','WS2M'] else 'missing_planetary_data'))
            # Explicit body references: useful physical conditions, never independent regional samples.
            global_values=[('gravity','Gravedad media','m/s²',9.82,1.62 if body=='MOON' else 3.73),
                ('solar_flux','Irradiancia solar extraterrestre','W/m²',1361.,1361. if body=='MOON' else 586.2),
                ('day_length','Duración del día solar','h',24.,29.53*24 if body=='MOON' else 24.6597),
                ('bond_albedo','Albedo de Bond','fracción',.294,.11 if body=='MOON' else .25),
                ('oxygen','Oxígeno atmosférico','% volumen',20.95,None if body=='MOON' else .16),
                ('carbon_dioxide','Dióxido de carbono atmosférico','% volumen',.042,None if body=='MOON' else 95.1)]
            for key,label,unit,a,b in global_values:
                rows.append(entry(key,label,unit,point(a),point(b) if b is not None else None,
                    'Referencia del cuerpo; Tierra no es medición local de Tacaná',facts,
                    'Ficha NASA; valores de referencia, no series temporales',
                    'body_reference' if b is not None else 'no_lunar_molecular_fraction'))
            rows.append(entry('pressure_reference','Presión atmosférica de referencia','kPa',point(101.4),point(3e-13 if body=='MOON' else .636),
                'Tierra: referencia global; Luna: estimación nocturna; Marte: radio medio',facts,'Ficha NASA', 'body_reference'))
            for key,label,unit in [('ionizing_radiation','Dosis de radiación ionizante','mSv/día'),('uv','Radiación ultravioleta superficial','W/m²'),
                                   ('dust_optical_depth','Opacidad del polvo','adimensional'),('thermal_inertia','Inercia térmica','J m⁻² K⁻¹ s⁻½'),
                                   ('available_water','Agua disponible localmente','kg/m²')]:
                rows.append(entry(key,label,unit,None,None,'Sin datos locales comparables en los insumos',None,status='missing_both'))
            other=[dict(phase=k[2],period=k[3],temperature_type=k[4],statistics=stats(v)) for k,v in extended.items() if k[0]==body and k[1]==s]
            coverage=sum(bool(rows[i]['planetary']) for i in range(3))+bool(air)
            profiles[s]=dict(sector=s,conditions=rows,observation_types_available=coverage,
                atmospheric_106Pa=[{k:v for k,v in r.items() if k!='samples'} for r in air],
                pressure_other_dates=[{k:v for k,v in r.items() if k!='samples'} for r in env['mars_pressure_by_sector_date'] if body=='MARS' and r['sector']==s],
                additional_thermal_observations=other,local_environment_observations=0,
                environmental_score_status='not_defined_incompatible_support_and_missing_data')
        for f in features:
            s=sector(f['latitude_deg'],f['longitude_east_deg']) if f['latitude_deg'] is not None and f['longitude_east_deg'] is not None else None
            f['conditions']=dict(profile=s,observation_types_available=profiles[s]['observation_types_available'] if s else 0,
                                 profile_file=f'condiciones_{body.lower()}.json',local_environment_observations=0)
        catalog['condition_sources']=dict(profiles=f'condiciones_{body.lower()}.json',earth_facts='https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html',planetary_facts=facts)
        write(CAT/f'{body.lower()}.json',catalog)
        output=dict(body=body,profiles=profiles,condition_count=len(next(iter(profiles.values()))['conditions']),
            reference_power_scope=env['reference_power']['scope'],
            reference_elevation_m=env['reference_power']['cell_elevation_m'],
            references=[facts,'https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html','../comparacion_tacana/ambiente_integrado.json'],
            general_similarity_percent=None,environmental_ranking=None,
            method='Per-variable ranges and signed differences; no missing-data imputation, no synthetic composite index.',
            input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA/'ambiente_integrado.json',ROOT/'recursos/ambiente_luna_marte/temperaturas.json']})
        write(CAT/f'condiciones_{body.lower()}.json',output)
        counts[body]=dict(regions=len(features),sectors=len(profiles),conditions=output['condition_count'])
    write(CAT/'condiciones_resumen.json',counts);print(json.dumps(counts))

if __name__=='__main__':main()
