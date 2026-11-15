"""Serve the project locally. --actualizar recomputes both comparisons first."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import subprocess
import sys
import json
import time,math
from urllib.parse import urlparse, parse_qs
from imagenes_catalogo import generate, OUT as IMAGE_CACHE, LEGACY_OUT
from pds_raster import nasa_dns,RateLimited,COOLDOWN

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Retain public image URLs while keeping generated assets outside the
        # workspace watched by Live Server. Only direct cache files are served.
        parsed=urlparse(path).path
        prefix='/recursos/comparador_imagenes/regiones_catalogo/'
        if parsed.startswith(prefix):
            name=parsed[len(prefix):]
            if name and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_.' for c in name) and name not in ('.','..'):
                cached=IMAGE_CACHE/name
                if cached.is_file():return str(cached)
                return str(LEGACY_OUT/name)
        return super().translate_path(path)
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path!='/api/region-image':return super().do_GET()
        q=parse_qs(parsed.query)
        retry_after=None
        try:
            data=generate(q.get('body',[''])[0],q.get('region',[''])[0],q.get('view',['full'])[0])
            payload=json.dumps(data,ensure_ascii=False).encode('utf-8');status=200
        except RateLimited:
            retry_after=max(1,math.ceil(float(COOLDOWN.read_text())-time.time())) if COOLDOWN.exists() else 3600
            payload=json.dumps({'error':f'El archivo PDS ha limitado temporalmente las descargas. Esta imagen aún no está disponible. Vuelve a intentarlo en {math.ceil(retry_after/60)} minutos.','retry_after_seconds':retry_after},ensure_ascii=False).encode('utf-8');status=429
        except Exception as error:
            payload=json.dumps({'error':str(error)},ensure_ascii=False).encode('utf-8');status=422
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        if retry_after is not None:self.send_header('Retry-After',str(retry_after))
        self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--actualizar', action='store_true')
    parser.add_argument('--puerto', type=int, default=8000)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.actualizar:
        for script in ['comparar_tacana.py', 'comparar_temperatura_tacana.py', 'calcular_similitud.py', 'ampliar_catalogo_regiones.py', 'comparar_catalogo_completo.py', 'integrar_ambiente.py', 'catalogar_condiciones.py', 'exportar_terrenos_3d.py', 'descargar_imagenes_comparador.py']:
            subprocess.run([sys.executable, str(Path(__file__).with_name(script))], cwd=root, check=True)
    nasa_dns()
    handler = partial(Handler, directory=str(root))
    with ThreadingHTTPServer((args.host, args.puerto), handler) as server:
        print(f'Abre http://127.0.0.1:{args.puerto}/ — Ctrl+C para detener.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()
