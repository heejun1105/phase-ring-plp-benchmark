"""Verify the final refinement preserved the prior measured evidence and five demos."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='bf5373190a931918c66ed8f14525cd33ae526abc'
KEEP=['computing_architecture','benchmark_speed_race','phase_overflow_lut','phase_precision_comparison','edge_preservation_comparison']

def main():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    evidence={}
    for name in names:
        p=Path(name)
        data=name.startswith('results/') and (p.suffix in ['.csv','.npz'] or (p.suffix=='.json' and p.name not in ['sha256_manifest.json','validation.json','visualization_environment.json','visual_dependency_licenses.json']))
        media=name.startswith('animations/') and any(p.stem==k for k in KEEP)
        source=name in ['src/plp/__init__.py','src/phase_ring/__init__.py','src/conventional/__init__.py','native/benchmark.cpp']
        if not (data or media or source):continue
        original=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        digest=hashlib.sha256(original).hexdigest()
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise AssertionError('Previously valid evidence changed: '+name)
        evidence[name]=digest
    record=dict(base_commit=BASE,backup_branch='backup/pre-final-refinement-bf53731',
        scope='Delivery preservation check; deliberately remeasuring current-run files later will change these hashes',
        unchanged_files=len(evidence),preserved_demos=KEEP,sha256=evidence)
    (ROOT/'results/refinement_preservation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(f'Preserved {len(evidence)} evidence/code/media files from {BASE[:7]}.')

if __name__=='__main__':main()
