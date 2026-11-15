"""Render small global relief maps from existing NASA elevation grids."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from matplotlib import colormaps
from matplotlib.colors import LightSource

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'recursos/datos/nasa'
Image.MAX_IMAGE_PIXELS = None
moon = np.asarray(Image.open(DATA/'luna/global/ldem_16.tif'), dtype=float)[::8, ::8] * 1000
mars = np.memmap(DATA/'marte/global/megt90n000fb.img', dtype='>i2', shape=(5760,11520))[::16, ::16].astype(float)
# Put longitude zero in the middle on both maps.
mars = np.roll(mars, mars.shape[1]//2, axis=1)
for name, heights, cmap in [('luna',moon,'gist_gray'), ('marte',mars,'copper')]:
    lo, hi = np.percentile(heights,[1,99])
    normalized = np.clip((heights-lo)/(hi-lo),0,1)
    rgb = LightSource(azdeg=315,altdeg=45).shade(normalized,cmap=colormaps[cmap],vert_exag=15,blend_mode='soft')
    Image.fromarray((rgb[:,:,:3]*255).astype('uint8')).save(ROOT/'img'/f'mapa-{name}.webp',quality=88)
(ROOT/'img/mapas-fuentes.json').write_text(json.dumps({
    'description':'Miniaturas de relieve derivadas; colores y sombreado ilustrativos, no fotografías ni mapas para medición.',
    'projection':'Equirectangular, norte arriba, longitudes -180 a 180 E',
    'moon':{'source':'NASA LOLA / NASA SVS','url':'https://svs.gsfc.nasa.gov/4720/','file':'ldem_16.tif'},
    'mars':{'source':'NASA MOLA / PDS','url':'https://pds-geosciences.wustl.edu/missions/mgs/megdr.html','file':'megt90n000fb.img'}
},indent=2,ensure_ascii=False),encoding='utf-8')
