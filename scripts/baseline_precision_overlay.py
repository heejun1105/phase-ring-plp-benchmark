"""Three actual reconstructed phase curves share one input and one magnified scale."""
import math
import numpy as np
from scripts.visual_style import *
from scripts.conventional_reference import sample,input_angle,WINDOW_DEG,native_metrics,METRIC_METHODS

DURATION=12.0
POSTER_TIME=3.0
KEYS=('fp32','z1024','z2048')
COLORS=(BLUE,CYAN,GREEN)
LABELS=('Conventional FP32','Z1024','Z2048')

def frame(t,study=None):
    if t>=8.2:return summary()
    a=float(input_angle(t));now=sample(a)
    im,d=scene('PRECISION / CONVENTIONAL FP32 + TWO PHASE SETTINGS','Compare both settings with the original calculation.',
        'Same input and complex64 output | Magnified 0–2.109375° window | Q15 reconstruction is included')
    px,py,pw,ph=140,311,1135,530
    for k in range(5):
        value=WINDOW_DEG*k/4;xx=px+pw*k/4;yy=py+ph-ph*k/4
        d.line((xx,py,xx,py+ph),fill=LINE,width=1);d.line((px,yy,px+pw,yy),fill=LINE,width=1)
        txt(d,(xx-12,py+ph+13),f'{value:.2f}',26,MUTED)
        txt(d,(px-76,yy-17),f'{value:.2f}',26,MUTED)
    angles=np.linspace(0,WINDOW_DEG,1801);values=sample(angles)
    for key,c,width in [('z1024',CYAN,8),('z2048',GREEN,5),('fp32',BLUE,6)]:
        curve(d,zip(px+angles/WINDOW_DEG*pw,py+ph-values[key+'_deg']/WINDOW_DEG*ph),c,width)
        xx=px+a/WINDOW_DEG*pw;yy=py+ph-float(now[key+'_deg'])/WINDOW_DEG*ph
        glow(d,(xx,yy),6,c)
    xx=px+a/WINDOW_DEG*pw
    d.line((xx,py,xx,py+ph),fill=FG,width=2)
    txt(d,(380,907),'Input angle (degrees)',34,MUTED)
    txt(d,(112,236),'Returned angle',31,FG,True)
    for j,(key,c,label) in enumerate(zip(KEYS,COLORS,LABELS)):
        y=224+j*238;card(d,(1355,y,1856,y+215),c)
        txt(d,(1377,y+14),label,35,c,True,width=455)
        txt(d,(1377,y+70),f"{float(now[key+'_deg']):.5f}°",49,c,True)
        gap=float(now[key+'_deg']-now['ideal_deg'])
        txt(d,(1377,y+139),f'Gap {gap:+.2e}°' if key=='fp32' else f'Gap {gap:+.5f}°',30,AMBER,True)
        txt(d,(1377,y+180),'No angle bins' if key=='fp32' else ('1,024 positions' if key=='z1024' else '2,048 positions'),27,MUTED)
    footer(d,'Blue is the conventional calculation; cyan and green are actual table-based outputs on the same scale.',
        'The demonstration inputs are separate from the recorded C++ product-accuracy dataset. No hardware timing is illustrated.',color=AMBER)
    return im

def summary():
    rows=native_metrics()
    im,d=scene('RECORDED NATIVE CPU / SAME 10 MILLION INPUT PAIRS','Faster here comes with more angle error.',
        'Primary conventional control: optimized angle sum, then sine/cosine | Two warm-ups and nine repeats')
    for j,(method,c,label) in enumerate(zip(METRIC_METHODS,COLORS,LABELS)):
        x=64+j*604;r=rows[method];card(d,(x,228,x+584,928),c)
        txt(d,(x+25,254),label,41,c,True,width=534)
        txt(d,(x+25,351),f"{float(r['median_ms']):.2f} ms",65,c,True)
        txt(d,(x+25,436),'Median processing time',31,MUTED)
        deg=math.degrees(float(r['angular_rmse_rad']))
        txt(d,(x+25,535),f'{deg:.2e}°' if j==0 else f'{deg:.4f}°',64,c,True)
        txt(d,(x+25,624),'Angular RMSE',33,MUTED)
        txt(d,(x+25,715),'More exact' if j==0 else 'Approximate lookup',38,FG,True)
        txt(d,(x+25,793),'200,000-pair accuracy check',29,MUTED)
        txt(d,(x+25,851),'Same output type; different error',26,MUTED)
    footer(d,'Conventional FP32 has nonzero floating-point error; no artificial zero or error magnification is used.',
        'Times and RMSE are retained C++ measurements. This is not general FP32 or physical PIM performance.',color=AMBER)
    return im
