"""Add five public-facing demos and a 40-second overview without replacing prior assets."""
from pathlib import Path
from functools import lru_cache
import argparse,json,math
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
from scripts.visual_style import *

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'results/public_visuals'
NAMES=['public_cpu_workflow','public_phase_computing','public_phase_precision','phase_bits_to_lut','photo_noise_comparison','project_overview']
FPS=24
GIF_FPS=25

@lru_cache(maxsize=8)
def renderer(name):
    if name=='public_cpu_workflow':
        from scripts.visualize_workflow_v5 import workflow,DURATION
        from scripts.visualize_v4 import NativeStudy
        return workflow,NativeStudy(),DURATION
    if name=='public_phase_computing':
        from scripts.visualize_public_principle import principle,DURATION
        return principle,None,DURATION
    if name=='public_phase_precision':
        from scripts.visualize_public_precision import precision,DURATION
        return precision,None,DURATION
    if name=='phase_bits_to_lut':
        from scripts.visualize_bit_lut_v5 import bit_lut,DURATION
        return bit_lut,None,DURATION
    if name=='photo_noise_comparison':
        from scripts.visualize_photo_noise import photo_noise,DURATION
        from scripts.visualize_v3 import Study
        return photo_noise,Study(),DURATION
    if name=='project_overview':return overview,None,40.0
    raise ValueError(name)

def raw(name,t):
    fn,s,duration=renderer(name)
    return fn(max(0,min(duration-.001,t)),s)

def hook(t,end=False):
    im=background().copy();d=ImageDraw.Draw(im)
    txt(d,(80,60),'PHASE-RING PIM & PLP ENGINE',48,CYAN,True)
    txt(d,(80,145),'Same task.',104,FG,True)
    txt(d,(80,270),'Different computing approach.',80,FG,True,width=1750)
    for j,(x,c,label) in enumerate([(95,BLUE,'CONVENTIONAL'),(1050,CYAN,'PHASE-RING')]):
        card(d,(x,445,x+775,870),c)
        txt(d,(x+30,462),label,42,c,True)
        if not j:
            for k in range(4):
                xx=x+55+k*165
                card(d,(xx,595,xx+120,725),c,12)
                txt(d,(xx+41,622),'+' if k%2 else '×',52,c,True)
                if k<3:wire(d,[(xx+124,660),(xx+157,660)],c,t*.8-k/4)
            waveform(d,(x+50,760,650,70),0,c,-t*2)
        else:
            cx=x+210;cy=675;r=125
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=c,width=8)
            angle=t*.9
            endpt=(cx+r*.85*math.cos(angle),cy-r*.85*math.sin(angle))
            d.line((cx,cy,*endpt),fill=c,width=10);glow(d,endpt,7,c)
            wire(d,[(cx+r+20,cy),(x+500,cy)],c,t)
            for k in range(12):
                xx=x+510+(k%4)*45;yy=605+(k//4)*50
                d.rounded_rectangle((xx,yy,xx+32,yy+31),radius=4,fill=c if k==int(t*3)%12 else LINE)
    txt(d,(85,930),'Measured CPU work. Phase arithmetic. Visible precision.',40,FG,True)
    footer(d,'Conceptual data flow. CPU results are specific workloads; no physical PIM chip is demonstrated.',color=AMBER)
    if end:
        im=background().copy();d=ImageDraw.Draw(im)
        d.ellipse((1320,320,1780,780),outline=LINE,width=5)
        angle=t*.5
        d.line((1550,550,1550+200*math.cos(angle),550-200*math.sin(angle)),fill=CYAN,width=5)
        txt(d,(110,340),'Phase-Ring PIM',115,CYAN,True)
        txt(d,(110,485),'& PLP Engine',115,FG,True)
        txt(d,(116,700),'Explore the motion. Inspect the evidence.',49,MUTED,True)
        txt(d,(116,935),'CPU measurements and experimental models — not a validated PIM chip.',30,AMBER)
    return im

def overview(t,study=None):
    if t<3:return hook(t)
    if t<13:return raw('public_cpu_workflow',(t-3)*1.38)
    if t<22:return raw('public_phase_computing',(t-13)*14/9)
    if t<31:return raw('public_phase_precision',(t-22)*15/9)
    if t<38:return raw('phase_bits_to_lut',(t-31)*5.9/7)
    return hook(t-38,True)

def overview_frame(t):
    im=overview(t)
    # Editorial crossfades link the five chapters; no intermediate algorithm states.
    for boundary in [3,13,22,31,38]:
        if boundary<=t<boundary+.28:
            return Image.blend(overview(boundary-.001),im,ease((t-boundary)/.28))
    return im

def teaser(t):
    if t<4:im=raw('public_cpu_workflow',.9+t*1.3)
    elif t<7:im=raw('public_phase_computing',2.5+(t-4)*2)
    elif t<10:im=raw('public_phase_precision',1+(t-7)*7/3)
    else:im=raw('phase_bits_to_lut',1.8+(t-10)*2)
    return Image.blend(im,raw('public_cpu_workflow',.9),ease((t-11.2)/.8)) if t>11.2 else im

def source(name,t,gif=False):
    if name=='project_overview':return teaser(t) if gif else overview_frame(t)
    fn,s,duration=renderer(name);im=fn(t,s)
    if t>duration-.8:im=Image.blend(im,fn(0,s),ease((t-duration+.8)/.8))
    return im

def export(name,preview_only=False):
    fn,s,duration=renderer(name);FOLDER.mkdir(parents=True,exist_ok=True)
    times=[.6,duration*.2,duration*.38,duration*.57,duration*.76,duration-1.1]
    if name=='project_overview':times=[1.5,6,11,18,27,36]
    for j,t in enumerate(times):source(name,t).save(FOLDER/f'{name}_{j}.png')
    poster={'public_cpu_workflow':3.3,'public_phase_computing':5.7,'public_phase_precision':4.8,
        'phase_bits_to_lut':11.4,'photo_noise_comparison':4.9,'project_overview':1.5}[name]
    source(name,poster).save(FOLDER/f'{name}_poster.png')
    source(name,poster).resize((720,405),Image.Resampling.LANCZOS).save(FOLDER/f'{name}_720.png')
    if preview_only:return
    target=ROOT/'animations';video=target/'video';video.mkdir(exist_ok=True)
    with imageio.get_writer(str(video/f'{name}.mp4'),fps=FPS,codec='libx264',quality=None,
        ffmpeg_params=['-crf','18','-movflags','+faststart'],macro_block_size=1) as writer:
        for i in range(round(duration*FPS)):writer.append_data(np.asarray(source(name,i/FPS)))
    gd=12 if name=='project_overview' else duration
    canvas=Image.new('RGB',(960,540*10))
    for j,t in enumerate(np.linspace(0,gd-.84,10)):
        canvas.paste(source(name,float(t),gif=True).resize((960,540),Image.Resampling.LANCZOS),(0,j*540))
    palette=canvas.quantize(colors=248 if name in ['phase_bits_to_lut','project_overview'] else 256,method=Image.Quantize.MEDIANCUT)
    if name in ['phase_bits_to_lut','project_overview']:
        # Preserve semantic carry/warning colors even when sample frames omit them.
        reserved=[BG,FG,BLUE,CYAN,GREEN,AMBER,RED,LINE]
        rgb=[int(c[i:i+2],16) for c in reserved for i in [1,3,5]]
        palette.putpalette(palette.getpalette()[:248*3]+rgb)
    frames=[source(name,i/GIF_FPS,gif=True).resize((960,540),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for i in range(round(gd*GIF_FPS))]
    frames[0].save(target/f'{name}.gif',save_all=True,append_images=frames[1:],duration=40,loop=0,optimize=True,disposal=1)
    print(f'Added {name}: MP4 {duration:g}s/24fps; GIF {gd:g}s/25fps',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=NAMES);p.add_argument('--preview-only',action='store_true');a=p.parse_args()
    for name in [a.only] if a.only else NAMES:export(name,a.preview_only)

if __name__=='__main__':main()
