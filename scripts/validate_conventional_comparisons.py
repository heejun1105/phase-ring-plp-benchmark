"""Check true conventional baselines, archived originals and all current comparison media."""
import ast,csv,hashlib,io,json,math,re,subprocess,unittest
import numpy as np
from PIL import Image
import imageio.v2 as imageio
from src import phase_ring as ring
from scripts import conventional_reference as reference
from scripts.render_conventional_comparisons import ROOT,FOLDER,ITEMS,renderer,source
from scripts.media_history import historical_path,ARCHIVES,archive_originals
from scripts.source_policy import validate_source

BASE='dc673d76bcc26c3117560fc62d643eab6b74d27e'

def main():
    FOLDER.mkdir(parents=True,exist_ok=True)
    report=FOLDER/'validation.json';report.write_text('{"status":"running"}',encoding='utf-8')
    count=0
    def check(ok,label):
        nonlocal count
        if not ok:raise AssertionError(label)
        count+=1
    archived=archive_originals();preserved={}
    for row in subprocess.check_output(['git','ls-tree','-r',BASE],cwd=ROOT,text=True).splitlines():
        meta,name=row.split('\t',1)
        freeze=name.startswith(('animations/','src/','native/','hardware/','tests/')) or (name.startswith('results/') and (ROOT/name).suffix.lower() in ['.csv','.npz','.png'])
        if not freeze:continue
        path=ROOT/historical_path(name);data=path.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        check(blob==meta.split()[2],'Original scientific asset retained directly or in archive: '+name)
        preserved[path.relative_to(ROOT).as_posix()]=hashlib.sha256(data).hexdigest()
    # Keep original numerical frame bodies as named legacy functions.
    for path,old,new in [('scripts/visualize_v3.py','precision','precision_legacy'),('scripts/visualize_public_precision.py','precision','precision_legacy'),('scripts/story_precision_targets.py','frame','frame_legacy')]:
        before=ast.parse(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True,encoding='utf-8'))
        after=ast.parse((ROOT/path).read_text(encoding='utf-8'))
        a=next(n for n in before.body if isinstance(n,ast.FunctionDef) and n.name==old)
        b=next(n for n in after.body if isinstance(n,ast.FunctionDef) and n.name==new)
        check([ast.dump(n) for n in a.body]==[ast.dump(n) for n in b.body],'Legacy frame body preserved: '+path)
    check(validate_source(ROOT)['source_id']=='VIII-EN','Authorized English paper is unchanged')
    angles=np.linspace(0,reference.WINDOW_DEG,2401);v=reference.sample(angles)
    theta=np.deg2rad(angles)
    check(np.allclose(v['fp32'],np.exp(1j*theta).astype(np.complex64),rtol=0,atol=2*np.finfo(np.float32).eps),'Conventional output follows actual FP32 reconstruction')
    check(np.any(np.abs(v['fp32_deg']-v['ideal_deg'])>0),'FP32 rounding error was not forced to zero')
    for n,key in [(1024,'z1024'),(2048,'z2048')]:
        expected=ring.end_to_end(theta,np.zeros_like(theta),n,ring.make_lut(n))
        check(np.array_equal(v[key],expected),'Output curves include real quantization and Q15 '+key)
        phase=np.rad2deg(np.arctan2(expected.imag.astype(np.float64),expected.real.astype(np.float64)))
        check(np.array_equal(v[key+'_deg'],phase),'Output phase uses actual restored channels '+key)
    p=reference.product(.29,.29)
    check(abs(float(p['fp32_deg'])-.580000021899)<1e-10,'Real FP32 product example')
    check(float(p['z1024_deg'])==0 and abs(float(p['z2048_deg'])-.3514712570)<1e-9,'Real Q15 product phases, not ideal bins')
    with (ROOT/'results/native_audit_benchmark.csv').open() as f:times={r['method']:r for r in csv.DictReader(f) if int(r['n'])==10000000}
    with (ROOT/'results/native_audit_accuracy.csv').open() as f:accuracy={r['method']:r for r in csv.DictReader(f) if int(r['n'])==10000000}
    metrics=reference.native_metrics()
    check(reference.METRIC_METHODS[0]=='FP32 summed-angle trig','Primary conventional baseline is the optimized existing route')
    for method in reference.METRIC_METHODS:
        check(metrics[method]=={**times[method],**accuracy[method]},'Same-run native metrics '+method)
        check(int(metrics[method]['evaluated_samples'])==200000,'Recorded accuracy sample scope')
    from scripts.baseline_wave_outputs import display_window,wave_values
    for t in np.linspace(0,9.3,40):
        lo,hi,bottom,top,_=display_window(float(t));xs=np.linspace(lo,hi,520)
        for key in reference.METHOD_KEYS:
            ys=wave_values(key,xs)
            check(float(ys.min())>=bottom-1e-10 and float(ys.max())<=top+1e-10,'Common wave zoom does not clip '+key)
    media=[]
    for name in ITEMS:
        _,duration,_=renderer(name);points=[0,1200,3200,6400,int((duration-.92)*1000)//40*40]
        with Image.open(ROOT/f'animations/{name}.gif') as im:
            check(im.size==(960,540) and im.info.get('loop')==0,'GIF dimensions/loop '+name)
            clock=0;errors=[];first=None;last=None
            for i in range(im.n_frames):
                im.seek(i);ms=im.info.get('duration',0);last=np.asarray(im.convert('RGB'),dtype=np.int16)
                if first is None:first=last.copy()
                if any(clock<=t<clock+ms for t in points):
                    ref=np.asarray(source(name,clock/1000).resize((960,540),Image.Resampling.LANCZOS),dtype=np.int16)
                    err=float(np.mean(np.abs(ref-last)));check(err<9,'Decoded GIF matches full conventional comparison '+name);errors.append(err)
                clock+=ms
            join=float(np.mean(np.abs(first-last)))
            check(clock==int(duration*1000) and im.n_frames>=30,'GIF timing and movement '+name)
            check(join<5,'GIF loop continuity '+name);gf=im.n_frames
        r=imageio.get_reader(str(ROOT/f'animations/video/{name}.mp4'));meta=r.get_meta_data();frames=0
        try:
            for f in r:
                check(f.shape[:2]==(1080,1920),'Decoded MP4 frame '+name);frames+=1
        finally:r.close()
        check(frames==int(duration*24) and abs(meta['fps']-24)<.01 and abs(meta['duration']-duration)<.1,'MP4 timing '+name)
        media.append(dict(name=name,duration_seconds=duration,gif_frames=gf,gif_bytes=(ROOT/f'animations/{name}.gif').stat().st_size,
            gif_max_source_mae=max(errors),loop_join_mae=join,mp4_frames=frames,methods=['Conventional FP32','Z1024','Z2048']))
    readme=(ROOT/'README.md').read_text(encoding='utf-8');depth=0;visible=set()
    for line in readme.splitlines():
        if '<details>' in line:depth+=1
        if '</details>' in line:depth-=1
        for target in re.findall(r'!\[[^\]]*\]\((animations/[^)]+\.gif)\)',line):
            check(depth==0,'Visible uncollapsed animation '+target);visible.add(target)
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'animations').glob('*.gif')}
    check(actual==visible,'All current and historical GIFs remain embedded')
    for name in actual:check('animations/video/'+name.split('/')[-1][:-4]+'.mp4' in readme,'Every view retains an MP4 link')
    for path in [ROOT/'README.md',ROOT/'paper/README.md',*list((ROOT/'docs').glob('*.md'))]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith(('#','mailto:')):check((path.parent/target.split('#')[0]).exists(),'Link '+target)
    tests=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    check(tests.wasSuccessful(),'Existing numerical model tests')
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().strip('\0').split('\0')
    for name in names:
        p=ROOT/name
        if p.suffix.lower() in ['.md','.py','.json','.csv','.txt','.cpp','.v','.hex'] or p.name=='LICENSE':check(not re.search('[\uac00-\ud7af\u1100-\u11ff]',p.read_text(encoding='utf-8')),'English publication text '+name)
    record=dict(status='passed',check_count=count,model_tests=tests.testsRun,media_count=len(media),media=media,
        unchanged_scientific_assets=len(preserved),archived_original_pairs=len(ARCHIVES),visible_gifs=len(visible),
        primary_conventional_control=reference.METRIC_METHODS[0],new_benchmark_results=False,
        source='Retained native C++ medians and 200,000-pair accuracy; illustration inputs are separate',
        public_visibility_requested_by_owner=True)
    report.write_text(json.dumps(record,indent=2),encoding='utf-8')
    (FOLDER/'preservation.json').write_text(json.dumps(dict(baseline=BASE,sha256=preserved,media_archives=archived),indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
