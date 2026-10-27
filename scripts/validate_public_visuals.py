"""Validate the new visual edition without rewriting any previous result record."""
from pathlib import Path
import csv,hashlib,io,json,math,re,subprocess,unittest
import numpy as np
from PIL import Image
import imageio.v2 as imageio
from scripts.render_public_visuals import ROOT,FOLDER,NAMES,renderer,source

BASE='b6fffe6484b35a5f54d4a7df13e7474627727742'

def main():
    FOLDER.mkdir(parents=True,exist_ok=True)
    report=FOLDER/'validation.json'
    report.write_text('{"status":"running"}',encoding='utf-8')
    checks=0
    def check(ok,label):
        nonlocal checks
        if not ok:raise AssertionError(label)
        checks+=1
    # Compare existing files to Git blob IDs directly; no normalization or edits.
    tree=subprocess.check_output(['git','ls-tree','-r',BASE],cwd=ROOT,text=True).splitlines()
    preserved={}
    for line in tree:
        meta,name=line.split('\t',1)
        if name in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md','.gitignore'] or name.startswith(('docs/','scripts/')):continue
        path=ROOT/('results/archive/source_manifest_viii_ko.json' if name=='results/source_manifest.json' else name)
        data=path.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        check(blob==meta.split()[2],'Existing file preserved: '+name)
        preserved[path.relative_to(ROOT).as_posix()]=hashlib.sha256(data).hexdigest()
    preservation=dict(base_commit=BASE,backup_branch='backup/pre-public-visuals-b6fffe6',
        exception='Prose, source-upload policy and validators may change; the prior translation manifest is archived. Numerical code, data and media remain checked.',unchanged_files=len(preserved),sha256=preserved)
    (FOLDER/'preservation.json').write_text(json.dumps(preservation,indent=2),encoding='utf-8')
    # Run existing model tests, recording their new execution in this edition.
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    check(result.wasSuccessful(),'Existing Python model suite')
    (FOLDER/'python_tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    from scripts.run_native_audit import validate_data
    for folder in [ROOT/'results',ROOT/'results/native_audit_repeat']:
        check(validate_data(folder)['raw_aggregates']=='passed','Retained native raw aggregates')
    from scripts.visualize_workflow_v5 import race_state,UNITS,PER_TILE
    from scripts.visualize_v4 import NativeStudy,METHODS
    native=NativeStudy();check(UNITS*PER_TILE==native.n==10000000,'Tiles represent the actual task count')
    for start,span,baseline in [(.9,6,METHODS[0]),(8.2,5,'FP32 summed-angle trig')]:
        for m in [baseline,*METHODS[1:]]:
            finish=start+span*native.ms(m)/native.ms(baseline)
            check(abs(race_state(finish,native)[2][m]-1)<1e-10,'Measured relative completion '+m)
        for t in np.linspace(start,start+span,101):
            _,elapsed,ps=race_state(float(t),native)
            for m,p in ps.items():
                check(np.isclose(p,min(1,elapsed/native.ms(m))),'Common replay clock '+m)
    from scripts.visualize_public_principle import numerical_example
    v=numerical_example();ac,bd,ad,bc=v['products']
    check(abs(complex(ac-bd,ad+bc)-complex(v['conventional']))<2e-7,'Four products reconstruct the conventional result')
    check(v['index']==126 and v['q15']==(23452,22883),'Public arithmetic actual Q15 example')
    actual=math.degrees(math.remainder(np.angle(v['output'])-np.angle(v['conventional']),math.tau))
    check(abs(actual-v['angle_error_deg'])<2e-5,'Public arithmetic real output gap')
    from scripts.visualize_public_precision import quantized_deg,WINDOW_DEG,accuracy_rows
    angles=np.random.default_rng(20261027).uniform(0,WINDOW_DEG,10001)
    for n in [1024,2048]:
        q=quantized_deg(angles,n);expected=np.floor(angles*n/360)*(360/n)
        check(np.allclose(q,expected,rtol=0,atol=1e-12),'True floor stairs Z'+str(n))
        check(np.all((angles-q>=-1e-12)&(angles-q<360/n+1e-12)),'Actual single-input bin gap')
        q0=float(quantized_deg(.29,n))
        check(np.isclose(2*(.29-q0),.58-2*q0),'Two-input floor error accumulation')
    check(accuracy_rows()==native.accuracy,'Precision uses the retained 10M product accuracy rows')
    from scripts.visualize_bit_lut_v5 import CASES,case_values
    for case,expected in zip(CASES,[(0,0,32767),(126,22883,23452),(252,22883,23452)]):
        v=case_values(*case)
        check((v['index'],v['sine_q15'],v['cosine_q15'])==expected,'Actual register/address/Q15 example')
        check(v['full_sum']==v['index']+(v['carry']<<v['bits']),'Upper carry is the only discarded bit')
        carry=0
        for row in v['trace']:
            total=row['a']+row['b']+carry
            check(row['carry_in']==carry and row['sum']==total%2 and row['carry_out']==total//2,'Actual ripple carry')
            carry=total//2
    from scripts.visualize_photo_noise import _study
    images,metrics,summary=_study()
    for name,arrays in images.items():
        with np.load(ROOT/f'results/visual_study/{name}_outputs.npz') as recorded:
            for key,array in arrays.items():check(np.array_equal(array,recorded[key]),'Unchanged recorded photo/fixture '+name+'/'+key)
    with (ROOT/'results/expanded_noise.csv').open() as f:noise=list(csv.DictReader(f))
    for key,row in metrics.items():
        expected=next(r for r in noise if (r['image'],r['method'])==key and float(r['sigma'])==.06 and int(r['seed'])==20261020)
        check(row==expected,'Photo metrics match the exact displayed case')
    # Test motion in the main visual region, excluding headers and footnotes.
    probes={'public_cpu_workflow':(2,2.5),'public_phase_computing':(4,4.5),
        'public_phase_precision':(3,4),'phase_bits_to_lut':(1.2,1.8),
        'photo_noise_comparison':(.45,1.1),'project_overview':(.5,1.3)}
    motion=[]
    for name,(a,b) in probes.items():
        aa=np.asarray(source(name,a).crop((70,270,1850,960)),dtype=np.int16)
        bb=np.asarray(source(name,b).crop((70,270,1850,960)),dtype=np.int16)
        delta=np.abs(aa-bb);mean=float(delta.mean());changed=float(np.mean(np.max(delta,axis=2)>5))
        check(mean>.08 and changed>.0005,'Actual main-region image motion '+name)
        motion.append(dict(name=name,times=[a,b],main_region_mean_abs_change=mean,changed_pixel_fraction=changed))
    media=[]
    for name in NAMES:
        _,_,duration=renderer(name);gd=12 if name=='project_overview' else duration
        times=[0,1200,3520,int(gd*500)//40*40,int((gd-.92)*1000)//40*40]
        with Image.open(ROOT/f'animations/{name}.gif') as im:
            check(im.size==(960,540),'GIF dimensions '+name)
            check(im.info.get('loop')==0,'Loop metadata '+name)
            timeline=0;errors=[];first=None;last=None;amber_distance=None
            for i in range(im.n_frames):
                im.seek(i);ms=im.info.get('duration',0);rgb=im.convert('RGB')
                if first is None:first=np.asarray(rgb,dtype=np.int16)
                last=np.asarray(rgb,dtype=np.int16)
                if any(timeline<=p<timeline+ms for p in times):
                    reference=source(name,timeline/1000,gif=True).resize((960,540),Image.Resampling.LANCZOS)
                    error=float(np.mean(np.abs(np.asarray(reference,dtype=np.int16)-last)))
                    check(error<9,'Decoded GIF matches renderer '+name);errors.append(error)
                color_time=3400 if name=='phase_bits_to_lut' else (11080 if name=='project_overview' else None)
                if color_time is not None and timeline<=color_time<timeline+ms:
                    amber_distance=int(np.min(np.sum(np.abs(last-np.array([250,198,110])),axis=2)))
                    check(amber_distance<15,'Semantic carry/warning amber survives GIF palette '+name)
                timeline+=ms
            check(timeline==int(gd*1000),'GIF full duration '+name)
            check(im.n_frames>=30,'Visible GIF sequence '+name)
            loop_error=float(np.mean(np.abs(first-last)))
            check(loop_error<5,'Smooth GIF loop join '+name)
            frames=im.n_frames
        reader=imageio.get_reader(str(ROOT/f'animations/video/{name}.mp4'));meta=reader.get_meta_data();nframes=0
        try:
            for frame in reader:
                check(frame.shape[:2]==(1080,1920),'Decoded MP4 frame dimensions '+name);nframes+=1
        finally:reader.close()
        check(nframes==int(duration*24),'Every MP4 frame decodes '+name)
        check(abs(meta['fps']-24)<.01 and abs(meta['duration']-duration)<.1,'MP4 timing '+name)
        media.append(dict(name=name,gif_duration_s=gd,gif_nominal_fps=25,gif_decoded_frames=frames,
            gif_bytes=(ROOT/f'animations/{name}.gif').stat().st_size,gif_source_max_mae=max(errors),loop_join_mae=loop_error,
            amber_min_rgb_l1_distance=amber_distance,
            mp4_duration_s=duration,mp4_fps=24,mp4_decoded_frames=nframes,mp4_bytes=(ROOT/f'animations/video/{name}.mp4').stat().st_size))
    for path in [ROOT/'README.md',*list((ROOT/'docs').glob('*.md'))]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                check((path.parent/target.split('#')[0]).exists(),'Document link '+target)
    published=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().strip('\0').split('\0')
    files=[ROOT/p for p in published if (ROOT/p).is_file()]
    from scripts.source_policy import validate_source
    check(validate_source(ROOT)['source_id']=='VIII-EN','Only the unchanged owner-approved English PDF is included')
    for p in files:
        if p.suffix.lower() in ['.md','.py','.cpp','.v','.json','.csv','.txt','.hex'] or p.name=='LICENSE':
            check(not re.search('[\uac00-\ud7af\u1100-\u11ff]',p.read_text(encoding='utf-8')),'English publication text '+p.relative_to(ROOT).as_posix())
    record=dict(status='passed',check_count=checks,existing_python_tests=result.testsRun,
        preserved_previous_files=len(preserved),native_remeasured=False,new_benchmark_results=False,
        numerical_probes_per_quantizer=10001,media=media,motion_checks=motion,
        review='Full-size and 720-pixel author/independent-agent review; not a human comprehension study',
        hardware='No new RTL simulation, synthesis or physical PIM measurements',
        plp='Independent experimental substitutes, not validated original PLP equations')
    report.write_text(json.dumps(record,indent=2),encoding='utf-8')
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p!=FOLDER/'sha256_manifest.json'}
    (FOLDER/'sha256_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
