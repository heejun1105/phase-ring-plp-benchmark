"""Render 12-second technical animations from measured CSV data and real outputs."""
from pathlib import Path
import csv, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

ROOT=Path(__file__).resolve().parents[1]
W,H=1920,1080
BG='#09111e';PANEL='#101d30';BORDER='#25374c';TEXT='#eaf2fc';MUTED='#91a6be';BLUE='#60a5fa';TEAL='#40dfbe';AMBER='#f2c36c'

def font(size,bold=False):
    paths=[Path('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf')),
           Path('/usr/share/fonts/truetype/dejavu/'+('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'))]
    for p in paths:
        if p.exists():return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)

def label(d,xy,text,size=26,fill=TEXT,bold=False):d.text(xy,text,font=font(size,bold),fill=fill)

def panel(d,box):d.rounded_rectangle(box,radius=22,fill=PANEL,outline=BORDER,width=2)

def base(kicker,title,subtitle):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    for x in range(0,W,60):d.line((x,0,x,H),fill='#0c1726')
    for y in range(0,H,60):d.line((0,y,W,y),fill='#0c1726')
    label(d,(68,34),kicker,22,TEAL,True);label(d,(64,76),title,48,TEXT,True)
    label(d,(68,144),subtitle,25,MUTED)
    return im,d

def load(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def data():
    bench=load('benchmark.csv');acc=load('accuracy.csv');noise=load('noise_benchmark.csv')
    size=max(int(r['n']) for r in bench)
    b={r['method']:r for r in bench if int(r['n'])==size}
    a={r['method']:r for r in acc if int(r['n'])==size}
    n={r['method']:r for r in noise if r['image']=='camera' and float(r['sigma'])==0.06 and int(r['seed'])==20261020}
    return b,a,n

def flow(d,x,y,width,names,color,t):
    count=len(names);bw=(width-44*(count-1))/count
    for j,name in enumerate(names):
        xx=x+j*(bw+44)
        d.rounded_rectangle((xx,y,xx+bw,y+82),radius=12,fill='#14273e',outline=color,width=2)
        label(d,(xx+18,y+23),name,24,TEXT,True)
        if j<count-1:
            end=xx+bw;d.line((end+3,y+41,end+39,y+41),fill=color,width=3)
            d.polygon([(end+39,y+41),(end+29,y+34),(end+29,y+48)],fill=color)
    position=(t/2)%1
    xx=x+width*position
    d.ellipse((xx-7,y+96,xx+7,y+110),fill=color)

def progress(d,x,y,width,p,color):
    d.rounded_rectangle((x,y,x+width,y+17),radius=8,fill='#24344b')
    if p>0:d.rounded_rectangle((x,y,x+max(17,width*min(p,1)),y+17),radius=8,fill=color)

def compute_frame(t,b,a,n):
    im,d=base('DEMO 01  /  CPU MEASUREMENTS','One phase product. Three execution paths.',
              f"{int(b['FP32 kernel']['n']):,} unit phasors  |  NumPy on the same CPU  |  median of {b['FP32 kernel']['repeats']} runs after 2 warm-ups")
    for x in [64,980]:panel(d,(x,202,x+876,804))
    label(d,(94,228),'Conventional FP32 Computing',34,BLUE,True)
    label(d,(1010,228),'Phase-Ring PIM',34,TEAL,True)
    label(d,(1010,273),'CPU software model of the proposed arithmetic',23,MUTED)
    label(d,(94,273),'complex64: FP32 real and imaginary channels',23,MUTED)
    flow(d,96,324,810,['Unit phasors','Complex multiply'],BLUE,t)
    flow(d,1012,324,810,['10/11-bit phase','Add + mask','Q15 LUT'],TEAL,t)
    label(d,(98,448),'Kernel only',24,MUTED,True)
    label(d,(1014,448),'Kernel only: integer indices as output',24,MUTED,True)
    fp=float(b['FP32 kernel']['median_ms']);z=float(b['Z1024 add']['median_ms']);z2=float(b['Z2048 add']['median_ms'])
    label(d,(98,487),f'{fp:.2f} ms',62,BLUE,True)
    label(d,(1014,489),f'Z1024  {z:.2f} ms',47,TEAL,True)
    label(d,(1014,548),f'Z2048  {z2:.2f} ms',31,TEAL)
    # The animation is a uniform time stretch of measured total durations.
    scaled_elapsed=max(0,t-2)/4*max(fp,z,z2)
    progress(d,100,582,800,min(scaled_elapsed/fp,1),BLUE)
    progress(d,1014,601,800,min(scaled_elapsed/z,1),TEAL)
    label(d,(100,620),'Measured-duration progress; uniformly slowed for display',21,MUTED)
    label(d,(1014,634),'Masking emulates hardware truncation on this CPU',21,MUTED)
    label(d,(100,686),'Angular RMSE vs. float64 reference',23,MUTED)
    label(d,(100,724),f"{float(a['FP32']['angular_rmse_rad']):.2e} rad",32,BLUE,True)
    label(d,(1014,686),'Angular RMSE: Z1024 / Z2048',23,MUTED)
    label(d,(1014,724),f"{float(a['Z1024']['angular_rmse_rad']):.5f} / {float(a['Z2048']['angular_rmse_rad']):.5f} rad",32,TEAL,True)
    panel(d,(64,826,1856,986))
    label(d,(94,845),'Equivalent complex output exposes LUT cost',28,TEXT,True)
    label(d,(94,891),f"Pre-encoded: FP32 {fp:.2f} ms  |  Z1024 + LUT {float(b['Z1024 encoded-to-complex']['median_ms']):.2f} ms",27,MUTED)
    label(d,(94,936),f"From raw angles: FP32 {float(b['FP32 end-to-end']['median_ms']):.2f} ms  |  Z1024 {float(b['Z1024 end-to-end']['median_ms']):.2f} ms  |  Z2048 {float(b['Z2048 end-to-end']['median_ms']):.2f} ms",26,TEXT)
    label(d,(70,1012),'PAPER-REPORTED ESTIMATES ONLY: 10-bit adder ~0.015 pJ/op, ~270 um^2. No silicon or PIM energy measured here.',23,AMBER)
    return im

def tile(im,d,x,y,picture,caption,width=350):
    image=picture.resize((width,width),Image.Resampling.LANCZOS)
    im.paste(image,(x,y));d.rectangle((x,y,x+width,y+width),outline=BORDER,width=2)
    label(d,(x,y+width+10),caption,23,MUTED)

def noise_frame(t,b,a,n):
    im,d=base('DEMO 02  /  EXPERIMENTAL PROTOTYPE','Noise removal, measured against a clean reference.',
              'CC0 camera photograph  |  512 x 512 grayscale  |  clipped Gaussian noise, sigma = 0.06  |  seed 20261020')
    for x in [64,980]:panel(d,(x,202,x+876,945))
    label(d,(92,226),'Conventional Noise Reduction',33,BLUE,True)
    label(d,(1008,225),'PLP-Inspired Experimental Prototype',31,TEAL,True)
    label(d,(94,273),'Bilateral filter: fixed parameters',23,MUTED)
    label(d,(1008,273),'Plane / Line / Point are independently designed substitutes',22,MUTED)
    imgs=IMAGE_CACHE
    baseline=float(n['Bilateral']['median_ms']);proto=float(n['PLP-Inspired Experimental Prototype']['median_ms'])
    elapsed=max(0,t-1.5)/3.8*max(baseline,proto)
    p0=min(elapsed/baseline,1);p1=min(elapsed/proto,1)
    # Whole-frame wipe reveals stored results; it is not an instrumented pixel trace.
    def wipe(final,p):
        image=imgs['noisy'].copy();cut=int(512*p)
        if cut:image.paste(final.crop((0,0,cut,512)),(0,0))
        return image
    tile(im,d,94,322,wipe(imgs['bilateral'],p0),'Output reveal (illustrative)',350)
    tile(im,d,1008,322,wipe(imgs['prototype'],p1),'Output reveal (illustrative)',350)
    crop=(260,100,388,228)
    for x,name,color in [(474,'bilateral',BLUE),(1388,'prototype',TEAL)]:
        z=imgs[name if (p0 if name=='bilateral' else p1)>=1 else 'noisy'].crop(crop).resize((350,350),Image.Resampling.NEAREST)
        im.paste(z,(x,322));d.rectangle((x,322,x+350,672),outline=color,width=2)
        label(d,(x,682),'128 x 128 crop: camera detail',21,MUTED)
    for x,name,color,p in [(94,'Bilateral',BLUE,p0),(1008,'PLP-Inspired Experimental Prototype',TEAL,p1)]:
        r=n[name];progress(d,x,728,730,p,color)
        label(d,(x,764),f"PSNR  {float(r['psnr_db']):.2f} dB    SSIM  {float(r['ssim']):.4f}",32,color,True)
        label(d,(x,813),f"Median  {float(r['median_ms']):.2f} ms    Edge score  {float(r['edge_preservation']):.3f}",29,TEXT)
    label(d,(94,868),'Measured CPU time; no hardware energy inference',22,MUTED)
    label(d,(1008,868),'Local Wiener -> guided filter -> 10-bit quantization',23,MUTED)
    stage=min(2,int(p1*3))
    for j,text in enumerate(['PLANE','LINE','POINT']):
        xx=1008+j*248
        label(d,(xx,909),text,21,TEAL if stage==j else MUTED,True)
    label(d,(70,968),'The prototype is not a validated implementation of the PLP equations. No prime-orbit erasure or sub-pixel recovery is claimed.',24,AMBER)
    label(d,(70,1013),'Sweep: 2 images x 3 noise levels x 3 seeds. Zooms and metrics are real outputs; reveal motion is illustrative.',23,MUTED)
    return im

def noise_figure():
    im,d=base('BENCHMARK CONTACT SHEET','Fine structures: real filter outputs','Original text / edge chart, sigma = 0.06, seed 20261020. All images share the same display mapping.')
    folder=ROOT/'results/images'
    names=[('clean','Clean reference'),('noisy','Noisy input'),('gaussian','Gaussian'),('bilateral','Bilateral'),('median','Median'),('prototype','PLP-inspired prototype')]
    for i,(key,title) in enumerate(names):
        x=64+(i%3)*610;y=210+(i//3)*410
        src=Image.open(folder/f'text_chart_{key}.png').convert('RGB')
        crop=src.crop((20,30,492,185)).resize((560,184))
        im.paste(crop,(x,y));label(d,(x,y+200),title,29,TEAL if key=='prototype' else TEXT,True)
        if key in ['clean','noisy']:desc='Reference only' if key=='clean' else 'Identical input to all filters'
        else:desc='Measured output; fixed parameters'
        label(d,(x,y+245),desc,23,MUTED)
        dots=src.crop((20,360,492,430)).resize((560,83))
        im.paste(dots,(x,y+288))
    return im

def export(name,frame_fn,b,a,n):
    target=ROOT/'animations';(target/'video').mkdir(exist_ok=True,parents=True)
    figs=ROOT/'results/figures';figs.mkdir(exist_ok=True,parents=True)
    first=frame_fn(0,b,a,n)
    def frame_at(t):
        frame=frame_fn(t,b,a,n)
        return Image.blend(frame,first,min(1,(t-11.2)/0.8)) if t>11.2 else frame
    for t in [0,3,6,10]:frame_at(t).save(figs/f'{name}_{t:02d}s.png')
    writer=imageio.get_writer(str(target/'video'/f'{name}.mp4'),fps=24,codec='libx264',quality=None,
        ffmpeg_params=['-crf','18','-movflags','+faststart'],macro_block_size=1)
    try:
        for i in range(288):writer.append_data(np.asarray(frame_at(i/24)))
    finally:writer.close()
    # A single global palette avoids frame-to-frame quantization flicker.
    palette_source=Image.new('RGB',(960,540*3))
    for i,t in enumerate([0,4,9]):palette_source.paste(frame_at(t).resize((960,540)),(0,540*i))
    palette=palette_source.quantize(colors=256)
    frames=[]
    for i in range(120):
        f=frame_at(i/10).resize((960,540),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE)
        frames.append(f)
    frames[0].save(target/f'{name}.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=True,disposal=2)
    print(f'Rendered {name}: GIF and 1080p MP4',flush=True)

IMAGE_CACHE={}
def main():
    b,a,n=data();folder=ROOT/'results/images'
    for key in ['noisy','bilateral','prototype','plane','line','point','clean']:
        IMAGE_CACHE[key]=Image.open(folder/f'camera_{key}.png').convert('RGB')
    export('computing_comparison',compute_frame,b,a,n)
    export('noise_comparison',noise_frame,b,a,n)
    noise_figure().save(ROOT/'results/figures/text_detail_comparison.png')

if __name__=='__main__':main()
