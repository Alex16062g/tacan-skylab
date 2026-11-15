"""Experimental terrain affinity index; not ANOVA, probability or equivalence."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.stats import wasserstein_distance

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'recursos/comparacion_tacana'
FEATURES = {'mean_slope_deg': ('Pendiente', '°'), 'local_relief_m': ('Relieve local', 'm')}


def affinity(distance, reference_sd):
    if not np.isfinite(distance) or distance < 0 or not np.isfinite(reference_sd) or reference_sd <= 0:
        raise ValueError('La afinidad requiere distancia válida y dispersión de referencia positiva.')
    # Divide the smaller magnitude by the larger to avoid overflow for
    # finite inputs with very different scales.
    if distance > reference_sd:
        ratio = reference_sd / distance
        return 100.0 * ratio / (1.0 + ratio)
    return 100.0 / (1.0 + distance / reference_sd)


def calculate(rows, region, side):
    features = []
    for key, (label, unit) in FEATURES.items():
        arrays = [np.asarray([r[key] for r in rows if r['region'] == name and r['block_side_m'] == side], dtype=float)
                  for name in ['tierra_tacana', region]]
        ref, sample = arrays
        if any(len(a) < 3 or not np.isfinite(a).all() for a in arrays):
            return None  # Missing data never becomes a match or a reweighted score.
        sd = float(ref.std(ddof=1))
        if sd <= 0:
            return None
        distance = float(wasserstein_distance(ref, sample))
        low, high = max(ref.min(), sample.min()), min(ref.max(), sample.max())
        features.append(dict(variable=key, label=label, unit=unit,
                             similarity_percent=affinity(distance, sd), weight=0.5,
                             reference_mean=float(ref.mean()), region_mean=float(sample.mean()),
                             reference_sd=sd, wasserstein_distance=distance,
                             n_reference=len(ref), n_region=len(sample),
                             shared_range=[float(low), float(high)] if low < high else None))
    return dict(block_side_m=side, similarity_percent=sum(f['weight'] * f['similarity_percent'] for f in features),
                features=features)


def main():
    source = OUT / 'bloques.json'
    rows = json.loads(source.read_text(encoding='utf-8'))
    names = {r['region']: r['name'] for r in rows if r['region'] != 'tierra_tacana'}
    regions = []
    for region, name in names.items():
        primary = calculate(rows, region, 1000)
        if primary is None:
            continue
        regions.append(dict(region=region, name=name, body='MOON' if region.startswith('luna_') else 'MARS',
                            primary=primary, sensitivity=calculate(rows, region, 2000)))
    selections = {}
    for body in ['MOON', 'MARS']:
        candidates = sorted([r for r in regions if r['body'] == body],
                            key=lambda r: (-r['primary']['similarity_percent'], r['region']))
        selections[body] = dict(candidate_count=len(candidates),
                                selected_region=candidates[0]['region'] if candidates else None,
                                ranking=[r['region'] for r in candidates])
    output = dict(version=1, scope='terrain_only', experimental=True,
                  formula='s_j = 100 / (1 + Wasserstein_j / SD_Tacana_j); S = 0.5*s_slope + 0.5*s_relief',
                  interpretation='Índice descriptivo diseñado para este proyecto, no una probabilidad ni un porcentaje de equivalencia. 100 indica distribuciones empíricas iguales en las medidas incluidas.',
                  calibration='Sin calibración externa. Una distancia de una desviación estándar de Tacaná produce 50 puntos en esa medida. Los pesos iguales son una decisión de diseño.',
                  primary_scale_m=1000, sensitivity_scale_m=2000,
                  source_file=str(source.relative_to(ROOT)), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  coverage=[
                      dict(feature='Pendiente', included=True, reason='Bloques locales a escala común.'),
                      dict(feature='Relieve local', included=True, reason='Bloques locales a escala común.'),
                      dict(feature='Temperatura diurna y nocturna', included=False, reason='Sectores y soportes distintos del relieve local. Marte térmico polar; Cerberus no tiene cobertura coincidente en esta descarga.'),
                      dict(feature='Oxígeno y presión', included=False, reason='No hay series regionales comparables de Tacaná y las regiones seleccionadas.'),
                      dict(feature='Gravedad, masa, diámetro y datos orbitales', included=False, reason='Propiedades de cuerpos completos; no describen semejanza entre regiones del terreno.'),
                      dict(feature='Sismicidad', included=False, reason='No hay catálogos compatibles para las regiones de los tres cuerpos.'),
                      dict(feature='Elevación absoluta', included=False, reason='Referencias verticales distintas; se usa relieve local.'),
                      dict(feature='Imágenes y coordenadas', included=False, reason='Se usan para localizar y visualizar; no son puntuaciones de similitud.')],
                  selections=selections, regions=regions)
    (OUT / 'similitud.json').write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    for body, selection in selections.items():
        winner = next((r for r in regions if r['region'] == selection['selected_region']), None)
        if winner:
            print(body, winner['region'], round(winner['primary']['similarity_percent'], 2), 'candidates:', selection['candidate_count'])


if __name__ == '__main__':
    main()
