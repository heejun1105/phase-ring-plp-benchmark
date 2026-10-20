"""Validate retained data, new experiments, publication links and all six decoded animations."""
from pathlib import Path
import collections,contextlib,csv,hashlib,io,json,re,statistics
import numpy as np
from PIL import Image,ImageChops
import imageio.v2 as imageio
from scripts.visualize_v3 import ROOT,NAMES,Study,RENDERERS

def read(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def main(require_media=True):
    count=0
    def check(ok,label):
        nonlocal count
        if not ok:raise AssertionError(label)
        count+=1
    from scripts.validate import main as legacy
    with contextlib.redirect_stdout(io.StringIO()):legacy(require_media=False)
    legacy_record=json.loads((ROOT/'results/validation.json').read_text())
    count+=legacy_record['check_count']
    # Recompute all aggregates from raw samples, including the native study.
    for summary_name,raw_name,keys in [('expanded_noise.csv','expanded_noise_samples.csv',['image','sigma','seed','method']),
            ('noise_ablation.csv','noise_ablation_samples.csv',['image','sigma','seed','method']),
            ('native_benchmark.csv','native_samples.csv',['n','method'])]:
        if not (ROOT/'results'/summary_name).exists():continue
        raw=read(raw_name);groups=collections.defaultdict(list)
        for row in raw:groups[tuple(row[k] for k in keys)].append(float(row['elapsed_ms']))
        for row in read(summary_name):
            vals=groups[tuple(row[k] for k in keys)]
            check(len(vals)==int(row['repeats']),summary_name+' repetition count')
            for k,value in [('mean_ms',statistics.mean(vals)),('median_ms',statistics.median(vals)),('std_ms',statistics.stdev(vals))]:
                check(np.isclose(float(row[k]),value,rtol=1e-10,atol=1e-10),summary_name+' raw '+k)
            if 'psnr_db' in row:
                check(all(np.isfinite(float(row[k])) for k in ['psnr_db','ssim','edge_preservation']),summary_name+' finite quality')
    expanded=read('expanded_noise.csv')
    cases={(r['image'],r['sigma'],r['seed']) for r in expanded}
    check(len(cases)==54,'6 images x 3 sigmas x 3 seeds')
    check(len(expanded)==324,'54 cases x 6 methods including input copy control')
    check(len({(*[r[k] for k in ['image','sigma','seed']],r['method']) for r in expanded})==324,'Expanded keys unique')
    representative=json.loads((ROOT/'results/representative_case.json').read_text())
    check(representative['image']=='microtext' and representative['sigma']==0.06,'Predeclared visual representative is retained')
    points=read('precision_sweep.csv');check(len(points)==2049,'Precision sweep length')
    for row in points:
        for n in [1024,2048]:
            err=float(row[f'z{n}_floor_error_deg'])
            check(-360/n-1e-12<=err<=1e-12,'Actual floor error within one single-input bin')
    if (ROOT/'results/native_accuracy.csv').exists():
        for row in read('native_accuracy.csv'):
            n=1024 if '1024' in row['method'] else (2048 if '2048' in row['method'] else None)
            check(float(row['max_angular_error_rad'])<(4*np.pi/n+0.0001 if n else 2e-6),'Native numerical error bound')
    for path in [ROOT/'README.md',*list((ROOT/'docs').glob('*.md'))]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                check((path.parent/target.split('#')[0]).exists(),'Local document/media link: '+target)
    files=[p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]
    check(not any(p.suffix.lower()=='.pdf' for p in files),'Original PDFs excluded')
    for p in files:
        if p.suffix in ['.md','.py','.cpp','.v','.json','.csv','.txt','.hex'] or p.name=='LICENSE':
            check(not re.search('[\uac00-\ud7af\u1100-\u11ff]',p.read_text(encoding='utf-8')),'English publication text: '+p.relative_to(ROOT).as_posix())
    media=[]
    if require_media:
        study=Study()
        for name in NAMES:
            gif=ROOT/'animations'/f'{name}.gif';duration=0;errors=[]
            with Image.open(gif) as im:
                check(im.size==(960,540),'GIF size '+name);check(im.info.get('loop')==0,'Infinite loop '+name)
                check(im.n_frames>=30,'Visible animation frames '+name)
                selected={0,20,40,80,130};timeline=0;first=None;middle=None
                for i in range(im.n_frames):
                    im.seek(i);ms=im.info.get('duration',0)
                    # Test exact times, even if an encoder merges repeated frames.
                    for frame_no in sorted(selected):
                        tt=frame_no*80
                        if timeline<=tt<timeline+ms:
                            reference=RENDERERS[name](tt/1000,study).resize((960,540),Image.Resampling.LANCZOS)
                            error=float(np.mean(np.abs(np.asarray(reference,dtype=np.int16)-np.asarray(im.convert('RGB'),dtype=np.int16))))
                            errors.append(error);check(error<8,'Decoded GIF matches source scene '+name)
                    if first is None:first=im.convert('RGB').copy()
                    if timeline<=6000<timeline+ms:middle=im.convert('RGB').copy()
                    timeline+=ms;duration+=ms
                check(duration==12000,'12-second GIF '+name)
                check(middle is not None and ImageChops.difference(first,middle).getbbox() is not None,'Image content changes '+name)
                gifframes=im.n_frames
            reader=imageio.get_reader(str(ROOT/'animations/video'/f'{name}.mp4'));meta=reader.get_meta_data();frames=0
            try:
                for frame in reader:
                    check(frame.shape[:2]==(1080,1920),'Decoded MP4 dimensions '+name);frames+=1
            finally:reader.close()
            check(frames==288,'All MP4 frames decode '+name)
            check(abs(meta['fps']-24)<0.01 and abs(meta['duration']-12)<0.1,'MP4 frame rate/duration '+name)
            media.append(dict(name=name,gif_bytes=gif.stat().st_size,gif_frames=gifframes,gif_duration_ms=duration,
                decoded_source_frame_mean_abs_error=max(errors),mp4_frames=frames,mp4_fps=meta['fps'],mp4_size=[1920,1080]))
    tests=json.loads((ROOT/'results/test_results.json').read_text())
    check(tests['successful'] is True,'Recorded Python suite passed')
    record=dict(status='passed',check_count=count,python_tests=tests['tests_run'],
        retained_numpy_rows=len(read('benchmark.csv')),expanded_noise_cases=54,expanded_noise_rows=len(expanded),
        native_measured=(ROOT/'results/native_benchmark.csv').exists(),media=media,
        source_confirmed=True,rtl_simulation='not run; testbench supplied',silicon_validation='not performed')
    (ROOT/'results/validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.name!='sha256_manifest.json'}
    manifest['results/validation.json']=hashlib.sha256((ROOT/'results/validation.json').read_bytes()).hexdigest()
    (ROOT/'results/sha256_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
