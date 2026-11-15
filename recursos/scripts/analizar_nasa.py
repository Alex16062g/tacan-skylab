"""Reproducible terrain products. Originals remain untouched.
100 m products are derived here, not official NASA slope products.
"""
from pathlib import Path
import json,re,math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter,map_coordinates,binary_erosion
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'datos/nasa';OUT=ROOT/'analisis_nasa';OUT.mkdir(exist_ok=True)
Image.MAX_IMAGE_PIXELS=None
def read_pds(path):
 with path.open('rb') as f:label=f.read(15000).decode('ascii',errors='replace').replace('\r','')
 def number(key):return float(re.search(r'^\s*'+re.escape(key)+r'\s*=\s*([-+\d.eE]+)',label,re.M)[1])
 assert 'PC_REAL' in label
 rows,cols=int(number('LINES')),int(number('LINE_SAMPLES'))
 offset=int((number('^IMAGE')-1)*number('RECORD_BYTES'))
 a=np.array(np.memmap(path,dtype='<f4',offset=offset,shape=(rows,cols)))
 a[(a < -1e30)|~np.isfinite(a)]=np.nan
 # Published valid range is rounded, so use the bit-pattern range for missing data.
 assert np.nanmin(a)>=number('VALID_MINIMUM')-1 and np.nanmax(a)<=number('VALID_MAXIMUM')+1
 return a,number('MAP_SCALE'),label

def common_grid(a,dx,dy,spacing=100.):
 """Low-pass before bilinear sampling; reject cells touching missing-data support."""
 valid=np.isfinite(a);sigma=(max(0,spacing/dy/2),max(0,spacing/dx/2))
 weight=gaussian_filter(valid.astype('float32'),sigma,mode='constant',cval=0)
 smooth=gaussian_filter(np.where(valid,a,0).astype('float32'),sigma,mode='constant',cval=0)/np.maximum(weight,1e-9)
 ys=np.arange(spacing/2,(a.shape[0]-1)*dy,spacing)/dy
 xs=np.arange(spacing/2,(a.shape[1]-1)*dx,spacing)/dx
 yy,xx=np.meshgrid(ys,xs,indexing='ij');coords=np.array([yy,xx])
 z=map_coordinates(smooth,coords,order=1,mode='nearest')
 w=map_coordinates(weight,coords,order=1,mode='nearest')
 z[w<.999]=np.nan
 gy,gx=np.gradient(z,spacing,spacing)
 slope=np.rad2deg(np.arctan(np.hypot(gx,gy)))
 slope[~binary_erosion(np.isfinite(z),iterations=1)]=np.nan
 return z.astype('float32'),slope.astype('float32'),xs*dx,ys*dy

regions=[]
moon_path=DATA/'luna/site01/Site01_final_adj_5mpp_surf.tif'
moon=np.asarray(Image.open(moon_path),dtype='float32')
regions.append(('luna_site01','Luna · Connecting ridge',moon,5.,5.,'LOLA, polo sur, MOON_ME DE421; alturas respecto a esfera lunar. Malla 5 m con fuerte interpolación.',str(moon_path.relative_to(ROOT))))
mars_path=DATA/'marte/cerberus/DTEED_044184_1850_044039_1850_A01.IMG'
mars,ms,label=read_pds(mars_path)
(OUT/'cerberus_etiqueta.txt').write_text(label.split('\nEND\n')[0]+'\nEND\n',encoding='utf-8')
regions.append(('marte_cerberus','Marte · Cerberus Tholi',mars,ms,ms,'HiRISE DTM; alturas sobre equipotencial Mars 2000; datos estereoscópicos.',str(mars_path.relative_to(ROOT))))
tac=np.load(ROOT/'datos/tacana_alturas.npy');tm=json.loads((ROOT/'vista_previa/tacana_fuentes.json').read_text(encoding='utf-8'))
regions.append(('tierra_tacana','Tierra · Tacaná',tac,*tm['local_spacing_m'],'Copernicus DSM EGM2008; incluye vegetación; no es un producto NASA.','datos/tacana_alturas.npy'))
stats=[];fig,axes=plt.subplots(3,2,figsize=(11,12),layout='constrained')
for row,(key,title,a,dx,dy,datum,source) in enumerate(regions):
 z,slope,x,y=common_grid(a,dx,dy)
 assert np.isfinite(slope).sum()>100
 np.savez_compressed(OUT/(key+'_100m.npz'),elevacion_m=z,pendiente_grados=slope,x_local_m=x,y_filas_m=y)
 s=slope[np.isfinite(slope)];h=z[np.isfinite(z)]
 record=dict(id=key,region=title,source=source,datum=datum,native_spacing_m=[dx,dy],output_spacing_m=100.,output_shape=list(z.shape),valid_slope_cells=int(s.size),analyzed_area_km2=float(s.size*.01),elevation_range_m=[float(h.min()),float(h.max())],relief_p95_p05_m=float(np.percentile(h,95)-np.percentile(h,5)),slope_median_deg=float(np.median(s)),slope_p90_deg=float(np.percentile(s,90)),native_missing_fraction=float(1-np.isfinite(a).mean()))
 if key=='luna_site01':
  counts=np.asarray(Image.open(DATA/'luna/site01/Site01_final_adj_5mpp_ldec.tif'))
  record['native_fraction_with_direct_lola_returns']=float(np.mean(counts>0))
 stats.append(record)
 image=axes[row,0].imshow(z,extent=[x[0]/1000,x[-1]/1000,y[-1]/1000,y[0]/1000],cmap='terrain')
 axes[row,0].set(title=title,xlabel='X local (km)',ylabel='Y local, dirección de filas (km)');fig.colorbar(image,ax=axes[row,0],label='Elevación (m; datum propio)')
 axes[row,1].hist(s,bins=np.arange(0,91,2),density=True,color=['#596b7d','#a35d41','#477256'][row]);axes[row,1].set(xlabel='Pendiente (grados)',ylabel='Densidad',xlim=(0,60),title='Malla común de 100 m')
fig.savefig(OUT/'comparacion_regional.png',dpi=150);plt.close(fig)
method={'method':'Filtro gaussiano normalizado con sigma = 50 m; remuestreo bilineal a 100 m; se exige soporte válido >=99.9%; gradiente central con separación de 100 m; atan de magnitud del gradiente. Un píxel de borde excluido.','not_official':'Las pendientes de 100 m son derivados calculados localmente, no productos publicados por NASA.','limits':['Son tres regiones diferentes y con extensiones distintas; no representan distribuciones globales.','Resolución de malla no equivale a resolución efectiva: LOLA contiene interpolación.','No comparar altitudes absolutas de diferentes cuerpos/datums; comparar relieve relativo y pendientes a la misma escala.','DSM terrestre incluye vegetación. La comparabilidad geométrica no elimina diferencias de sensor y reconstrucción.','NPZ usa coordenadas métricas locales relativas al primer centro de píxel; consultar etiquetas originales para georreferenciar.'],'regions':stats}
(OUT/'comparacion.json').write_text(json.dumps(method,ensure_ascii=False,indent=2),encoding='utf-8')

# Global context sampled only for display. These PNGs are not analytical rasters.
glob_moon=np.asarray(Image.open(DATA/'luna/global/ldem_16.tif'),dtype='float32')*1000
glob_mars=np.memmap(DATA/'marte/global/megt90n000fb.img',dtype='>i2',shape=(5760,11520))
fig,axes=plt.subplots(2,1,figsize=(12,10),layout='constrained')
for ax,a,title,extent in [(axes[0],glob_moon,'Luna · LOLA · 16 píxeles/grado',[-180,180,-90,90]),(axes[1],glob_mars,'Marte · MOLA · 32 píxeles/grado',[0,360,-90,90])]:
 stride=max(1,a.shape[1]//1440);im=ax.imshow(a[::stride,::stride],extent=extent,cmap='terrain');ax.set(title=title,xlabel='Longitud este (°)',ylabel='Latitud (°)');fig.colorbar(im,ax=ax,label='Elevación (m; referencia propia)')
fig.savefig(OUT/'relieve_global.png',dpi=130);plt.close(fig)
globalmeta={'moon':{'shape':list(glob_moon.shape),'file':'luna/global/ldem_16.tif','stored_units':'km','to_meters':1000,'nominal_pixel_m':2*math.pi*1737400/360/16,'reference':'Esfera de radio 1737.4 km','longitude':'−180..180 E, centrado en 0; norte arriba','range_m':[float(glob_moon.min()),float(glob_moon.max())]},'mars':{'shape':list(glob_mars.shape),'file':'marte/global/megt90n000fb.img','dtype':'>i2','stored_units':'m','nominal_pixel_m':2*math.pi*3396000/360/32,'reference':'Areoide GMM3 (mgm1025), grado/orden 50, IAU2000; ver etiqueta','longitude':'0..360 E, norte arriba','range_m':[int(glob_mars.min()),int(glob_mars.max())]}}
(OUT/'global_metadata.json').write_text(json.dumps(globalmeta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False,indent=2))
