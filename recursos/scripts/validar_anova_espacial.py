"""Spatial-block sensitivity analysis. Does not certify independence or sample sufficiency."""
from pathlib import Path
import csv,json,itertools
import numpy as np
from scipy import stats
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"anova_regiones"
VARIABLES=["elevation_m","slope_deg","relief_p95_p05_m"]

def save(name,rows):
    (OUT/(name+".json")).write_text(json.dumps(rows,indent=2,allow_nan=False),encoding="utf-8")
    if isinstance(rows,list) and rows:
        with (OUT/(name+".csv")).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def holm(rows,key,out):
    order=np.argsort([r[key] for r in rows]);last=0.
    for rank,i in enumerate(order):
        last=max(last,min(1.,(len(rows)-rank)*rows[i][key]));rows[i][out]=last

def xyz(lat,lon,radius):
    lat,lon=np.radians(lat),np.radians(lon)
    return radius*np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])

def moran(values,positions,labels,distance,rng,permutations=4999):
    # Symmetric binary neighbors in 3-D chord distance; permutation within sectors.
    pairs=cKDTree(positions).query_pairs(distance,output_type="ndarray")
    residual=values.copy()
    ids=[np.flatnonzero(labels==g) for g in np.unique(labels)]
    for ix in ids:residual[ix]-=residual[ix].mean()
    if len(pairs)==0 or np.dot(residual,residual)==0:
        return dict(I=None,p=None,edges=int(len(pairs)),status="insufficient_neighbors")
    def score(v):return len(v)/len(pairs)*np.sum(v[pairs[:,0]]*v[pairs[:,1]])/np.dot(v,v)
    observed=score(residual);permuted=[]
    for _ in range(permutations):
        v=residual.copy()
        for ix in ids:v[ix]=rng.permutation(v[ix])
        permuted.append(score(v))
    # Upper-tail test for positive residual spatial association.
    p=(1+np.sum(np.asarray(permuted)>=observed))/(permutations+1)
    return dict(I=float(observed),p=float(p),edges=int(len(pairs)),status="diagnostic_only")

def main():
    rng=np.random.default_rng(20261115)
    records=json.loads((OUT/"muestras.json").read_text())
    tests=[];pairs_out=[];summaries=[];blocks_out=[];diagnostics=[]
    for body,radius in [("MOON",1737.4),("MARS",3396.)]:
        data=[r for r in records if r["body"]==body]
        labels=np.array([r["region"] for r in data])
        points=xyz([r["latitude_deg"] for r in data],[r["longitude_east_deg"] for r in data],radius)
        values={v:np.array([r[v] for r in data],dtype=float) for v in VARIABLES}
        for variable,y in values.items():
            for distance in [100,200,400]:
                d=moran(y,points,labels,distance,rng)
                diagnostics.append(dict(body=body,variable=variable,level="original_points",distance_km=distance,**d))
        for scale in [100,200,400]:
            # Cartesian cubes avoid longitude seams and polar singularities.
            cells=np.floor(points/scale).astype(int)
            keys=[(labels[i],*cells[i]) for i in range(len(data))]
            buckets={}
            for i,key in enumerate(keys):buckets.setdefault(key,[]).append(i)
            keys=list(buckets);indices=[buckets[k] for k in keys]
            block_labels=np.array([k[0] for k in keys])
            positions=np.array([points[ix].mean(axis=0) for ix in indices])
            region_names=np.unique(block_labels)
            for variable,y in values.items():
                means=np.array([y[ix].mean() for ix in indices])
                groups=[means[block_labels==g] for g in region_names]
                if min(map(len,groups))<3:raise ValueError("Too few occupied blocks in a sector")
                classic=stats.f_oneway(*groups);welch=stats.f_oneway(*groups,equal_var=False)
                grand=means.mean();ssb=sum(len(g)*(g.mean()-grand)**2 for g in groups)
                ssw=sum(np.sum((g-g.mean())**2) for g in groups)
                dfb=len(groups)-1;dfw=len(means)-len(groups);mse=ssw/dfw
                eta=ssb/(ssb+ssw);omega=max(0.,(ssb-dfb*mse)/(ssb+ssw+mse))
                d=moran(means,positions,block_labels,scale*2,rng)
                diagnostics.append(dict(body=body,variable=variable,level=f"blocks_{scale}km",distance_km=scale*2,**d))
                tests.append(dict(body=body,variable=variable,block_km=scale,occupied_blocks=len(means),
                    min_blocks_per_sector=min(map(len,groups)),max_blocks_per_sector=max(map(len,groups)),
                    classic_F=float(classic.statistic),classic_p=float(classic.pvalue),welch_F=float(welch.statistic),welch_p=float(welch.pvalue),
                    eta_squared=float(eta),omega_squared=float(omega),levene_p=float(stats.levene(*groups,center="median").pvalue),
                    spatial_I=d["I"],spatial_p=d["p"],inference_status="conditional_not_confirmatory"))
                if scale!=200:continue
                for k,ix,val in zip(keys,indices,means):
                    blocks_out.append(dict(body=body,region=k[0],cube_x=int(k[1]),cube_y=int(k[2]),cube_z=int(k[3]),variable=variable,n_points=len(ix),mean=float(val)))
                for name,g in zip(region_names,groups):
                    boot=g[rng.integers(0,len(g),size=(2000,len(g)))].mean(axis=1)
                    lo,hi=np.percentile(boot,[2.5,97.5])
                    summaries.append(dict(body=body,region=str(name),variable=variable,n_blocks=len(g),mean=float(g.mean()),
                        sd=float(g.std(ddof=1)),ci95_low=float(lo),ci95_high=float(hi),
                        interval="percentile bootstrap of occupied block means; assumes independent blocks"))
                for i,j in itertools.combinations(range(len(groups)),2):
                    a,b=groups[i],groups[j];test=stats.ttest_ind(a,b,equal_var=False)
                    va,vb=a.var(ddof=1)/len(a),b.var(ddof=1)/len(b)
                    df=(va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1))
                    margin=stats.t.ppf(.975,df)*np.sqrt(va+vb);delta=a.mean()-b.mean()
                    pooled=np.sqrt(((len(a)-1)*a.var(ddof=1)+(len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2))
                    hedges=(1-3/(4*(len(a)+len(b))-9))*delta/pooled
                    pairs_out.append(dict(body=body,variable=variable,region_a=str(region_names[i]),region_b=str(region_names[j]),
                        mean_difference=float(delta),ci95_low=float(delta-margin),ci95_high=float(delta+margin),
                        hedges_g=float(hedges),welch_t=float(test.statistic),p=float(test.pvalue),
                        interval="unadjusted Welch interval; conditional on independent blocks"))
    # Planning scenarios, not claimed achieved power; units must be independent.
    planning=[]
    for body in ["MOON","MARS"]:
        for variable,deltas in [("slope_deg",[0.5,1.,2.]),("relief_p95_p05_m",[100.,250.,500.])]:
            subset=[r for r in summaries if r["body"]==body and r["variable"]==variable]
            sd=max(r["sd"] for r in subset)
            for delta in deltas:
                for alpha,label in [(.05,"single_prespecified_pair"),(.05/3780,"conservative_all_pairs")]:
                    n=int(np.ceil(2*(stats.norm.ppf(1-alpha/2)+stats.norm.ppf(.8))**2*sd**2/delta**2))
                    planning.append(dict(body=body,variable=variable,minimum_difference=delta,reference_sd=sd,
                        target_power=.8,alpha=alpha,comparison_plan=label,approx_independent_units_per_group=max(2,n),
                        status="Normal-approximation planning scenario; not achieved power or number of pixels required"))
    save("plan_muestreo",planning)
    holm(tests,"welch_p","welch_p_holm_18_tests")
    holm(pairs_out,"p","p_holm_3780_pairs")
    valid=[d for d in diagnostics if d["p"] is not None]
    holm(valid,"p","p_holm_diagnostics")
    save("anova_bloques",tests);save("comparaciones_regiones",pairs_out)
    save("intervalos_regionales",summaries);save("bloques_200km",blocks_out);save("diagnostico_espacial",diagnostics)
    status=dict(original_samples=len(records),tests=len(tests),pairwise_comparisons=len(pairs_out),
        spatial_diagnostics_significant_holm=sum(d["p_holm_diagnostics"]<.05 for d in valid),
        sufficient_for="Reproducible exploratory terrain comparison and spatial sensitivity assessment",
        sufficient_for_confirmatory_anova=False,
        reason="More pixels cannot establish independence. Spatial models and a predefined effect/power target are required for confirmatory claims.",
        estimand="Equal-weight mean of occupied Cartesian block means within each sector; not an area-weighted global mean.",
        limits=["Blocks can remain correlated and can cross sector boundaries; blocks are split by sector, so adjacent split pieces are not independent.",
        "Block sizes 100/200/400 km are sensitivity scenarios, not estimated decorrelation ranges.",
        "Bootstrap intervals and Welch tests assume independent blocks; diagnostics do not prove independence when nonsignificant.",
        "Moran diagnostic uses chord distances, symmetric binary weights, and 4999 within-sector permutations; smallest attainable p is 0.0002.",
        "No measurements of temperature/composition/gravity were synthesized. Native data coverage and interpolation limitations remain.",
        "Sector definitions and latitude exclusion remain unchanged. No test pools absolute elevations across bodies."])
    save("estado_validacion",status)
    print(json.dumps(status,indent=2))

if __name__=="__main__":main()
