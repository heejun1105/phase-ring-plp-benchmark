"""Validate the paper and prose update without changing measurements or media."""
from pathlib import Path
import hashlib,io,json,re,subprocess,unittest
from scripts.source_policy import validate_source

ROOT=Path(__file__).resolve().parents[1]
BASE='68305e034cc141a3b00063bf90092754664ca4a0'

def main():
    source=validate_source(ROOT);frozen={}
    for row in subprocess.check_output(['git','ls-tree','-r',BASE],cwd=ROOT,text=True).splitlines():
        meta,name=row.split('\t',1)
        fixed=name.startswith(('animations/','src/','hardware/','native/','tests/'))
        fixed=fixed or (name.startswith('results/') and Path(name).suffix.lower() in ['.csv','.npz','.png'])
        if not fixed:continue
        from scripts.media_history import historical_path
        path=ROOT/historical_path(name)
        data=path.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=meta.split()[2]:raise AssertionError('Unexpected experiment change: '+name)
        frozen[path.relative_to(ROOT).as_posix()]=hashlib.sha256(data).hexdigest()
    old_manifest=subprocess.check_output(['git','show',BASE+':results/source_manifest.json'],cwd=ROOT)
    assert old_manifest==(ROOT/'results/archive/source_manifest_viii_ko.json').read_bytes()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'));stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream).run(suite)
    assert result.wasSuccessful(),stream.getvalue()
    # Historical report commands must not restore the former translation/no-PDF README.
    before=(ROOT/'README.md').read_bytes()
    from scripts import build_report,gallery_report,refinement_report
    for generator in [build_report,gallery_report,refinement_report]:
        generator.main()
        assert (ROOT/'README.md').read_bytes()==before,'A historical generator restored an outdated README'
    links=0
    for p in [ROOT/'README.md',ROOT/'paper/README.md',*list((ROOT/'docs').glob('*.md'))]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith(('#','mailto:')):
                assert (p.parent/target.split('#')[0]).exists(),f'{p.name}: {target}'
                links+=1
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().strip('\0').split('\0')
    for name in names:
        p=ROOT/name
        if p.suffix.lower() in ['.md','.py','.json','.csv','.txt','.v','.cpp','.hex'] or p.name=='LICENSE':
            assert not re.search('[\uac00-\ud7af\u1100-\u11ff]',p.read_text(encoding='utf-8')),name
    record=dict(status='passed',baseline=BASE,unchanged_scientific_files=len(frozen),
        measurement_or_algorithm_changes=False,original_media_preserved_including_named_archives=True,english_original_sha256=source['sha256'],
        original_language='English',translation_pdf_included=False,previous_source_manifest_preserved=True,
        python_tests=result.testsRun,local_links_checked=links,historical_generators_preserve_current_readme=True,
        readme_order=['Wave-angle calculation','Photograph denoising','Paper and scope','Reproduction and supporting material','Paper and author'],
        publication_language='English',sha256=frozen)
    (ROOT/'results/reader_review.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().strip('\0').split('\0')
    manifest={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names if name!='results/reader_sha256_manifest.json' and (ROOT/name).is_file()}
    (ROOT/'results/reader_sha256_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='sha256'},indent=2))

if __name__=='__main__':main()
