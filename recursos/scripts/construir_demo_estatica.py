"""Prepare the static demo locally, prioritizing the HTML's selected regions."""
import argparse,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def run(name,*args):
    subprocess.run([sys.executable,str(HERE/name),*args],cwd=HERE.parents[1],check=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--priority-only',action='store_true',help='Prepare only the 196 regions displayed in the main HTML.')
    args=parser.parse_args()
    run('filtrar_sismos_tacana.py')
    run('preparar_imagenes_estaticas.py','--priority-only','--workers','1','--export-progress')
    if args.priority_only:
        run('exportar_demo_estatica.py','--allow-incomplete')
        import json
        report=json.loads((HERE.parent/'github-pages/build-report.json').read_text())
        if not report['html_images_complete']:raise SystemExit('Some HTML images remain pending; inspect build-report.json.')
        run('verificar_imagenes_html.py')
        print('All HTML images are ready. Other catalogue images may still be pending.',flush=True)
        return
    run('preparar_imagenes_estaticas.py','--workers','1','--export-progress')
    run('exportar_demo_estatica.py')

if __name__=='__main__':main()
