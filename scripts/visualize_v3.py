"""Six data-driven, 12-second procedural technical animations.

Conceptual dataflow uses editorial timing. CPU race timing is a common linear
stretch of measured medians. Images, lookup values and error curves are real.
"""
from pathlib import Path
import argparse,csv,json,math
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
from scripts.visual_style import *
from src import phase_ring as ring
from src import conventional as fp

ROOT=Path(__file__).resolve().parents[1]
NAMES=['computing_architecture','benchmark_speed_race','phase_overflow_lut','noise_reduction_comparison','phase_precision_comparison','edge_preservation_comparison']
COLORS=[BLUE,CYAN,GREEN]

def read(name):
    with (ROOT/'results'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

class Study:
    def __init__(self):
        self.b={(int(r['n']),r['method']):r for r in read('benchmark.csv')}
        self.a={(int(r['n']),r['method']):r for r in read('accuracy.csv')}
        self.sizes=sorted({k[0] for k in self.b})
        self.images={};self.maps={};self.profiles={}
        self.noise=read('expanded_noise.csv');self.precision=read('precision_sweep.csv')
        self.representative=json.loads((ROOT/'results/representative_case.json').read_text())
        self.summary=json.loads((ROOT/'results/visual_study/study_summary.json').read_text())
        for name in ['microtext','geometry','camera','dark_texture']:
            folder=ROOT/'results/visual_study'
            self.images[name]=dict(np.load(folder/f'{name}_outputs.npz'))
            self.profiles[name]=Image.open(folder/f'{name}_profile.png').convert('RGB')
            for method in ['clean','noisy','bilateral','legacy_v1','prototype_v2']:
                for mode in ['error','edge','removed']:
                    self.maps[name,method,mode]=Image.open(folder/f'{name}_{method}_{mode}.png').convert('RGB')
    def metric(self,image,method):
        return next(r for r in self.noise if r['image']==image and r['method']==method and float(r['sigma'])==0.06 and int(r['seed'])==20261020)

def architecture(t,s):
    cases=[(750,400,1024),(1023,1,1024),(1500,800,2048)]
    ci=min(2,int(t/4));a,b,n=cases[ci];q=t%4;stage=min(3,int(q/0.9))
    # Quarter-bin offsets make quantization error visible without changing the index.
    aa=(a+0.25)*math.tau/n;bb=(b+0.25)*math.tau/n
    za,zb=fp.encode_pair(np.array([aa]),np.array([bb]));zf=fp.multiply(za,zb)[0]
    index=(a+b)&(n-1);lut=ring.make_lut(n);zr=ring.decode(np.array([index]),lut)[0]
    im,d=scene('01 / ARCHITECTURE / ACTUAL NUMERICAL EXAMPLE','Same phase signals. Different arithmetic.',
        'Unit-magnitude complex products | Conceptual circuit dataflow; editorial timing, not a physical layout')
    card(d,(64,207,1856,323))
    txt(d,(92,222),'SHARED INPUT',28,MUTED,True)
    txt(d,(340,223),f'a = {aa:.5f} rad',42,BLUE,True)
    txt(d,(925,223),f'b = {bb:.5f} rad',42,GREEN,True)
    waveform(d,(1330,219,480,82),aa+bb,FG,q*1.8)
    card(d,(64,350,940,963),BLUE);card(d,(980,350,1856,963),CYAN)
    txt(d,(92,365),'CONVENTIONAL FP32',34,BLUE,True)
    txt(d,(1010,365),'PHASE-RING PIM MODEL',34,CYAN,True)
    left=['COMPLEX ENCODE','FOUR REAL PRODUCTS','ADD / SUBTRACT','COMPLEX OUTPUT']
    right=['INTEGER QUANTIZE','ADD / WRAP','SRAM LUT READ','COMPLEX RESTORE']
    for side,x,color,names in [(0,106,BLUE,left),(1,1020,CYAN,right)]:
        for j,name in enumerate(names):
            y=430+j*121
            chip(d,x,y,304,87,name,color,active=j==stage)
            if j<3:wire(d,[(x+145,y+97),(x+145,y+111),(x+145,y+119)],color,q*1.5)
    # Numerical details are tied to the same shared angle pair.
    values=[(f'x = {za[0].real:+.3f}',f'    {za[0].imag:+.3f}j'),
            (f'ac = {za[0].real*zb[0].real:+.3f}',f'bd = {za[0].imag*zb[0].imag:+.3f}'),
            ('real = ac - bd','imag = ad + bc'),
            (f'{zf.real:+.5f}',f'{zf.imag:+.5f}j')]
    for j,(line1,line2) in enumerate(values):
        col=FG if stage>=j else LINE
        txt(d,(452,435+j*121),line1,33,col,True,mono=True)
        txt(d,(452,478+j*121),line2,30,col,mono=True)
    rv=[(f'q(a) = {a}',f'q(b) = {b}'),(f'{a} + {b}',f'& {n-1} -> {index}'),
        (f'address {index}',f'Q15 sin {int(lut[index,1])}'),(f'{zr.real:+.5f}',f'{zr.imag:+.5f}j')]
    for j,(line1,line2) in enumerate(rv):
        col=FG if stage>=j else LINE
        txt(d,(1365,435+j*121),line1,34,col,True,mono=True)
        txt(d,(1365,478+j*121),line2,30,col,mono=True)
    # Addressed memory cells show actual indices around the selected LUT entry.
    if stage>=2:
        start=max(0,(index//16)*16)
        for j in range(16):
            x=1370+(j%8)*49;y=901+(j//8)*18
            d.rectangle((x,y,x+42,y+10),fill=CYAN if start+j==index else '#294356')
    waveform(d,(450,898,430,50),float(np.angle(zf)),BLUE,q*1.6)
    for cx,z,color in [(827,zf,BLUE),(1764,zr,CYAN)]:
        cy=650;rr=61
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=LINE,width=2)
        if stage>=3:
            point=(cx+rr*float(z.real),cy-rr*float(z.imag))
            d.line((cx,cy,*point),fill=color,width=4);glow(d,point,5,color)
    footer(d,'Both restore complex output. Integer quantization changes accuracy; block counts do not establish speed.',
        'FP32: two float32 channels | Ring: uint16 containers + explicit 10/11-bit mask + paired signed-Q15 LUT')
    return im

def race(t,s):
    mode=0 if t<6 else 1;local=t%6
    slot=min(3,int(local/1.5));size=s.sizes[min(slot,len(s.sizes)-1)];p=(local%1.5)/1.5
    keys=['FP32 kernel','Z1024 add','Z2048 add'] if mode==0 else ['FP32 end-to-end','Z1024 end-to-end','Z2048 end-to-end']
    rows=[s.b[size,key] for key in keys];times=[float(r['median_ms']) for r in rows]
    elapsed=max(0,(p-0.12)/0.72)*max(times)
    im,d=scene('02 / SAME-CPU MEASUREMENTS / MEDIAN OF 7 RUNS','Arithmetic kernel' if mode==0 else 'Full end-to-end pipeline',
        'KERNEL: pre-encoded operands, different output types' if mode==0 else 'PIPELINE: same raw float64 angles -> complex64 output, including conversion and LUT reconstruction')
    txt(d,(72,209),f'{size:,}',76,FG,True);txt(d,(590,249),'PHASE PRODUCTS',32,MUTED,True)
    for j,ss in enumerate(s.sizes):
        x=1040+j*195;card(d,(x,221,x+177,278),CYAN if ss==size else LINE,radius=12)
        txt(d,(x+15,231),f'{ss/1e6:g}M' if ss>=1e6 else f'{ss//1000}K',30,CYAN if ss==size else MUTED,True)
    for j,(row,color) in enumerate(zip(rows,COLORS)):
        y=338+j*194;progress=min(1,elapsed/times[j]);done=int(size*progress)
        card(d,(64,y,1856,y+168),color)
        txt(d,(92,y+15),['FP32','Z1024','Z2048'][j],44,color,True)
        txt(d,(1390,y+11),f'{times[j]:.4f} ms' if times[j]<1 else f'{times[j]:.2f} ms',56,color,True,width=425)
        x=338;width=980
        d.rounded_rectangle((x,y+30,x+width,y+76),radius=20,fill='#20324b')
        if progress>0:
            end=x+max(42,width*progress);d.rounded_rectangle((x,y+30,end,y+76),radius=20,fill=color)
            glow(d,(end-18,y+53),5,color)
        txt(d,(338,y+91),f'{done:,} / {size:,}',31,FG,True)
        txt(d,(92,y+112),f"{float(row['ops_per_sec'])/1e6:.1f} M/s",29,MUTED)
        memory=int(row['traced_peak_alloc_bytes'])/2**20
        memory_text=f'{memory:.3f}' if memory<1 else f'{memory:.1f}'
        txt(d,(1020,y+100),f'Alloc. peak {memory_text} MiB',27,MUTED)
        method=['FP32','Z1024','Z2048'][j];err=float(s.a[size,method]['angular_rmse_rad'])
        txt(d,(1430,y+107),f'RMSE {err:.2e} rad',26,MUTED,width=380)
    if mode==0:
        n=max(s.sizes);f=float(s.b[n,'FP32 kernel']['median_ms']);z=float(s.b[n,'Z1024 encoded-to-complex']['median_ms'])
        footer(d,f'Common complex output at {n:,}: FP32 {f:.2f} ms | Z1024 + LUT {z:.2f} ms',
            'Progress is a linear replay of measured medians, not live profiling. Alloc. peak is incremental tracemalloc; inputs excluded.')
    else:
        footer(d,'Conversion, quantization, lookup and output restoration are included. CPU evidence only.',
            'Identical progress scale within each race. OS, cache and allocation effects remain; no chip speed or energy inference.')
    return im

def bitrow(d,x,y,value,count,color,revealed=None):
    for j in range(count):
        bit=count-1-j;xx=x+j*60
        active=revealed is None or bit<revealed
        card(d,(xx,y,xx+49,y+66),color if active else LINE,radius=7,fill='#16334a' if active and (value>>bit)&1 else '#101a29')
        txt(d,(xx+12,y+6),str((value>>bit)&1) if active else '.',38,color if active else LINE,True,mono=True)

def overflow(t,s):
    a,b,n=[(1023,1,1024),(750,400,1024),(1500,800,2048)][min(2,int(t/4))];q=t%4;bits=n.bit_length()-1
    result=(a+b)&(n-1);value=int(ring.make_lut(n)[result,1]);p=ease((q-0.35)/1.7)
    unwrapped=a+b*p;idx=int(unwrapped)%n
    im,d=scene('03 / PAPER VIII EQ. (2)-(4) + LISTING 2','Add. Drop the carry. Select a word.',
        f'Z{n} | {bits}-bit register | Bit-exact arithmetic model; conceptual SRAM addressing')
    card(d,(64,210,730,967),CYAN);card(d,(765,210,1856,967))
    cx,cy,r=397,535,218
    for j in range(64):
        angle=math.tau*j/64-math.pi/2;rr=r-13 if j%8==0 else r-6
        d.line((cx+rr*math.cos(angle),cy+rr*math.sin(angle),cx+r*math.cos(angle),cy+r*math.sin(angle)),fill=MUTED if j%8==0 else LINE,width=3)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=LINE,width=13)
    start=a/n*360-90;finish=unwrapped/n*360-90
    d.arc((cx-r,cy-r,cx+r,cy+r),start=start,end=finish+0.001,fill=CYAN,width=13)
    angle=(unwrapped%n)/n*math.tau-math.pi/2
    d.line((cx,cy,cx+(r-24)*math.cos(angle),cy+(r-24)*math.sin(angle)),fill=CYAN,width=8)
    glow(d,(cx+r*math.cos(angle),cy+r*math.sin(angle)),9,CYAN)
    txt(d,(cx-d.textlength(str(idx),font=font(75,True))/2,cy-44),str(idx),75,FG,True,width=260)
    txt(d,(cx-89,cy+42),'PHASE INDEX',26,MUTED,True)
    txt(d,(cx-12,cy-r-52),'0',34,FG,True)
    txt(d,(90,799),f'{a} + {b}',60,FG,True)
    txt(d,(90,874),f'= {result} (mod {n})',45,CYAN,True)
    labels=[('INPUT A',a,296),('INPUT B',b,403),('FULL SUM',a+b,535)]
    for label,value0,yy in labels:
        txt(d,(793,yy-44),label,26,MUTED,True)
        count=bits+1 if label=='FULL SUM' else bits
        revealed=int(p*(bits+1))+1 if label=='FULL SUM' else None
        bitrow(d,1015+(12-count)*60,yy,value0,count,CYAN if label=='FULL SUM' else BLUE,revealed)
    if q>=2.05:
        carryx=1015+(12-(bits+1))*60
        offset=int(110*ease((q-2.05)/0.55))
        txt(d,(carryx+12,541-offset),'1',40,RED,True,mono=True)
        d.line((carryx,535,carryx+49,601),fill=RED,width=5)
        txt(d,(793,640),'RETAIN',26,CYAN,True)
        bitrow(d,1015+(12-bits)*60,676,result,bits,CYAN)
    else:txt(d,(794,664),'Carry propagates from right to left',30,MUTED)
    if q>=2.7:
        txt(d,(794,782),f'LUT[{result}]',45,CYAN,True)
        txt(d,(1375,782),f'Q15 = {value}',45,FG,True,width=440)
        rows=n//32
        for j in range(n):
            xx=805+(j%32)*15;yy=855+(j//32)*(75/rows)
            d.rectangle((xx,yy,xx+11,yy+max(1,60/rows)),fill=CYAN if j==result else '#243c50')
        rr=result//32;cc=result%32
        glow(d,(805+cc*15+5,855+rr*(75/rows)),6,CYAN)
        txt(d,(1365,856),'Address -> signed sine value',28,MUTED,width=440)
        txt(d,(1365,901),'No division in the narrow RTL adder',25,MUTED,width=440)
    footer(d,'Phase addition -> register truncation -> LUT address -> output',
        'One-clock behavior is a source RTL concept; no fabricated SRAM, physical timing closure or silicon power is verified.')
    return im

def crop_zoom(p):
    zoom=1+1.6*ease(p);cx,cy=256,256;w=512/zoom
    return (cx-w/2,cy-w/2,cx+w/2,cy+w/2)

def noise(t,s):
    name='microtext';arrays=s.images[name];mode=0 if t<4 else (1 if t<8 else 2)
    keys=['clean','noisy','bilateral','prototype_v2'];labels=['CLEAN ORIGINAL','NOISY INPUT','BILATERAL','PLP-INSPIRED V2']
    modes=['INTENSITY / IDENTICAL DISPLAY SCALE','ABSOLUTE PIXEL ERROR / FIXED SCALE','EDGE MAGNITUDE ERROR / FIXED SCALE']
    im,d=scene('04 / 54 NOISY CASES / PREDECLARED MICROTEXT EXAMPLE','What is removed? What is lost?',
        modes[mode]+' | sigma 0.06, seed 20261020 | Camera-independent synthetic text fixture')
    roi=crop_zoom(min(1,(t%4)/1.7));colors=[FG,RED,BLUE,CYAN]
    for j,(key,label,color) in enumerate(zip(keys,labels,colors)):
        x=64+j*451;card(d,(x,215,x+432,955),color)
        txt(d,(x+18,232),label,32,color,True,width=400)
        if mode==0 or key=='clean':
            pic=Image.fromarray(np.rint(arrays[key]*255).astype(np.uint8)).convert('RGB')
        else:pic=s.maps[name,key,'error' if mode==1 else 'edge']
        image=pic.crop(roi).resize((396,396),Image.Resampling.NEAREST if mode else Image.Resampling.LANCZOS)
        im.paste(image,(x+18,300));d.rectangle((x+18,300,x+414,696),outline=LINE,width=2)
        # An advancing curtain exposes true heatmap values; all methods use the same x.
        scan=x+18+int(396*((t%4)/4));d.line((scan,300,scan,696),fill=FG,width=2)
        if key=='clean':
            txt(d,(x+20,730),'REFERENCE',42,FG,True);txt(d,(x+20,799),'No filtering',30,MUTED)
        else:
            method={'noisy':'Noisy input','bilateral':'Bilateral','prototype_v2':'Prototype V2'}[key];r=s.metric(name,method)
            txt(d,(x+20,720),f"{float(r['psnr_db']):.2f} dB",49,color,True)
            txt(d,(x+20,783),f"SSIM  {float(r['ssim']):.4f}",32,FG,True)
            txt(d,(x+20,831),f"{float(r['median_ms']):.2f} ms" if key!='noisy' else 'Input only',34,MUTED)
            txt(d,(x+20,887),f"Edge {float(r['edge_preservation']):.3f}",28,MUTED)
    if mode:
        scale=0.20 if mode==1 else 1.0
        txt(d,(75,966),f'Clean panel stays grayscale | Error maps: dark = lower, bright = higher | Shared range 0 to {scale:.2f}',25,AMBER)
    else:txt(d,(75,966),'Shared animated zoom. The same clean image and noise realization enter both algorithms.',25,MUTED)
    footer(d,'PLP-Inspired Experimental Prototype - Not a Validated Implementation of the Original PLP Equations',
        f"V2 minus Bilateral PSNR: {s.representative['psnr_v2_minus_bilateral']:+.3f} dB | Rank {s.representative['rank_ascending_psnr_gain']}/54, ascending gain; not a best-case selection.",color=AMBER)
    return im

def precision_legacy(t,s):
    p=(t/11.2)%1;angle=4*ease(p);row=s.precision[min(2048,int(angle/4*2048))];angle=float(row['input_deg'])
    im,d=scene('05 / QUANTIZATION / TRUE ANGLES WITH MAGNIFIED DISPLAY','Half the bin width. A different error budget.',
        'A 4-degree input window makes quantization visible | Floor quantizer, not rounding-to-nearest')
    for j,(n,color) in enumerate([(1024,CYAN),(2048,GREEN)]):
        x=64+j*916;card(d,(x,211,x+876,954),color)
        txt(d,(x+30,229),f'Z{n}',49,color,True)
        txt(d,(x+288,234),f'{360/n:.6f} deg / bin',38,FG,True,width=550)
        px,py,pw,ph=x+78,350,730,365
        d.line((px,py,px,py+ph,px+pw,py+ph),fill=MUTED,width=2)
        vals=np.linspace(0,4,1100);quant=np.floor(vals*n/360)*360/n
        actual_x=np.array([float(r['input_deg']) for r in s.precision])
        actual_fp=np.array([float(r['fp32_deg']) for r in s.precision])
        curve(d,zip(px+actual_x/4*pw,py+ph-actual_fp/4*ph),FG,3)
        curve(d,zip(px+vals/4*pw,py+ph-quant/4*ph),color,4)
        for k in range(5):
            xx=px+k/4*pw;txt(d,(xx-8,py+ph+9),str(k),24,MUTED)
        txt(d,(px+190,py+ph+45),'Input phase (degrees)',27,MUTED)
        qval=float(row[f'z{n}_deg']);xx=px+angle/4*pw;yy=py+ph-qval/4*ph;truey=py+ph-angle/4*ph
        d.line((xx,py-7,xx,py+ph),fill='#435873',width=2)
        d.line((xx,truey,xx,yy),fill=RED,width=8)
        glow(d,(xx,yy),7,color);d.ellipse((xx-5,truey-5,xx+5,truey+5),fill=FG)
        error=float(row[f'z{n}_floor_error_deg'])
        txt(d,(x+30,807),f'Input {angle:.3f} deg',35,FG,True)
        txt(d,(x+30,861),f'Floor error {error:+.5f} deg',36,RED,True,width=810)
        txt(d,(x+30,914),f"Integer index {row[f'z{n}_index']} -> paired Q15 LUT",25,MUTED)
    txt(d,(78,963),'White: complex64 phase reference   |   Colored: quantized phase   |   Orange: actual floor error',24,MUTED)
    size=max(s.sizes)
    footer(d,f"Product RMSE: FP32 {float(s.a[size,'FP32']['angular_rmse_rad']):.2e} rad | Z1024 {float(s.a[size,'Z1024']['angular_rmse_rad']):.5f} rad | Z2048 {float(s.a[size,'Z2048']['angular_rmse_rad']):.5f} rad",
        'The animated window illustrates a single-input floor quantizer. Product RMSE uses the separately recorded benchmark dataset.')
    return im

def edges(t,s):
    name=['microtext','geometry','dark_texture'][min(2,int(t/4))];arrays=s.images[name]
    im,d=scene('06 / ABLATION / LEGACY V1 VS DETAIL-LATENCY VARIANT','Removing a pass changes the tradeoff.',
        f'{name.replace("_"," ").upper()} | Same noisy input | V1: Wiener + guided + 10-bit | V2: Wiener + 10-bit')
    keys=['clean','legacy_v1','prototype_v2'];labels=['CLEAN REFERENCE','LEGACY V1','PROTOTYPE V2']
    # Crop and common gain expose actual residual/texture; no algorithm-specific sharpening.
    roi={'microtext':(15,100,495,314),'geometry':(15,30,497,245),'dark_texture':(15,130,497,345)}[name]
    for j,(key,label,color) in enumerate(zip(keys,labels,[FG,BLUE,CYAN])):
        x=64+j*604;card(d,(x,211,x+584,625),color)
        txt(d,(x+20,228),label,36,color,True)
        arr=arrays[key]
        if name=='dark_texture':arr=np.clip(arr/0.22,0,1)
        paste_gray(im,arr,(x+20,288,544,243),roi)
        profile_y=120 if name=='microtext' else (140 if name=='geometry' else 256)
        display_y=288+(profile_y-roi[1])/(roi[3]-roi[1])*243
        d.line((x+20,display_y,x+564,display_y),fill=AMBER,width=2)
        if j:
            r=s.metric(name,'Legacy V1' if j==1 else 'Prototype V2')
            txt(d,(x+20,549),f"{float(r['psnr_db']):.2f} dB | {float(r['median_ms']):.2f} ms",34,color,True)
        else:txt(d,(x+20,549),'Same crop / same display gain',28,MUTED)
    profile=s.profiles[name].resize((1150,300),Image.Resampling.LANCZOS);im.paste(profile,(64,653))
    cursor=64+100+int(((t%4)/4)*990);d.line((cursor,670,cursor,902),fill=AMBER,width=3)
    card(d,(1240,653,1856,954))
    txt(d,(1262,674),'ALL 54 CASES',31,FG,True)
    v1=s.summary['Legacy V1'];v2=s.summary['Prototype V2']
    txt(d,(1262,728),f"Edge {v1['edge_preservation']:.3f} -> {v2['edge_preservation']:.3f}",34,CYAN,True)
    txt(d,(1262,781),f"PSNR {v1['psnr_db']:.2f} -> {v2['psnr_db']:.2f} dB",33,RED,True)
    txt(d,(1262,835),f"Time {v1['median_ms']:.2f} -> {v2['median_ms']:.2f} ms",33,CYAN,True)
    txt(d,(1262,894),'Means across all image/noise cases',26,MUTED)
    footer(d,'V2 trades residual noise for lower work and less average edge attenuation. It is not a universal quality improvement.',
        'Profiles show actual clean/filtered intensities. Dark scene display gain is shared (1/0.22). Both variants are PLP-inspired substitutes.',color=AMBER)
    return im

def precision(t,s):
    from scripts.baseline_precision_overlay import frame
    return frame(t,s)

RENDERERS=dict(zip(NAMES,[architecture,race,overflow,noise,precision,edges]))

def export(name,s,preview_only=False):
    fn=RENDERERS[name];folder=ROOT/'results/visualizations';folder.mkdir(parents=True,exist_ok=True)
    frames_at=[0.4,2.2,4.6,7.5,10.3]
    for j,t in enumerate(frames_at):
        im=fn(t,s);im.save(folder/f'{name}_{j}.png')
    poster={'computing_architecture':3.4,'benchmark_speed_race':5.25,'phase_overflow_lut':3.3,
            'noise_reduction_comparison':6.0,'phase_precision_comparison':5.1,'edge_preservation_comparison':5.0}[name]
    fn(poster,s).resize((720,405),Image.Resampling.LANCZOS).save(folder/f'{name}_readme_720.png')
    if preview_only:return
    first=fn(0,s)
    def frame(t):
        im=fn(t,s)
        return Image.blend(im,first,ease((t-11.2)/0.8)) if t>11.2 else im
    target=ROOT/'animations';(target/'video').mkdir(exist_ok=True,parents=True)
    with imageio.get_writer(str(target/'video'/f'{name}.mp4'),fps=24,codec='libx264',quality=None,
        ffmpeg_params=['-crf','18','-movflags','+faststart'],macro_block_size=1) as writer:
        for j in range(288):writer.append_data(np.asarray(frame(j/24)))
    # Global palette + retained canvas allows small delta frames in README GIFs.
    palette_canvas=Image.new('RGB',(960,540*6))
    for j,t in enumerate([0,2,4,6,8,10]):palette_canvas.paste(frame(t).resize((960,540)),(0,j*540))
    palette=palette_canvas.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    gif=[frame(j*0.08).resize((960,540),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for j in range(150)]
    gif[0].save(target/f'{name}.gif',save_all=True,append_images=gif[1:],duration=80,loop=0,optimize=True,disposal=1)
    print(f'Exported {name}: 1080p H.264 + 12.5fps GIF',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=NAMES);p.add_argument('--preview-only',action='store_true');a=p.parse_args()
    s=Study()
    for name in [a.only] if a.only else NAMES:export(name,s,a.preview_only)

if __name__=='__main__':main()
