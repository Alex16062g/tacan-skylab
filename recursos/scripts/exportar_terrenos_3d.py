"""Export the same smoothed 7x7 terrain grids used by the 2 km comparison."""
import json
import hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from comparar_catalogo_completo import ROOT, FINE, HALF, RADII, coordinates, sample, reference_patches


def terrain(patch, name, center, source):
    smooth = gaussian_filter(patch, sigma=(0, 2000/(2*FINE), 2000/(2*FINE)), mode='nearest', truncate=3.)
    indices = np.rint((np.arange(-6000,6001,2000)+HALF)/FINE).astype(int)
    z = smooth[0][np.ix_(indices,indices)]
    return dict(name=name, center=center, heights_m=z.tolist(), median_m=float(np.median(z)),
                source=str(source.relative_to(ROOT)), sha256=hashlib.sha256(source.read_bytes()).hexdigest())


def main():
    summary=json.loads((ROOT/'recursos/comparacion_tacana/similitud_catalogo_resumen.json').read_text(encoding='utf-8'))
    patch,source=reference_patches()
    reference=terrain(patch,'Tacaná',[-92.109,15.132],source)
    out=ROOT/'recursos/comparador_3d';out.mkdir(exist_ok=True)
    for body in ['MOON','MARS']:
        selected=summary['selections'][body]['selected_region']
        region=next(r for r in summary['regions'] if r['region']==selected)
        if body=='MOON':
            source=ROOT/'recursos/datos/nasa/luna/global/ldem_16.tif'
            grid=np.asarray(Image.open(source),dtype=np.float32)*1000
            grid=np.roll(grid,-grid.shape[1]//2,axis=1)
        else:
            source=ROOT/'recursos/datos/nasa/marte/global/megt90n000fb.img'
            grid=np.asarray(np.memmap(source,dtype='>i2',shape=(5760,11520)),dtype=np.float32)
        center=[region['location']['longitude'],region['location']['latitude']]
        lat,lon=coordinates([center[1]],[center[0]],RADII[body])
        comparison=terrain(sample(grid,lat,lon),region['name'],center,source)
        # Reproduce slope samples independently from the exported grid.
        for model,values in [(reference,summary['reference']['samples']['2000']['mean_slope_deg']),
                             (comparison,next(f['samples'] for f in region['primary']['features'] if f['variable']=='mean_slope_deg'))]:
            z=np.asarray(model['heights_m'])
            slopes=np.degrees(np.arctan(np.hypot((z[1:-1,2:]-z[1:-1,:-2])/4000,(z[2:,1:-1]-z[:-2,1:-1])/4000)))
            assert np.allclose(slopes.ravel(),values,rtol=1e-12,atol=1e-12)
        result=dict(body=body,region_id=selected,window_m=12000,spacing_m=2000,
                    rows='south to north',columns='west to east',vertical_origin='median of each 7x7 grid',
                    reference=reference,comparison=comparison,similarity=region['primary'],
                    sensitivity=region['sensitivity'],generated_utc=summary['generated_utc'],
                    limitations=['Interpolated visual surface from the 7x7 analysis grid, not native fine detail.',
                                 'Relative heights; identical horizontal and vertical scale in both views.',
                                 'Experimental similarity index, not exact equivalence or an ANOVA percentage.'])
        (out/f'{body.lower()}.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print(body,selected,'exported; slope samples verified')


if __name__=='__main__': main()
