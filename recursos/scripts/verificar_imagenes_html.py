"""Check every displayed region's static crop, identity, encoding and checksum."""
import json,hashlib
import numpy as np
from PIL import Image
from exportar_demo_estatica import DEST
from preparar_imagenes_estaticas import html_priority
from imagenes_catalogo import catalog

def main():
    base=DEST/'recursos/comparador_imagenes'
    manifest=json.loads((base/'regiones_manifest.json').read_text(encoding='utf-8'))
    failures=[];count=0;partial=[]
    for body,ident in html_priority():
        try:
            entry=manifest['regions'][ident]
            assert entry['status']=='ready','pending image'
            data=json.loads((base/entry['metadata']).read_text(encoding='utf-8'))
            assert data['region']==ident and data['body']==body,'wrong identity'
            f=catalog(body)[ident]
            assert abs((data['center'][0]-f['longitude_east_deg']+180)%360-180)<1e-5,'wrong longitude'
            assert abs(data['center'][1]-f['latitude_deg'])<1e-5,'wrong latitude'
            path=base/data['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==data['sha256'],'checksum mismatch'
            with Image.open(path) as im:
                im.load();a=np.asarray(im.convert('RGBA'));valid=a[:,:,3]>0
                assert im.size==(512,512) or data.get('view')=='analysis','unexpected size'
                assert valid.any() and np.std(a[:,:,:3][valid])>1,'empty or constant raster'
                if not valid.all():partial.append(ident)
            assert data['source_url'].startswith('https://') and data['license_url'].startswith('https://')
            count+=1
        except Exception as error:failures.append(dict(region=ident,error=str(error)))
    report=dict(expected=len(html_priority()),verified=count,failed=failures,partial_alpha_regions=partial)
    (DEST/'html-images-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
