"""Run actual CPU measurements; no paper estimates enter these CSV files."""
from pathlib import Path
import csv, gc, importlib.metadata, json, os, platform, time, tracemalloc
from datetime import datetime, timezone
import numpy as np
import cv2
import psutil
from PIL import Image, ImageDraw, ImageFont
from skimage import data, metrics
from src import conventional as fp
from src import phase_ring as ring
from src.plp import methods, prototype

ROOT=Path(__file__).resolve().parents[2]

def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def summary(values):
    return dict(mean_ms=float(np.mean(values)),median_ms=float(np.median(values)),
                std_ms=float(np.std(values,ddof=1)),min_ms=float(min(values)),max_ms=float(max(values)))

def environment(seed,repeats):
    packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-image','opencv-python-headless','Pillow','imageio','imageio-ffmpeg','psutil']}
    info=dict(measured_at_utc=datetime.now(timezone.utc).isoformat(),platform=platform.platform(),
              python=platform.python_version(),processor=platform.processor(),logical_cpus=os.cpu_count(),
              physical_cpus=psutil.cpu_count(logical=False),ram_bytes=psutil.virtual_memory().total,
              packages=packages,seed=seed,repeats=repeats,warmups=2,opencv_threads=cv2.getNumThreads(),
              thread_environment={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']})
    if os.name=='nt':
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            info['cpu_model']=winreg.QueryValueEx(key,'ProcessorNameString')[0].strip()
    (ROOT/'results/environment.json').write_text(json.dumps(info,indent=2),encoding='utf-8')

def compute(sizes,repeats,seed):
    rng=np.random.default_rng(seed);rows=[];raw=[];accuracy=[]
    for size in sizes:
        a=rng.uniform(-np.pi,np.pi,size);b=rng.uniform(-np.pi,np.pi,size)
        x,y=fp.encode_pair(a,b)
        tasks={'FP32 kernel':(lambda:fp.multiply(x,y),x.nbytes+y.nbytes),
               'FP32 encode pair':(lambda:fp.encode_pair(a,b),a.nbytes+b.nbytes),
               'FP32 end-to-end':(lambda:fp.end_to_end(a,b),a.nbytes+b.nbytes)}
        holders=[]
        for n in [1024,2048]:
            qa,qb=ring.quantize(a,n),ring.quantize(b,n);lut=ring.make_lut(n);idx=ring.add(qa,qb,n)
            holders.extend([qa,qb,lut,idx])
            tasks.update({
                f'Z{n} add':(lambda qa=qa,qb=qb,n=n:ring.add(qa,qb,n),qa.nbytes+qb.nbytes),
                f'Z{n} LUT decode':(lambda idx=idx,lut=lut:ring.decode(idx,lut),idx.nbytes+lut.nbytes),
                f'Z{n} encoded-to-complex':(lambda qa=qa,qb=qb,n=n,lut=lut:ring.encoded_complex(qa,qb,n,lut),qa.nbytes+qb.nbytes+lut.nbytes),
                f'Z{n} quantize pair':(lambda n=n:(ring.quantize(a,n),ring.quantize(b,n)),a.nbytes+b.nbytes),
                f'Z{n} end-to-end':(lambda n=n,lut=lut:ring.end_to_end(a,b,n,lut),a.nbytes+b.nbytes+lut.nbytes),
            })
        for fn,_ in tasks.values():
            for _ in range(2): fn()
        values={name:[] for name in tasks}
        for rep in range(repeats):
            for name in rng.permutation(list(tasks)):
                fn,_=tasks[name];start=time.perf_counter_ns();result=fn();elapsed=(time.perf_counter_ns()-start)/1e6
                values[name].append(elapsed);raw.append(dict(n=size,method=name,repeat=rep,elapsed_ms=elapsed))
                del result
        for name,(fn,input_bytes) in tasks.items():
            gc.collect();tracemalloc.start();rss_before=psutil.Process().memory_info().rss
            result=fn();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            rss_after=psutil.Process().memory_info().rss;del result
            row=dict(n=size,method=name,**summary(values[name]),repeats=repeats,warmups=2,
                     ops_per_sec=size/(np.median(values[name])/1000),input_bytes=input_bytes,
                     traced_peak_alloc_bytes=peak,rss_before_bytes=rss_before,rss_after_bytes=rss_after,
                     evidence='Independently Measured Results')
            rows.append(row)
        # Precision on a fixed, explicitly disclosed prefix; this does not affect timing.
        count=min(size,200000);aa,bb=a[:count],b[:count];truth=np.exp(1j*(aa+bb))
        z=fp.multiply(x[:count],y[:count])
        def error(name,z,extra=0.0):
            angular=np.abs(np.angle(z*np.conj(truth)))
            accuracy.append(dict(n=size,method=name,evaluated_samples=count,
                angular_rmse_rad=float(np.sqrt(np.mean(angular**2))),max_angular_error_rad=float(angular.max()),
                complex_rmse=float(np.sqrt(np.mean(np.abs(z-truth)**2))),max_modulus_error=float(np.max(np.abs(np.abs(z)-1))),
                quantized_reference_rmse=extra))
        error('FP32',z)
        for n in [1024,2048]:
            qa,qb=ring.quantize(aa,n),ring.quantize(bb,n);idx=ring.add(qa,qb,n)
            z=ring.decode(idx,ring.make_lut(n));qt=np.exp(1j*idx.astype(np.float64)*(2*np.pi/n))
            error(f'Z{n}',z,float(np.sqrt(np.mean(np.abs(z-qt)**2))))
        print(f'Compute complete: {size:,} phase products',flush=True)
        del tasks,holders,a,b,x,y
        gc.collect()
    write_csv(ROOT/'results/benchmark.csv',rows);write_csv(ROOT/'results/timing_samples.csv',raw)
    write_csv(ROOT/'results/accuracy.csv',accuracy)
    # LUT setup is excluded from steady-state timing and measured independently.
    setup=[]
    for n in [1024,2048]:
        vals=[]
        for _ in range(repeats):
            start=time.perf_counter_ns();ring.make_lut(n);vals.append((time.perf_counter_ns()-start)/1e6)
        setup.append(dict(modulus=n,complex_q15_lut_bytes=ring.make_lut(n).nbytes,paper_sine_only_lut_bytes=n*2,**summary(vals)))
    write_csv(ROOT/'results/lut_setup.csv',setup)

def fixtures():
    """A CC0 photograph and an original text/edge chart; no private user imagery."""
    photo=data.camera().astype(np.float32)/255
    im=Image.new('L',(512,512),35);d=ImageDraw.Draw(im)
    candidates=[Path('C:/Windows/Fonts/arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font=next((ImageFont.truetype(str(p),42) for p in candidates if p.exists()),ImageFont.load_default())
    d.text((32,40),'PHASE RING',fill=230,font=font)
    d.text((32,105),'PLP 1024',fill=220,font=font)
    for k in range(3,15):d.line((32+k*19,210,32+k*19,340),fill=220,width=1+(k%4))
    for k in range(8):d.ellipse((32+k*58,385,45+k*58,398),fill=220)
    d.rectangle((350,225,475,330),outline=230,width=3)
    return {'camera':photo,'text_chart':np.asarray(im,dtype=np.float32)/255}

def edge_score(clean,result):
    """1/(1+relative Sobel error) on clean strong edges; higher is better."""
    def grad(x):
        return np.hypot(cv2.Sobel(x,cv2.CV_32F,1,0,ksize=3),cv2.Sobel(x,cv2.CV_32F,0,1,ksize=3))
    g=grad(clean);h=grad(result);mask=g>np.percentile(g,90)
    return float(1/(1+np.mean(np.abs(h[mask]-g[mask]))/(np.mean(g[mask])+1e-12)))

def denoise(repeats,seed):
    rows=[];raw=[];stages=[];folder=ROOT/'results/images';folder.mkdir(exist_ok=True,parents=True)
    for image_name,clean in fixtures().items():
        Image.fromarray(np.rint(clean*255).astype(np.uint8)).save(folder/f'{image_name}_clean.png')
        for sigma in [0.03,0.06,0.10]:
            for noise_seed in [seed,seed+1,seed+2]:
                noisy=np.clip(clean+np.random.default_rng(noise_seed).normal(0,sigma,clean.shape),0,1).astype(np.float32)
                tasks=methods(sigma);tasks['Noisy input']=lambda x:x.copy()
                values={name:[] for name in tasks}
                for fn in tasks.values():
                    for _ in range(2):fn(noisy)
                order=np.random.default_rng(noise_seed+int(sigma*1000))
                for rep in range(repeats):
                    for name in order.permutation(list(tasks)):
                        start=time.perf_counter_ns();out=tasks[name](noisy);elapsed=(time.perf_counter_ns()-start)/1e6
                        values[name].append(elapsed);raw.append(dict(image=image_name,sigma=sigma,seed=noise_seed,method=name,repeat=rep,elapsed_ms=elapsed))
                for name,fn in tasks.items():
                    out=fn(noisy)
                    rows.append(dict(image=image_name,sigma=sigma,seed=noise_seed,method=name,
                        psnr_db=float(metrics.peak_signal_noise_ratio(clean,out,data_range=1)),
                        ssim=float(metrics.structural_similarity(clean,out,data_range=1)),edge_preservation=edge_score(clean,out),
                        **summary(values[name]),repeats=repeats,warmups=2,
                        evidence='Experimental Prototype Results' if name.startswith('PLP') else 'Independently Measured Results'))
                    if sigma==0.06 and noise_seed==seed:
                        safe={'PLP-Inspired Experimental Prototype':'prototype','Noisy input':'noisy'}.get(name,name.lower())
                        Image.fromarray(np.rint(np.clip(out,0,1)*255).astype(np.uint8)).save(folder/f'{image_name}_{safe}.png')
                for stage,img in zip(['plane','line','point'],prototype(noisy,sigma,True)):
                    stages.append(dict(image=image_name,sigma=sigma,seed=noise_seed,stage=stage,
                        psnr_db=float(metrics.peak_signal_noise_ratio(clean,img,data_range=1)),
                        ssim=float(metrics.structural_similarity(clean,img,data_range=1)),
                        edge_preservation=edge_score(clean,img),evidence='Experimental Prototype Results'))
                    if sigma==0.06 and noise_seed==seed:
                        Image.fromarray(np.rint(np.clip(img,0,1)*255).astype(np.uint8)).save(folder/f'{image_name}_{stage}.png')
        print(f'Denoise complete: {image_name}',flush=True)
    write_csv(ROOT/'results/noise_benchmark.csv',rows);write_csv(ROOT/'results/noise_timing_samples.csv',raw)
    write_csv(ROOT/'results/stage_quality.csv',stages)

def main(sizes=(10000,100000,1000000,10000000),repeats=7,seed=20261020):
    cv2.setNumThreads(1);(ROOT/'results').mkdir(exist_ok=True)
    environment(seed,repeats);compute(sizes,repeats,seed);denoise(repeats,seed)

if __name__=='__main__':main()
