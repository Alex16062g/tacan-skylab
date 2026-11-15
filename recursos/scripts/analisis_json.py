"""Compara exclusivamente los JSON locales y comprueba la viabilidad del ANOVA."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "recursos" / "analisis_json" / "comparacion_json.json"
SOURCES = [
    ROOT / "datos" / "luna_marte.json",
    ROOT / "datos" / "tacana.json",
]


def main():
    planets = json.loads(SOURCES[0].read_text(encoding="utf-8"))
    volcano = json.loads(SOURCES[1].read_text(encoding="utf-8"))
    records = {
        "Luna": planets["MOON"],
        "Marte": planets["MARS"],
        "Tacaná": volcano["TACANA"],
    }
    common_fields = set.intersection(*(set(record) for record in records.values()))
    common_numeric_fields = sorted(
        field for field in common_fields
        if all(type(record[field]) in (int, float) for record in records.values())
    )

    measurements = [
        ("Masa", "Mass (10^24 kg)", "10^24 kg"),
        ("Diámetro del cuerpo", "Diameter (km)", "km"),
        ("Densidad", "Density (kg/m^3)", "kg/m^3"),
        ("Gravedad superficial", "Gravity (m/s^2)", "m/s^2"),
        ("Temperatura media", "Mean Temperature (C)", "°C"),
        ("Elevación sobre el nivel del mar", "Elevation (m above sea level)", "m"),
        ("Altura sobre terreno circundante", "Height Above Surrounding Terrain (m)", "m"),
    ]
    comparison = [
        {
            "variable": name,
            "unidad": unit,
            "valores": {body: record.get(field) for body, record in records.items()},
        }
        for name, field, unit in measurements
    ]

    result = {
        "alcance": "Comparación descriptiva de Luna, Marte y Tacaná usando solo los dos JSON locales.",
        "fuentes": [
            {
                "archivo": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in SOURCES
        ],
        "registros_por_entidad": {body: 1 for body in records},
        "campos_comunes_tres_entidades": sorted(common_fields),
        "variables_cuantitativas_comunes": common_numeric_fields,
        "comparacion": comparison,
        "descripcion_tacana": {
            key: records["Tacaná"][key]
            for key in ("Countries", "Volcano Types", "Major Rock Types", "Tectonic Setting")
        },
        "anova": {
            "estado": "No estimable con estos archivos",
            "F": None,
            "p": None,
            "razones": [
                "No hay una misma variable cuantitativa observada en las tres entidades.",
                "Cada JSON proporciona un registro por entidad y ninguna serie de réplicas.",
                "Con un valor de una misma variable por grupo, N-k sería 3-3=0 y el cuadrado medio residual no podría estimarse.",
            ],
            "fundamento": "ANOVA contrasta medias de una misma variable. F = MS_entre / MS_dentro, con gl_dentro = N-k.",
            "referencia": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html",
        },
        "similitud": {
            "estado": "Sin puntuación cuantitativa estimable respecto al Tacaná",
            "razon": "Los atributos planetarios y volcanológicos disponibles describen magnitudes diferentes.",
            "interpretacion": "Los valores ausentes se conservan como null. Las propiedades distintas no constituyen réplicas de una misma variable.",
        },
        "datos_necesarios": "Mediciones comparables de una misma variable, con unidades compatibles y réplicas independientes en cada grupo, por ejemplo pendientes de varias zonas de cada entorno.",
    }

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Comparación exclusiva de los JSON locales")
    print(f"{'Variable':<36} {'Luna':>12} {'Marte':>12} {'Tacaná':>12}  Unidad")
    for row in comparison:
        values = ["sin dato" if value is None else str(value) for value in row["valores"].values()]
        print(f"{row['variable']:<36} {values[0]:>12} {values[1]:>12} {values[2]:>12}  {row['unidad']}")
    print(f"\nVariables cuantitativas comunes a los tres: {len(common_numeric_fields)}")
    print("ANOVA no estimable. F y p quedan sin calcular.")
    print("Un valor por grupo daría cero grados de libertad residuales, incluso con una variable común.")
    print(f"Resultado guardado en {OUTPUT}")


if __name__ == "__main__":
    main()
