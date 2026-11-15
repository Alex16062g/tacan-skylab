"""Example: load numeric temperatures and pressure without extra dependencies."""
from pathlib import Path
import csv
import json
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'ambiente_luna_marte'

def cargar_temperaturas(body, temperature_type, phase=None, period=None):
    data = json.loads((DATA/'temperaturas.json').read_text(encoding='utf-8'))
    return [row for row in data[body]
            if row['temperature_type'] == temperature_type
            and (phase is None or row['phase'] == phase)
            and (period is None or row['observation_period'] == period)]

def cargar_presiones_marte():
    with (DATA/'marte_presion_observada.csv').open(encoding='utf-8') as f:
        return [float(row['pressure_Pa']) for row in csv.DictReader(f)]

if __name__ == '__main__':
    luna = cargar_temperaturas('MOON', 'surface_bolometric', 'day_14h30_15h30')
    # This is a descriptive mean of sampled cells, not an area-weighted global temperature.
    temperatura_luna_C = mean(row['temperature_C'] for row in luna)
    presiones_marte_Pa = cargar_presiones_marte()
    atmosfera = json.loads((DATA/'atmosfera_referencia.json').read_text(encoding='utf-8'))
    oxigeno_marte_porcentaje = atmosfera['MARS']['Oxygen By Volume (%)']
    print('Luna, promedio de celdas muestreadas a 14:30-15:30:', temperatura_luna_C, 'C')
    print('Mediciones de presion marciana:', len(presiones_marte_Pa))
    print('O2 de referencia en Marte (no medicion regional):', oxigeno_marte_porcentaje, '%')
