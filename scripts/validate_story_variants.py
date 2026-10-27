"""Check new variants, preserve old assets, and validate the curated gallery/archive."""
import csv,hashlib,io,json,math,re,subprocess,unittest
import numpy as np
from PIL import Image
import imageio.v2 as imageio
from scripts.render_story_variants import ROOT,FOLDER,ITEMS,renderer,source,gif_interval_ms
from scripts.source_policy import validate_source

BASE='6f0cce5246446093ffd88bc58777c90894357864'

def main():
    FOLDER.mkdir(parents=True,exist_ok=True)
    report=FOLDER/'validation.json';report.write_text('{"status":"running"}',encoding='utf-8')
    count=0
    def check(ok,label):
        nonlocal count
        if not ok:raise AssertionError(label)
        count+=1
    kept={};old_gifs=[]
    for line in subprocess.check_output(['git','ls-tree','-r',BASE],cwd=ROOT,text=True).splitlines():
        meta,name=line.split('\t',1)
        old=name.startswith(('animations/','src/','native/','hardware/','tests/'))
        old=old or (name.startswith('results/') and (ROOT/name).suffix.lower() in ['.csv','.npz','.png'])
        old=old or (name.startswith('scripts/') and ((ROOT/name).name.startswith('visualize_') or (ROOT/name).name=='render_public_visuals.py') and (ROOT/name).name not in ['visualize_v3.py','visualize_public_precision.py'])
        if not old:continue
        from scripts.media_history import historical_path
        path=ROOT/historical_path(name)
        data=path.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        check(blob==meta.split()[2],'Previous numerical code/data/media preserved: '+name)
        kept[path.relative_to(ROOT).as_posix()]=hashlib.sha256(data).hexdigest()
        if name.startswith('animations/') and name.endswith('.gif'):old_gifs.append(name)
    check(validate_source(ROOT)['source_id']=='VIII-EN','The authorized English original is unchanged')
    from scripts.story_phase_wave import phase
    for t in np.linspace(0,6,101):
        check(abs(math.sin(phase(t))-math.sin(phase(t+6)))<1e-12,'Circle/wave return after one full turn')
    from scripts.story_calculate_lookup import example
    e=example()
    check((e['qa'],e['qb'],e['address'],e['q15'])==(750,400,126,(23452,22883)),'Actual lookup example')
    gap=abs(math.degrees(math.remainder(math.atan2(e['stored'].imag,e['stored'].real)-math.atan2(e['calculated'].imag,e['calculated'].real),math.tau)))
    check(abs(gap-e['angle_gap_deg'])<1e-10,'Actual output angle gap')
    from scripts.story_precision_targets import quantized_deg,WINDOW_DEG,recorded_accuracy
    angles=np.random.default_rng(20261027).uniform(0,WINDOW_DEG,10001)
    for n in [1024,2048]:
        q=quantized_deg(angles,n);ref=np.floor(angles*n/360)*360/n
        check(np.allclose(q,ref,rtol=0,atol=1e-12),'True snapping positions Z'+str(n))
        check(np.all((angles-q>=-1e-12)&(angles-q<360/n+1e-12)),'Literal gap within a real bin')
        check(np.isclose(2*(.29-float(quantized_deg(.29,n))),.58-2*float(quantized_deg(.29,n))),'Two input gaps accumulate separately')
    with (ROOT/'results/native_audit_accuracy.csv').open() as f:
        expected={r['method']:r for r in csv.DictReader(f) if int(r['n'])==10000000}
    check(recorded_accuracy()==expected,'Final errors use retained native records')
    from scripts.story_wrap_fetch import state,CASES
    for j,(a,b,n) in enumerate(CASES):
        for local in np.linspace(0,5.99,144):
            v=state(j*6+float(local))
            check(v['position']==(a+v['steps'])%n and v['laps']==(a+v['steps'])//n,'Exact intermediate integer ring state')
        v=state(j*6+5.5)
        check((v['position'],v['sine_q15'])==[(0,0),(126,22883),(252,22883)][j],'Final address and scalar sine word')
    from scripts.story_noise_lens import roi
    for t in np.linspace(0,5,101):
        r=roi(float(t));check(np.isclose(r[2]-r[0],96) and np.isclose(r[3]-r[1],96),'Shared lens crop size')
        check(0<=r[0]<r[2]<=512 and 0<=r[1]<r[3]<=512,'Lens stays inside recorded photo')
    motion=[]
    for name,a,b in [('phase_wave_basics',1,1.5),('calculate_or_lookup',5,5.5),('angle_snap_targets',5,6),('wrap_and_fetch',7,8),('noise_detail_lens',1.8,2.5)]:
        aa=np.asarray(source(name,a).crop((65,260,1855,960)),dtype=np.int16)
        bb=np.asarray(source(name,b).crop((65,260,1855,960)),dtype=np.int16)
        value=float(np.mean(np.abs(aa-bb)));check(value>.08,'Actual main-image motion '+name)
        motion.append(dict(name=name,times=[a,b],main_image_mean_abs_change=value))
    media=[]
    for name in ITEMS:
        _,duration,_=renderer(name)
        points=[0,1200,3200,6400,int((duration-.92)*1000)//40*40]
        with Image.open(ROOT/f'animations/{name}.gif') as im:
            check(im.size==(960,540),'GIF size '+name);check(im.info.get('loop')==0,'GIF infinite loop '+name)
            clock=0;errors=[];first=None;last=None
            for i in range(im.n_frames):
                im.seek(i);ms=im.info.get('duration',0);rgb=im.convert('RGB')
                last=np.asarray(rgb,dtype=np.int16)
                if first is None:first=last.copy()
                if any(clock<=p<clock+ms for p in points):
                    ref=source(name,clock/1000).resize((960,540),Image.Resampling.LANCZOS)
                    err=float(np.mean(np.abs(last-np.asarray(ref,dtype=np.int16))))
                    check(err<9,'Decoded GIF matches current renderer '+name);errors.append(err)
                clock+=ms
            join=float(np.mean(np.abs(first-last)))
            check(clock==int(duration*1000),'GIF full duration '+name);check(im.n_frames>=30,'GIF contains motion '+name)
            check(join<5,'GIF last-to-first continuity '+name);nf=im.n_frames
        reader=imageio.get_reader(str(ROOT/f'animations/video/{name}.mp4'));meta=reader.get_meta_data();frames=0
        try:
            for f in reader:
                check(f.shape[:2]==(1080,1920),'Decoded MP4 frame '+name);frames+=1
        finally:reader.close()
        check(frames==int(duration*24) and abs(meta['fps']-24)<.01 and abs(meta['duration']-duration)<.1,'MP4 timing '+name)
        check((ROOT/f'animations/{name}.gif').stat().st_size<10000000,'New GIF loading-size budget '+name)
        media.append(dict(name=name,duration_seconds=duration,gif_nominal_fps=1000/gif_interval_ms(name),gif_frames=nf,gif_bytes=(ROOT/f'animations/{name}.gif').stat().st_size,
            gif_max_source_mae=max(errors),loop_join_mae=join,mp4_frames=frames,mp4_fps=24,mp4_bytes=(ROOT/f'animations/video/{name}.mp4').stat().st_size))
    from scripts.gallery_catalog import validate_gallery
    gallery=validate_gallery(ROOT,check)
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    check('https://doi.org/10.5281/zenodo.22782241' in readme[-700:] and 'mailto:voodoo6000@daum.net' in readme[-700:],'Requested DOI and email are at the end')
    for p in [ROOT/'README.md',ROOT/'paper/README.md',*list((ROOT/'docs').glob('*.md'))]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith(('#','mailto:')):
                check((p.parent/target.split('#')[0]).exists(),'Local link '+target)
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    check(tests.wasSuccessful(),'Existing model tests pass');(FOLDER/'python_tests.txt').write_text(stream.getvalue(),encoding='utf-8')
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().strip('\0').split('\0')
    for name in names:
        p=ROOT/name
        if p.suffix.lower() in ['.md','.py','.json','.csv','.txt','.v','.cpp','.hex'] or p.name=='LICENSE':
            check(not re.search('[\uac00-\ud7af\u1100-\u11ff]',p.read_text(encoding='utf-8')),'English publication text '+name)
    record=dict(status='passed',check_count=count,model_tests=tests.testsRun,new_variants=len(ITEMS),
        previous_gifs_preserved=len(old_gifs),selected_gifs_visible=gallery['selected_gifs'],
        excluded_gifs_indexed=gallery['archived_gifs'],gallery=gallery,old_scientific_assets_preserved=len(kept),
        new_benchmark_results=False,media=media,motion_probes=motion,
        doi='https://doi.org/10.5281/zenodo.22782241',email='voodoo6000@daum.net',
        link_provenance='Owner supplied; no external archive identity or new performance evidence inferred')
    report.write_text(json.dumps(record,indent=2),encoding='utf-8')
    (FOLDER/'preservation.json').write_text(json.dumps(dict(baseline=BASE,sha256=kept),indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
