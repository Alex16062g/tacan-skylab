"""Terrain sampling and exploratory regional ANOVA; NASA originals are unchanged.
Run: python recursos/scripts/anova_regiones.py
Dependencies: numpy scipy pillow matplotlib
"""
from pathlib import Path
import csv, json, hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datos/nasa"
OUT = ROOT / "anova_regiones"
OUT.mkdir(exist_ok=True)
Image.MAX_IMAGE_PIXELS = None
SEED = 20261114
N = 80
STEP = 10000.0

def sample(a, lat, lon):
    # Pixel centers, east-positive longitude 0..360; input array starts at 0 E.
    y = (90 - np.asarray(lat)) * a.shape[0] / 180 - 0.5
    x = np.mod(lon, 360) * a.shape[1] / 360 - 0.5
    return map_coordinates(a, np.array([y, x]), order=1, mode="grid-wrap", prefilter=False)

def terrain(a, radius, lat, lon):
    # Equal physical baseline on both bodies. Central differences over 20 km.
    dy = np.degrees(STEP / radius)
    dx = dy / np.cos(np.radians(lat))
    z = sample(a, lat, lon)
    gx = (sample(a, lat, lon + dx) - sample(a, lat, lon - dx)) / (2 * STEP)
    gy = (sample(a, lat + dy, lon) - sample(a, lat - dy, lon)) / (2 * STEP)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    patch = np.array([sample(a, lat + j * dy, lon + i * dx)
                      for j in range(-2, 3) for i in range(-2, 3)])
    relief = np.percentile(patch, 95, axis=0) - np.percentile(patch, 5, axis=0)
    return z, slope, relief

def main():
    rng = np.random.default_rng(SEED)
    moon = np.asarray(Image.open(DATA / "luna/global/ldem_16.tif"), dtype=np.float64) * 1000
    # SVS texture spans -180..180; put 0 E at first column.
    moon = np.roll(moon, -moon.shape[1] // 2, axis=1)
    mars = np.memmap(DATA / "marte/global/megt90n000fb.img", dtype=">i2", shape=(5760, 11520))
    # Float conversion avoids rounding bilinear interpolation into integer meters.
    mars = np.asarray(mars, dtype=np.float32)
    rows, tests, summaries = [], [], []
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), layout="constrained")
    for ax, (body, a, radius) in zip(axes, [("MOON", moon, 1737400.), ("MARS", mars, 3396000.)]):
        groups = {}
        for south in range(-90, 90, 30):
            for west in range(0, 360, 60):
                # Exclude polar caps beyond 85 degrees to avoid tangent-grid singularity.
                low, high = max(south, -85), min(south + 30, 85)
                lat = np.degrees(np.arcsin(rng.uniform(np.sin(np.radians(low)), np.sin(np.radians(high)), N)))
                lon = rng.uniform(west, west + 60, N)
                z, slope, relief = terrain(a, radius, lat, lon)
                assert np.all(np.isfinite([z, slope, relief]))
                region = f"lat_{south}_{south+30}_lon_{west}_{west+60}"
                groups[region] = {"elevation_m": z, "slope_deg": slope, "relief_p95_p05_m": relief}
                for k in range(N):
                    rows.append(dict(body=body, region=region, latitude_deg=float(lat[k]), longitude_east_deg=float(lon[k]),
                                     elevation_m=float(z[k]), slope_deg=float(slope[k]), relief_p95_p05_m=float(relief[k])))
                summaries.append(dict(body=body, region=region, n=N, latitude_limits=[low, high], longitude_limits=[west, west+60],
                                      **{key+"_mean":float(np.mean(v)) for key,v in groups[region].items()}))
        for variable in ["elevation_m", "slope_deg", "relief_p95_p05_m"]:
            samples = [np.asarray(g[variable], dtype=np.float64) for g in groups.values()]
            classic = stats.f_oneway(*samples)
            welch = stats.f_oneway(*samples, equal_var=False)
            levene = stats.levene(*samples, center="median")
            residuals = np.concatenate([v-v.mean() for v in samples])
            normality = stats.normaltest(residuals)
            tests.append(dict(body=body, variable=variable, groups=len(samples), n_per_group=N,
                              classic_F=float(classic.statistic), classic_p=float(classic.pvalue),
                              welch_F=float(welch.statistic), welch_p=float(welch.pvalue),
                              levene_p=float(levene.pvalue), residual_normality_p=float(normality.pvalue)))
        ax.boxplot([g["slope_deg"] for g in groups.values()], showfliers=False)
        ax.set(title=f"{body}: 36 sectores geográficos, 80 muestras por sector", xlabel="Sector (orden en resumen.json)", ylabel="Pendiente a escala de 10 km (grados)")
    # Holm correction over the six Welch tests; no between-body absolute elevation test.
    order = np.argsort([t["welch_p"] for t in tests])
    adjusted = 0.
    for rank, idx in enumerate(order):
        adjusted = max(adjusted, min(1., (len(tests)-rank)*tests[idx]["welch_p"]))
        tests[idx]["welch_p_holm"] = adjusted
    with (OUT / "muestras.csv").open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    for filename, value in [("muestras.json", rows), ("resumen.json", summaries), ("anova.json", tests)]:
        (OUT / filename).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    fig.savefig(OUT / "pendientes.png", dpi=150)
    manifest=json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    sources=[e for e in manifest if e["file"] in ["luna/global/ldem_16.tif", "marte/global/megt90n000fb.img"]]
    for e in sources:
        with (DATA/e["file"]).open("rb") as f: assert hashlib.file_digest(f,"sha256").hexdigest()==e["sha256"]
    extra = DATA / "luna/site04/Site04_final_adj_5mpp_surf.tif"
    extra_summary = {}
    if extra.exists():
        z=np.asarray(Image.open(extra),dtype=float)
        extra_summary=dict(region="Shackleton rim / Site04",shape=list(z.shape),pixel_spacing_m=5,
                           elevation_min_m=float(z.min()),elevation_max_m=float(z.max()),
                           elevation_mean_m=float(z.mean()),included_in_anova=False)
    metadata=dict(seed=SEED, sample_count=len(rows), sectors_per_body=36,
        latitude_coverage=[-85,85], longitude_coverage=[0,360], sources=sources, additional_region=extra_summary,
        method="Uniform-area random sampling within 30-degree latitude x 60-degree longitude sectors. Bilinear DEM interpolation. Slope: central differences with offsets of 10 km. Relief: P95-P05 of a 5x5 grid spaced by 10 km in a local tangent approximation. ANOVA separately within each body.",
        limitations=["Exploratory only: spatial independence is not established; p values are conditional and not confirmatory evidence.",
        "Sectors are analytical bins, not official geological regions. Polar caps beyond 85 degrees are excluded.",
        "Random samples may have overlapping neighborhoods; spatial autocorrelation needs explicit modelling or block resampling before inference.",
        "DEM interpolation and native instrument resolution differ. Same derivative baseline does not imply identical effective resolution.",
        "Elevation references differ by body; absolute elevations are never pooled across bodies.",
        "No temperature, regional gravity, composition or thermal inertia has been added; those require separate products and processing.",
        "P values reported as zero indicate numerical underflow, not exact probability zero."])
    (OUT/"metodologia.json").write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(dict(samples=len(rows),sectors=len(summaries),tests=tests,additional_region=extra_summary),indent=2))

if __name__ == "__main__":
    main()
    from validar_anova_espacial import main as validar_espacial
    validar_espacial()
