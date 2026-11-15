"""Compatibility command: generate a verified lunar crop by catalogue ID."""
import argparse
import json
from imagenes_catalogo import generate
from pds_raster import nasa_dns

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('region', help='Official ID, for example MOON:12671')
    parser.add_argument('--view', choices=['full', 'analysis'], default='full')
    args = parser.parse_args()
    nasa_dns()
    print(json.dumps(generate('MOON', args.region, args.view), ensure_ascii=True))
