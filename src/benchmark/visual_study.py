"""Expanded image suite, legacy ablation, precision sweep and animation inputs."""
from pathlib import Path
import csv,json,time,statistics,hashlib
from datetime import datetime,timezone
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from skimage import metrics
from src.benchmark.run import ROOT,fixtures,edge_score,write_csv,summary
from src.plp import prototype,prototype_v2,wiener_plane,guided_stage,latch,methods
from src import phase_ring as ring

def suite():
    """Six fixed images span five requested content classes; no result-based choice."""
    old=fixtures();out=dict(old)
    def font(size):
        for p in ['C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
            if Path(p).exists():return ImageFont.truetype(p,size)
        return ImageFont.load_default(size=size)
    im=Image.new('L',(512,512),25);d=ImageDraw.Draw(im)
    for j,size in enumerate([12,16,22,30,42]):
        d.text((24,24+j*83),f'PHASE {1024+j}  SRAM LUT',font=font(size),fill=225)
    out['microtext']=np.asarray(im,dtype=np.float32)/255
    yy,xx=np.indices((512,512))
    grid=np.full((512,512),0.1,np.float32)
    grid[((xx%13)==0)|((yy%17)==0)]=0.88
    grid[(xx>270)&(((xx+yy)%9)==0)]=0.95
    out['line_grid']=grid
    im=Image.new('L',(512,512),25);d=ImageDraw.Draw(im)
    d.rectangle((40,40,230,225),fill=220);d.ellipse((275,40,475,240),fill=180)
    d.polygon([(80,450),(250,270),(420,450)],fill=240)
    for k in range(7):d.rectangle((300+k*20,280,307+k*20,310+k*15),fill=210)
    out['geometry']=np.asarray(im,dtype=np.float32)/255
    out['dark_texture']=(0.02+0.18*old['camera']).astype(np.float32)
    return out

def quality(clean,x):
    return dict(psnr_db=float(metrics.peak_signal_noise_ratio(clean,x,data_range=1)),
        ssim=float(metrics.structural_similarity(clean,x,data_range=1)),edge_preservation=edge_score(clean,x),
        mse=float(np.mean((x.astype(np.float64)-clean)**2)))

def algorithms(sigma):
    return {**{k:v for k,v in methods(sigma).items() if not k.startswith('PLP')},
        'Legacy V1':lambda x:prototype(x,sigma),
        'Prototype V2':lambda x:prototype_v2(x,sigma),
        'Noisy input':lambda x:x.copy()}

def time_calls(tasks,x,repeats,rng):
    for fn in tasks.values():
        for _ in range(2):fn(x)
    samples={name:[] for name in tasks}
    for rep in range(repeats):
        for name in rng.permutation(list(tasks)):
            start=time.perf_counter_ns();out=tasks[name](x);ms=(time.perf_counter_ns()-start)/1e6
            samples[name].append(ms);del out
    return samples

def expanded_noise(repeats=7,seed=20261020):
    cv2.setNumThreads(1);rows=[];raw=[];ablation=[];abraw=[];manifest=[]
    folder=ROOT/'results/visual_study';folder.mkdir(exist_ok=True,parents=True)
    for name,clean in suite().items():
        Image.fromarray(np.rint(clean*255).astype(np.uint8)).save(folder/f'{name}_clean.png')
        manifest.append(dict(image=name,shape=list(clean.shape),sha256_float32=hashlib.sha256(clean.tobytes()).hexdigest()))
        for sigma in [0.03,0.06,0.10]:
            for ns in [seed,seed+1,seed+2]:
                x=np.clip(clean+np.random.default_rng(ns).normal(0,sigma,clean.shape),0,1).astype(np.float32)
                tasks=algorithms(sigma);samples=time_calls(tasks,x,repeats,np.random.default_rng(ns+int(sigma*1000)))
                outputs={k:fn(x) for k,fn in tasks.items()}
                for method,output in outputs.items():
                    rows.append(dict(image=name,sigma=sigma,seed=ns,method=method,**quality(clean,output),
                        **summary(samples[method]),repeats=repeats,warmups=2,
                        evidence='Experimental Prototype Results' if method in ['Legacy V1','Prototype V2'] else 'Independently Measured Results'))
                    raw.extend(dict(image=name,sigma=sigma,seed=ns,method=method,repeat=i,elapsed_ms=ms) for i,ms in enumerate(samples[method]))
                # Ablations have their own full callable timings, not cumulative-time subtraction.
                variants={'Local mean':lambda z:cv2.boxFilter(z,-1,(5,5),borderType=cv2.BORDER_REFLECT_101),
                    'Wiener float':lambda z:wiener_plane(z,sigma),
                    'Wiener + guided float':lambda z:guided_stage(wiener_plane(z,sigma),sigma)}
                av=time_calls(variants,x,repeats,np.random.default_rng(ns+71))
                for method,fn in variants.items():
                    ablation.append(dict(image=name,sigma=sigma,seed=ns,method=method,**quality(clean,fn(x)),**summary(av[method]),repeats=repeats))
                    abraw.extend(dict(image=name,sigma=sigma,seed=ns,method=method,repeat=i,elapsed_ms=ms) for i,ms in enumerate(av[method]))
                if ns==seed and sigma==0.06:
                    arrays={'clean':clean,'noisy':x,**{k.lower().replace(' ','_'):v for k,v in outputs.items()}}
                    np.savez_compressed(folder/f'{name}_outputs.npz',**arrays)
        print(f'Expanded image suite complete: {name}',flush=True)
    write_csv(ROOT/'results/expanded_noise.csv',rows);write_csv(ROOT/'results/expanded_noise_samples.csv',raw)
    write_csv(ROOT/'results/noise_ablation.csv',ablation);write_csv(ROOT/'results/noise_ablation_samples.csv',abraw)
    (folder/'fixtures.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    rank_cases(rows,seed)

def rank_cases(rows,seed=20261020):
    """Rank the predeclared representative instead of presenting it as the best case."""
    deltas=[]
    cases={(r['image'],r['sigma'],r['seed']) for r in rows}
    for key in sorted(cases):
        rs={r['method']:r for r in rows if (r['image'],r['sigma'],r['seed'])==key}
        deltas.append(dict(image=key[0],sigma=key[1],seed=key[2],
            psnr_v2_minus_bilateral=rs['Prototype V2']['psnr_db']-rs['Bilateral']['psnr_db'],
            edge_v2_minus_v1=rs['Prototype V2']['edge_preservation']-rs['Legacy V1']['edge_preservation']))
    ordered=sorted(deltas,key=lambda r:r['psnr_v2_minus_bilateral'])
    chosen=dict(next(r for r in deltas if r['image']=='microtext' and r['sigma']==0.06 and r['seed']==seed))
    chosen.update(rank_ascending_psnr_gain=ordered.index(chosen)+1,total_cases=len(ordered),selection_rule='Predeclared microtext, sigma=0.06, first seed; not selected by quality gain',conventional_method='Bilateral',conventional_reason='Fixed edge-aware classical baseline; Gaussian and Median also measured')
    (ROOT/'results/representative_case.json').write_text(json.dumps(chosen,indent=2),encoding='utf-8')
    write_csv(ROOT/'results/noise_case_deltas.csv',deltas)

def precision():
    # A 4-degree moving probe is magnified in the animation; the data retain true angles.
    theta=np.linspace(0,np.deg2rad(4),2049,dtype=np.float64)
    rows=[]
    for t in theta:
        z=np.complex64(np.exp(1j*t))
        row=dict(input_deg=float(np.rad2deg(t)),fp32_deg=float(np.rad2deg(np.angle(z))),fp32_error_deg=float(np.rad2deg(np.angle(z*np.exp(-1j*t)))))
        for n in [1024,2048]:
            index=int(ring.quantize(t,n));restored=ring.decode(np.array([index]),ring.make_lut(n))[0]
            row.update({f'z{n}_index':index,f'z{n}_deg':float(index*360/n),f'z{n}_floor_error_deg':float(index*360/n-np.rad2deg(t)),f'z{n}_lut_error_deg':float(np.rad2deg(np.angle(restored*np.exp(-1j*t))))})
        rows.append(row)
    write_csv(ROOT/'results/precision_sweep.csv',rows)

def main(repeats=7):
    expanded_noise(repeats);precision()
    (ROOT/'results/visual_study/run.json').write_text(json.dumps(dict(measured_at_utc=datetime.now(timezone.utc).isoformat(),repeats=repeats,warmups=2,images=6,noise_levels=[0.03,0.06,0.10],seeds=[20261020,20261021,20261022],opencv_threads=1),indent=2),encoding='utf-8')

if __name__=='__main__':main()
