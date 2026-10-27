"""Verify a locally supplied research PDF against the reviewed source fingerprint."""
import argparse,hashlib,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf',type=Path,help='PDF to compare with the primary English reference; this command only reads it.')
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    source=json.loads((root/'results/source_manifest.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256(a.pdf.read_bytes()).hexdigest()
    match=digest==source['sha256']
    print(json.dumps({'source_id':source['source_id'],'sha256':digest,'matches_reviewed_source':match},indent=2))
    return 0 if match else 1

if __name__=='__main__':raise SystemExit(main())
