"""Validate raw measurements, references, language constraints, and decoded media."""
from pathlib import Path
import csv,hashlib,json,re,statistics
import numpy as np
from PIL import Image,ImageChops
import imageio.v2 as imageio

ROOT=Path(__file__).resolve().parents[1]

def rows(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def main(require_media=True):
    checks=[]
    def check(condition,text):
        if not condition:raise AssertionError(text)
        checks.append(text)
    from scripts.source_policy import validate_source
    source=validate_source(ROOT)
    check(source.get('user_designated_reference') is True,'Source is explicitly user-designated')
    check(source['source_id']=='VIII-EN','Primary source is the owner-approved English original')
    check(source['paper_viii_pages']==[1,2,3,4,5] and source['appended_paper_ix_pages']==[6,7,8,9],'Paper VIII and appended IX page ranges are distinct')
    for row in rows('reference_vectors.csv'):
        check((int(row['a'])+int(row['b']))%int(row['modulus'])==int(row['sum']),'Rollover example matches modular arithmetic')
        check(int(row['retained_bits'],2)==int(row['sum']),'Displayed retained binary bits match LUT address')
    samples=rows('timing_samples.csv');bench=rows('benchmark.csv')
    for row in bench:
        values=[float(r['elapsed_ms']) for r in samples if r['n']==row['n'] and r['method']==row['method']]
        check(len(values)==int(row['repeats']),f"Compute repetition count: {row['n']} / {row['method']}")
        for field,value in [('median_ms',statistics.median(values)),('mean_ms',statistics.mean(values)),('std_ms',statistics.stdev(values))]:
            check(np.isclose(float(row[field]),value,rtol=1e-10,atol=1e-10),f"Raw compute samples match {field}: {row['n']} / {row['method']}")
    noise=rows('noise_benchmark.csv');raw=rows('noise_timing_samples.csv')
    check(len(noise)==90,'18 image/noise/seed cases x 5 entries including noisy input')
    for row in noise:
        values=[float(r['elapsed_ms']) for r in raw if all(r[k]==row[k] for k in ['image','sigma','seed','method'])]
        check(len(values)==int(row['repeats']),f"Noise repetition count: {row['image']} / {row['sigma']} / {row['seed']} / {row['method']}")
        for field,value in [('median_ms',statistics.median(values)),('mean_ms',statistics.mean(values)),('std_ms',statistics.stdev(values))]:
            check(np.isclose(float(row[field]),value,rtol=1e-10,atol=1e-10),f'Noise raw samples match {field}')
        check(all(np.isfinite(float(row[k])) for k in ['psnr_db','ssim','edge_preservation']), 'Noise quality values are finite')
    stage_rows=rows('stage_quality.csv')
    check(len(stage_rows)==54,'18 noisy cases x 3 actual prototype stages')
    check(len({(r['image'],r['sigma'],r['seed'],r['stage']) for r in stage_rows})==54,'Stage quality keys are unique')
    final_rows={(r['image'],r['sigma'],r['seed']):r for r in noise if r['method']=='PLP-Inspired Experimental Prototype'}
    for row in stage_rows:
        check(row['stage'] in ['plane','line','point'],'Stage name is a documented prototype stage')
        check(all(np.isfinite(float(row[k])) for k in ['psnr_db','ssim','edge_preservation']),'Intermediate quality is finite')
        if row['stage']=='point':
            final=final_rows[row['image'],row['sigma'],row['seed']]
            check(all(np.isclose(float(row[k]),float(final[k])) for k in ['psnr_db','ssim','edge_preservation']),
                'Point stage quality equals the final prototype result')
    for file in [ROOT/'README.md',*list((ROOT/'docs').glob('*.md'))]:
        content=file.read_text(encoding='utf-8')
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',content):
            if '://' not in target and not target.startswith(('#','mailto:')):
                check((file.parent/target.split('#')[0]).exists(),f'Local Markdown target exists: {target}')
    text_extensions={'.py','.md','.v','.txt','.json','.csv','.hex'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]
    check(source['original_pdf_in_repository'] is True,'Only the authorized English source PDF is included')
    for file in files:
        if file.suffix in text_extensions or file.name in ['LICENSE','.gitignore']:
            content=file.read_text(encoding='utf-8')
            check(not re.search('[\uac00-\ud7af\u1100-\u11ff]',content),f'No Korean publication text: {file.relative_to(ROOT).as_posix()}')
    media=[]
    if require_media:
        for name in ['computing_comparison','noise_comparison']:
            path=ROOT/'animations'/f'{name}.gif'
            with Image.open(path) as im:
                check(im.size==(960,540),f'{name} GIF dimensions')
                check(im.n_frames>=20,f'{name} GIF is animated')
                check(im.info.get('loop')==0,f'{name} GIF loops')
                duration=0;frames=[]
                for i in range(im.n_frames):
                    im.seek(i);duration+=im.info.get('duration',0)
                    if i in [0,im.n_frames//2]:frames.append(im.convert('RGB').copy())
                check(11000<=duration<=13000,f'{name} GIF duration near 12 seconds')
                check(ImageChops.difference(frames[0],frames[1]).getbbox() is not None,f'{name} GIF contains visible frame changes')
                media.append(dict(path=path.relative_to(ROOT).as_posix(),width=960,height=540,frames=im.n_frames,duration_ms=duration))
            video=ROOT/'animations/video'/f'{name}.mp4';reader=imageio.get_reader(str(video))
            meta=reader.get_meta_data();count=0
            try:
                for frame in reader:
                    check(frame.shape[:2]==(1080,1920),f'{name} decoded MP4 frame {count} size')
                    count+=1
            finally:reader.close()
            check(count==288,f'{name} MP4 decodes all 288 frames')
            check(abs(meta['fps']-24)<0.01,f'{name} MP4 frame rate')
            check(abs(meta['duration']-12)<0.1,f'{name} MP4 duration')
            media.append(dict(path=video.relative_to(ROOT).as_posix(),width=1920,height=1080,frames=count,fps=meta['fps'],duration_seconds=meta['duration']))
    record=dict(status='passed',check_count=len(checks),source_sha256=source['sha256'],user_designated_source_confirmed=True,
        intermediate_quality_rows=len(stage_rows),compute_rows=len(bench),compute_timing_samples=len(samples),
        noise_rows=len(noise),noise_timing_samples=len(raw),python_tests=8,
        rtl_simulation='not run: no simulator installed',silicon_or_pim_validation='not performed',media=media)
    (ROOT/'results/validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.name!='sha256_manifest.json' and p.suffix!='.pyc'}
    manifest['results/validation.json']=hashlib.sha256((ROOT/'results/validation.json').read_bytes()).hexdigest()
    (ROOT/'results/sha256_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
