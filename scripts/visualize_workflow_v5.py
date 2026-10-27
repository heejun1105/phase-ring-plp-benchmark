"""Public-facing work queues replay the retained native CPU medians, not a chip trace."""
import math
from PIL import ImageDraw
from scripts.visual_style import *
from scripts.visualize_v4 import NativeStudy,METHODS

DURATION=16.0
UNITS=200
PER_TILE=50_000

def race_state(t,s=None):
    """One common linear replay clock per baseline; no per-lane time rescaling."""
    s=s or NativeStudy()
    optimized=t>=7.6
    baseline='FP32 summed-angle trig' if optimized else METHODS[0]
    start,span=(8.2,5.0) if optimized else (0.9,6.0)
    elapsed=max(0,min(1,(t-start)/span))*s.ms(baseline)
    methods=[baseline,*METHODS[1:]]
    return baseline,elapsed,{m:min(1,elapsed/s.ms(m)) for m in methods}

def _tiles(d,x,y,count,color,finished=False):
    for k in range(UNITS):
        if (k<count) != finished:continue
        xx=x+(k%25)*18;yy=y+(k//25)*11
        d.rounded_rectangle((xx,yy,xx+12,yy+7),radius=2,fill=color)

def _stream(d,left,right,y,t,speed,color,active):
    d.line((left,y,right,y),fill=LINE,width=5)
    if not active:return
    for j in range(7):
        p=(t*speed+j/7)%1
        x=left+(right-left)*p
        d.line((x-22,y,x-5,y),fill=color,width=3)
        d.rounded_rectangle((x-5,y-7,x+7,y+7),radius=3,fill=color)

def workflow(t,study=None):
    s=study or NativeStudy();baseline,elapsed,progress=race_state(t,s)
    optimized=baseline=='FP32 summed-angle trig';summary=t>=13.8
    im,d=scene('A / SAME INPUT / 10,000,000 PHASE PRODUCTS',
        'Watch the waiting work become finished work.' if not summary else 'The faster path also uses an approximation.',
        ('Optimized baseline: add angles, then sin / cos' if optimized else 'Four-trig baseline: build two phasors, then multiply')+' | Measured CPU medians, stretched in time')
    txt(d,(100,198),'WAITING',27,MUTED,True)
    txt(d,(825,198),'PROCESS',27,MUTED,True)
    txt(d,(1280,198),'FINISHED',27,MUTED,True)
    for j,(m,label,color) in enumerate(zip(progress,
        ['Optimized angle-sum' if optimized else 'Conventional / four-trig','Phase-Ring Z1024','Phase-Ring Z2048'],[BLUE,CYAN,GREEN])):
        top=235+j*232;p=progress[m];done=int(p*UNITS)
        card(d,(64,top,1856,top+214),color if p>=1 else LINE)
        txt(d,(90,top+5),label,38,color,True,width=1070)
        txt(d,(1280,top+3),f'{s.ms(m):.2f} ms',43,color,True)
        _tiles(d,100,top+67,done,color,False)
        _tiles(d,1280,top+67,done,color,True)
        active=0<p<1
        _stream(d,560,790,top+128,t,2.5*s.ms(baseline)/s.ms(m),color,active)
        _stream(d,1070,1260,top+128,t,2.5*s.ms(baseline)/s.ms(m),color,active)
        card(d,(790,top+61,1070,top+190),color,12,fill='#16314a' if active else PANEL)
        if p>=1:
            d.line((875,top+126,902,top+154,965,top+91),fill=color,width=9)
            txt(d,(1510,top+172),'DONE',30,color,True)
        else:
            txt(d,(813,top+83),'ANGLE + TRIG' if j==0 and optimized else ('TRIG + PRODUCT' if j==0 else 'ADD + LOOKUP'),29,color,True,width=235)
            if active:
                for k in range(5):
                    xx=810+k*49;hh=15+30*(.5+.5*math.sin(t*13+k))
                    d.rectangle((xx,top+176-hh,xx+27,top+176),fill=color)
        txt(d,(91,top+175),f'{int(s.n*p+1e-7):,} / 10,000,000 completed',27,FG,True)
    if summary:
        txt(d,(95,950),f'vs four-trig: {s.ratio(METHODS[1]):.2f}x / {s.ratio(METHODS[2]):.2f}x',34,CYAN,True)
        txt(d,(975,950),f'vs angle-sum: {s.ms(baseline)/s.ms(METHODS[1]):.2f}x / {s.ms(baseline)/s.ms(METHODS[2]):.2f}x',34,CYAN,True)
    else:
        txt(d,(95,950),'Each tile represents 50,000 products.',30,MUTED)
        txt(d,(1120,950),f'Shared replay: {elapsed:.1f} ms',32,FG,True)
    footer(d,'Illustrative data motion; uniform progress replay from measured CPU medians. This is not a live execution trace.',
        'Same double-angle inputs and complex<float> outputs. Q15 is approximate. No PIM hardware speedup was measured.',color=AMBER)
    return im
