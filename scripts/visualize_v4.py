"""Incremental native hero and image-first noise revision; retained demos stay unchanged."""
from pathlib import Path
import argparse,csv,math
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
from scripts.visual_style import *

ROOT=Path(__file__).resolve().parents[1]
DURATION=15
NATIVE='native_cpp_performance'
NOISE='noise_reduction_comparison'
NAMES=[NATIVE,NOISE]
METHODS=['FP32 four-trig product','Z1024 Q15 end-to-end','Z2048 Q15 end-to-end']
LABELS=['Conventional FP32','Phase-Ring Z1024','Phase-Ring Z2048']
COLORS=[BLUE,CYAN,GREEN]

def rows(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

class NativeStudy:
    def __init__(self):
        self.n=10_000_000
        self.timing={r['method']:r for r in rows('native_audit_benchmark.csv') if int(r['n'])==self.n}
        self.accuracy={r['method']:r for r in rows('native_audit_accuracy.csv') if int(r['n'])==self.n}
    def ms(self,m):return float(self.timing[m]['median_ms'])
    def ratio(self,m):return self.ms(METHODS[0])/self.ms(m)

def number(d,x,y,value,label,color=FG,size=76):
    txt(d,(x,y),value,size,color,True)
    txt(d,(x,y+size+8),label,27,MUTED)

def native(t,s):
    intro=t<2.3;race=2.3<=t<7.3;summary=7.3<=t<11.0
    title='One input. Three measured CPU paths.' if intro else ('Watch the measured runtime gap.' if race else ('The baseline changes the speedup.' if summary else 'Approximation buys a different error budget.'))
    im,d=scene('NATIVE C++ / SAME DOUBLE ANGLES / COMPLEX<FLOAT> OUTPUT',title,
        'Measured on a specific optimized C++ CPU workload | Unit-magnitude phase products, not general FP32 or PIM hardware')
    if intro:
        txt(d,(360,220),'10,000,000',144,FG,True)
        txt(d,(636,392),'PHASE PRODUCTS',47,MUTED,True)
        for j,(label,c) in enumerate(zip(LABELS,COLORS)):
            x=64+j*604;card(d,(x,574,x+584,904),c)
            wire(d,[(960,476),(960,513),(x+292,513),(x+292,560)],c,t/1.4+j/3)
            txt(d,(x+28,603),label,40,c,True,width=530)
            parts=[('Four trig evaluations','then complex multiply'),('Two floor quantizers','then wrapped Q15 lookup'),('Two floor quantizers','then wrapped Q15 lookup')][j]
            txt(d,(x+28,688),parts[0],32,FG,True)
            txt(d,(x+28,734),parts[1],30,MUTED)
            txt(d,(x+28,820),'Preallocated / one CPU thread',27,MUTED)
        footer(d,'Same raw angle arrays for every method. Q15 lookup is an approximation to the same unit-phase product.',
            'Table construction and allocation are outside the timed loops; quantization, lookup and output restoration are inside.')
    elif race:
        p=(t-2.3)/4.3;maxms=s.ms(METHODS[0]);elapsed=min(1,p)*maxms
        txt(d,(67,205),'COMMON LINEAR REPLAY',27,MUTED,True)
        txt(d,(1260,200),f'{elapsed:6.1f} / {maxms:.1f} ms',38,FG,True)
        for j,(m,label,c) in enumerate(zip(METHODS,LABELS,COLORS)):
            y=265+j*227;ms=s.ms(m);done=min(1,max(0,elapsed/ms));count=int(s.n*done)
            card(d,(64,y,1856,y+204),c if done>=1 else LINE)
            txt(d,(92,y+13),label,34,c,True,width=510)
            txt(d,(640,y+20),f'{ms:.2f} ms',36,FG,True)
            txt(d,(955,y+20),f'{s.n/ms/1000:.1f} M products/s',34,c,True)
            txt(d,(1480,y+20),f'{ms/maxms:.3f}x runtime',30,MUTED,True,width=350)
            d.rounded_rectangle((94,y+82,1815,y+140),radius=13,fill='#050b15')
            if done>0:d.rounded_rectangle((94,y+82,94+1721*done,y+140),radius=13,fill=c)
            txt(d,(96,y+154),f'{count:,} / {s.n:,}',28,FG,True,mono=True)
            if done>=1:
                pulse=max(0,1-abs(elapsed-ms)/maxms*6)
                glow(d,(1774,y+168),int(5+7*pulse),c)
                txt(d,(1580,y+149),'COMPLETE',30,c,True)
        footer(d,'Playback stretches measured median time onto one shared linear axis. Counters are an editorial replay.',
            'Baseline: four double-precision trig evaluations, FP32 complex multiply. Ring paths: two floor quantizers + paired Q15 LUT.')
    elif summary:
        for j,(m,c) in enumerate(zip(METHODS[1:],COLORS[1:])):
            x=64+j*916;card(d,(x,214,x+876,545),c)
            txt(d,(x+30,231),'Z1024' if j==0 else 'Z2048',43,c,True)
            txt(d,(x+30,285),f'{s.ratio(m):.2f}x',115,c,True)
            txt(d,(x+30,433),'shorter median runtime',37,FG,True)
            txt(d,(x+30,490),'vs. the four-trig product baseline',28,MUTED)
        control='FP32 summed-angle trig';cm=s.ms(control)
        card(d,(64,575,1856,951),AMBER)
        txt(d,(95,595),'OPTIMIZED MATHEMATICALLY EQUIVALENT CONTROL',31,AMBER,True)
        txt(d,(95,650),'Add angles, then evaluate cos / sin once.',43,FG,True)
        txt(d,(95,720),f'{cm:.2f} ms',77,BLUE,True)
        txt(d,(710,744),f'Z1024: {cm/s.ms(METHODS[1]):.2f}x   |   Z2048: {cm/s.ms(METHODS[2]):.2f}x',48,CYAN,True,width=1070)
        txt(d,(95,842),'Fewer trig evaluations explain a substantial part of the original gap.',32,FG,True)
        txt(d,(95,898),'Ratios depend on representation, scalar math library, loop optimization and this CPU.',28,MUTED)
        footer(d,'Measured on a specific optimized C++ CPU workload. Faster here does not establish general FP32 superiority.',
            'No in-memory chip, energy, area or physical hardware speedup was measured.',color=AMBER)
    else:
        for j,(m,label,c) in enumerate(zip(METHODS,LABELS,COLORS)):
            x=64+j*604;card(d,(x,214,x+584,872),c);a=s.accuracy[m]
            txt(d,(x+27,238),label,36,c,True,width=532)
            number(d,x+27,327,f"{float(a['angular_rmse_rad']):.2e}",'Angular RMSE (radians)',c,64)
            number(d,x+27,484,f"{float(a['complex_rmse']):.2e}",'Complex output RMSE',FG,58)
            number(d,x+27,637,f'{s.ms(m):.2f} ms','Median / 10 million products',c,63)
            txt(d,(x+27,798),f"Accuracy sample: {int(a['evaluated_samples']):,}",27,MUTED)
        txt(d,(91,908),'Floating-point rounding vs. floor quantization + Q15 table error',39,AMBER,True)
        footer(d,'Accuracy is checked against double-precision cos(a+b), sin(a+b), independently of display animation.',
            'Two warm-ups and nine randomized repeats. Sample SD and all controls are available in the linked native audit.',color=MUTED)
    return im

def renderer(name):
    if name==NATIVE:return native,NativeStudy()
    from scripts.visualize_v3 import Study
    from scripts.visualize_noise_v4 import noise_v4
    return noise_v4,Study()

def source_frame(name,t,study=None):
    fn,s=renderer(name) if study is None else study
    im=fn(t,s)
    return Image.blend(im,fn(0,s),ease((t-14.2)/0.8)) if t>14.2 else im

def export(name,preview_only=False):
    fn,s=renderer(name);study=(fn,s);folder=ROOT/'results/visualizations';folder.mkdir(exist_ok=True)
    times=[0.7,3.0,6.6,8.4,12.8] if name==NATIVE else [0.7,3.5,6.5,10.4,13.8]
    for j,t in enumerate(times):fn(t,s).save(folder/f'{name}_{j}.png')
    poster=8.3 if name==NATIVE else 5.5
    fn(poster,s).resize((720,405),Image.Resampling.LANCZOS).save(folder/f'{name}_readme_720.png')
    if preview_only:return
    target=ROOT/'animations';(target/'video').mkdir(exist_ok=True)
    with imageio.get_writer(str(target/'video'/f'{name}.mp4'),fps=24,codec='libx264',quality=None,
        ffmpeg_params=['-crf','18','-movflags','+faststart'],macro_block_size=1) as writer:
        for j in range(DURATION*24):writer.append_data(np.asarray(source_frame(name,j/24,study)))
    canvas=Image.new('RGB',(960,540*8))
    for j,t in enumerate([0,2,4,6,8,10,12,14]):canvas.paste(source_frame(name,t,study).resize((960,540)),(0,j*540))
    palette=canvas.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    # 100 ms divides 15 seconds exactly and allows full images to remain economical.
    frames=[source_frame(name,j/10,study).resize((960,540),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for j in range(150)]
    frames[0].save(target/f'{name}.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=True,disposal=1)
    print(f'Exported {name}: 15s 1080p H.264 / 960px GIF',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=NAMES);p.add_argument('--preview-only',action='store_true');a=p.parse_args()
    for name in [a.only] if a.only else NAMES:export(name,a.preview_only)

if __name__=='__main__':main()
