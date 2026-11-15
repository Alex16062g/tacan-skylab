from pathlib import Path
import hashlib, io, json, struct, zipfile
import numpy as np
from PIL import Image, PngImagePlugin
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'vista_previa'
OUT.mkdir(exist_ok=True)
Image.MAX_IMAGE_PIXELS = None  # Local scientific rasters, dimensions inspected beforehand.
records = []
seen = {}
def save(arr, name, origin):
    meta = PngImagePlugin.PngInfo()
    meta.add_text('Source', origin)
    Image.fromarray(arr).save(OUT/name, pnginfo=meta)

for p in sorted((ROOT/'datos').glob('*'),key=lambda p: ('(1)' in p.name,p.name)):
    if p.suffix not in ('.tif', '.jp2'): continue
    digest = hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
    im = Image.open(p)
    r = dict(archivo=p.name, cuerpo='Luna', dimensiones=list(im.size), modo=im.mode,
             bytes=p.stat().st_size, sha256=digest)
    if digest in seen:
        r.update(duplicado_de=seen[digest]['archivo'], preview=seen[digest]['preview'], tipo=seen[digest]['tipo'])
        records.append(r)
        continue
    if p.suffix == '.tif':
        # Uncompressed float32 TIFF: map strips without allocating the full 1 GB image.
        assert im.tag_v2[259] == 1 and im.mode == 'F'
        data = np.memmap(p, dtype='<f4', mode='r', offset=im.tag_v2[273][0], shape=(im.height,im.width))
        a = np.array(data[::16,::16])
        r.update(tipo='Elevación', evidencia='Nombre, dimensiones y formato coinciden con NASA CGI Moon Kit; TIFF sin CRS incrustado.', unidades='km (según producto NASA)', resolucion='64 píxeles/grado', cobertura='Global')
        r['min_max_completo']=[float(np.nanmin(data)),float(np.nanmax(data))]
        lo,hi=-9,11
        rgb=(matplotlib.colormaps['terrain'](np.clip((a-lo)/(hi-lo),0,1))[:,:,:3]*255).astype('uint8')
        r['escala_preview']={'min':lo,'max':hi,'unidad':'km','metodo':'Submuestreo cada 16 píxeles; color terrain; límites fijos.'}
        gray=(np.clip((a-lo)/(hi-lo),0,1)*255).astype('uint8')
        save(gray,'ldem_gris.png',p.name+'; escala lineal -9 a 11 km')
    else:
        with p.open('rb') as f:
            while True:
                n,t=struct.unpack('>I4s',f.read(8))
                if t==b'uuid':
                    geo=Image.open(io.BytesIO(f.read(n-8)[16:]));break
                f.seek(n-8,1)
        r.update(crs=geo.tag_v2[34737], escala_m_por_pixel=list(geo.tag_v2[33550])[:2], tiepoint=list(geo.tag_v2[33922]), evidencia='GeoTIFF incrustado: GCS_Moon / Moon_2000 / Moon2000_spole.')
        a=np.asarray(im)
        r['min_max_completo']=[int(a.min()),int(a.max())]
        step=max(1,im.width//1000)
        a=a[::step,::step].astype(float)
        hi=float(np.percentile(a,99))
        low=float(a.min())
        rgb=(matplotlib.colormaps['cividis'](np.clip(np.log1p(a-low)/np.log1p(max(hi-low,1)),0,1))[:,:,:3]*255).astype('uint8')
        r['escala_preview']={'min':low,'max':hi,'metodo':'log(1+valor−mínimo), saturación en percentil 99 de la muestra; contraste visual, no calibración física.'}
        r.update(tipo='Conteo de altimetría' if p.stem.startswith('ldec') else 'Capa auxiliar de albedo (LDAC)', cobertura='Polo sur', unidades='Valores almacenados; falta etiqueta PDS .LBL para validar escala y NoData')
    r['preview']=p.stem+'.png'
    save(rgb,r['preview'],p.name+'; '+r['escala_preview']['metodo'])
    records.append(r);seen[digest]=r
    print('Procesado',p.name,flush=True)

with zipfile.ZipFile(ROOT/'datos/trekOBJ.zip') as z:
    dest=OUT/'modelo';dest.mkdir(exist_ok=True)
    for name in ('model.obj','terrain.mtl','texture.png'):
        (dest/name).write_bytes(z.read(name))
    verts=[];faces=0;uv=0
    with (dest/'model.obj').open() as f:
        for line in f:
            if line.startswith('v '): verts.append([float(x) for x in line.split()[1:4]])
            elif line.startswith('f '):faces+=1
            elif line.startswith('vt '):uv+=1
    v=np.array(verts);lo=v.min(axis=0);hi=v.max(axis=0)
    # The exported terrain is a regular XY grid with repeated triangle vertices.
    xy,idx=np.unique(v[:,:2],axis=0,return_index=True)
    points=v[idx]; xs=np.unique(points[:,0]);ys=np.unique(points[:,1])
    grid=np.full((len(ys),len(xs)),-np.inf)
    np.maximum.at(grid,(np.searchsorted(ys,v[:,1]),np.searchsorted(xs,v[:,0])),v[:,2])
    grid[~np.isfinite(grid)]=np.nan
    fig=plt.figure(figsize=(10,7),facecolor='#f4f1e9');ax=fig.add_subplot(projection='3d',facecolor='#f4f1e9')
    X,Y=np.meshgrid(xs,ys)
    ax.plot_surface(X,Y,grid,cmap='copper',rcount=100,ccount=100,linewidth=0,antialiased=True)
    ax.set(xlabel='X · unidades OBJ',ylabel='Y · unidades OBJ',zlabel='Z · unidades OBJ')
    ax.set_box_aspect((1,1,max(float((hi[2]-lo[2])/(hi[0]-lo[0])),.03)))
    ax.set_zticks([round(float(hi[2]),1)])
    ax.view_init(elev=35,azim=-55)
    fig.savefig(OUT/'modelo.png',dpi=140,bbox_inches='tight',metadata={'Source':'datos/trekOBJ.zip/model.obj; geometry rendered without physical unit assumptions'})
    plt.close(fig)
    records.append(dict(archivo='trekOBJ.zip',cuerpo='Marte',tipo='Malla 3D + material + textura',bytes=(ROOT/'datos/trekOBJ.zip').stat().st_size,vertices=len(v),caras=faces,uv=uv,limites=[lo.tolist(),hi.tolist()],preview='modelo.png',evidencia='Procedencia marciana confirmada por el usuario; OBJ con coordenadas locales, región y unidades físicas no especificadas.'))
(OUT/'inventario.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('Inventario y vistas generados',flush=True)
