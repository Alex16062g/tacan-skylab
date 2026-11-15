"""Generate local browser geometry; retain every triangle from the Mars OBJ."""
from pathlib import Path
import base64,json,zipfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'vista_previa'
Image.MAX_IMAGE_PIXELS=None
im=Image.open(ROOT/'datos/ldem_64.tif')
a=np.memmap(ROOT/'datos/ldem_64.tif',dtype='<f4',mode='r',offset=im.tag_v2[273][0],shape=(im.height,im.width))
heights=np.array(a[::45,::45],dtype='<f4')
def encode(a):return base64.b64encode(a.tobytes()).decode()
v=[];uv=[];corners=[]
with zipfile.ZipFile(ROOT/'datos/trekOBJ.zip') as z:
    for line in z.read('model.obj').decode().splitlines():
        parts=line.split()
        if not parts:continue
        if parts[0]=='v':v.append(list(map(float,parts[1:4])))
        elif parts[0]=='vt':uv.append(list(map(float,parts[1:3])))
        elif parts[0]=='f':
            face=[]
            for token in parts[1:]:
                ids=token.split('/')
                vi=int(ids[0]);vi=vi-1 if vi>0 else len(v)+vi
                ti=int(ids[1]) if len(ids)>1 and ids[1] else 0
                ti=ti-1 if ti>0 else len(uv)+ti if ti<0 else -1
                face.append(v[vi]+(uv[ti] if ti>=0 else [0.,0.]))
            for i in range(1,len(face)-1):corners.extend([face[0],face[i],face[i+1]])
    texture='data:image/png;base64,'+base64.b64encode(z.read('texture.png')).decode()
vertices,indices=np.unique(np.asarray(corners,dtype='<f4'),axis=0,return_inverse=True)
data=dict(moon=dict(width=heights.shape[1],height=heights.shape[0],heights=encode(heights)),mars=dict(vertices=encode(vertices),indices=encode(indices.astype('<u4')),texture=texture,triangles=len(indices)//3))
(OUT/'datos3d.js').write_text('window.PLANET_DATA='+json.dumps(data,separators=(',',':'))+';',encoding='utf-8')
# Preserve the declared origin and the model's unresolved spatial units.
path=OUT/'inventario.json'
if path.exists():
    inventory=json.loads(path.read_text(encoding='utf-8'))
    for r in inventory:
        if r['archivo']=='trekOBJ.zip':r.update(cuerpo='Marte',evidencia='Procedencia marciana confirmada explícitamente por el usuario. Coordenadas locales; región y unidades físicas no especificadas.')
    path.write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Luna: {heights.shape}; Marte: {len(vertices)} vértices con UV, {len(indices)//3} triángulos')
