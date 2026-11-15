"""Native-grid spherical gradients. Values are local derivatives, not NASA products."""
from pathlib import Path
import json,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'analisis_nasa'
meta={}
for key,a,radius,ppd,factor in [('luna',np.asarray(Image.open(ROOT/'datos/nasa/luna/global/ldem_16.tif')),1737400.,16,1000.),('marte',np.memmap(ROOT/'datos/nasa/marte/global/megt90n000fb.img',dtype='>i2',shape=(5760,11520)),3396000.,32,1.)]:
 rows,cols=a.shape;dy=radius*np.pi/180/ppd
 output=np.lib.format.open_memmap(OUT/(key+'_pendiente_global_grados.npy'),mode='w+',dtype='float32',shape=a.shape)
 for start in range(0,rows,128):
  stop=min(rows,start+128);first=max(0,start-1);last=min(rows,stop+1)
  block=np.asarray(a[first:last],dtype='float32')*factor
  gy=np.gradient(block,dy,axis=0)[start-first:stop-first]
  block=block[start-first:stop-first]
  lat=90-(np.arange(start,stop)+.5)/ppd
  dx=dy*np.cos(np.deg2rad(lat))[:,None]
  gx=(np.roll(block,-1,axis=1)-np.roll(block,1,axis=1))/(2*dx)
  slope=np.rad2deg(np.arctan(np.hypot(gx,gy)));slope[np.abs(lat)>=85,:]=np.nan
  output[start:stop]=slope
 output.flush()
 meta[key]={'file':str(OUT/(key+'_pendiente_global_grados.npy')),'shape':[rows,cols],'dtype':'float32','unit':'degrees','source_ppd':ppd,'equatorial_spacing_m':dy,'sphere_radius_m':radius,'polar_exclusion':'|latitud| >=85 grados: NaN; usar DEM polar para pendientes polares','method':'Gradientes centrales, dx=R*cos(lat)*dlongitud, dy=R*dlatitud; longitud periódica; atan(hypot). Latitudes en centro de celda. Incluye celdas interpoladas del DEM.','status':'Derivado local, no pendiente publicada por NASA'}
 print(key,'pendiente global generada',flush=True)
(OUT/'pendientes_globales.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
