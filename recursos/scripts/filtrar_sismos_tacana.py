"""Filter the national SSN catalogue to the exact rectangle displayed on the map."""
import csv,json,re,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'datos/SSNMX_catalogo_20200101_20261114.csv'
OUT=ROOT/'recursos/sismos'

def inside(lon,lat,bounds):
    west,south,east,north=bounds
    return west<=lon<=east and south<=lat<=north

def main():
    bounds=json.loads((ROOT/'recursos/comparacion_tacana/metodologia.json').read_text(encoding='utf-8'))['reference_source']['sample_bounds_wsen']
    lines=SOURCE.read_text(encoding='utf-8-sig').splitlines()
    start=next(i for i,line in enumerate(lines) if line.startswith('Fecha,Hora,'))
    features=[];total=0
    for index,row in enumerate(csv.DictReader(lines[start:]),start+2):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',row['Fecha']):continue
        total+=1;lat=float(row['Latitud']);lon=float(row['Longitud'])
        if not (math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180):
            raise ValueError(f'Invalid coordinates at source row {index}')
        if not inside(lon,lat,bounds):continue
        try:magnitude=float(row['Magnitud'])
        except ValueError:magnitude=None
        if magnitude is not None and not math.isfinite(magnitude):magnitude=None
        features.append(dict(type='Feature',id=f'ssn-{index}',geometry=dict(type='Point',coordinates=[lon,lat]),properties=dict(
            date=row['Fecha'],time=row['Hora'],magnitude=magnitude,depth_km=float(row['Profundidad']),
            date_utc=row['Fecha UTC'],time_utc=row['Hora UTC'],status=row['Estatus'],source_row=index)))
    metadata=dict(source='Servicio Sismológico Nacional (SSN), UNAM',source_url='https://doi.org/10.21766/SSNMX/EC/MX',
        source_file=str(SOURCE.relative_to(ROOT)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        national_events=total,selected_events=len(features),period=['2020-01-01','2026-11-14'],
        filter=dict(method='epicentre inside displayed Tacana rectangle; inclusive boundaries',bounds_wsen=bounds,depth_filter=None,magnitude_filter=None),
        time_basis='Date and time as published: central Mexico local time; UTC values retained separately',
        interpretation='Geographical selection only. Does not establish volcanic origin or a geological boundary of the volcano.',
        use_conditions='SSN catalogue states: non-commercial reproduction with attribution; other use requires prior written permission.')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'tacana.geojson').write_text(json.dumps(dict(type='FeatureCollection',metadata=metadata,features=features),ensure_ascii=False,allow_nan=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(national=total,selected=len(features),bounds_wsen=bounds)))

if __name__=='__main__':main()
