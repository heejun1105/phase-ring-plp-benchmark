"""A synchronized detail lens over the same recorded photograph and filter outputs."""
from functools import lru_cache
import math
import numpy as np
from PIL import Image,ImageDraw
from scripts.visual_style import *
from scripts.visualize_photo_noise import _study

DURATION=18.0
POSTER_TIME=11.5
METHODS=[('Bilateral','bilateral',BLUE),('Legacy V1','legacy_v1',GREEN),('Prototype V2','prototype_v2',CYAN)]
POINTS=[(370,110),(302,340)]

def roi(local):
    p=ease((local-1.5)/1.5)
    cx=POINTS[0][0]*(1-p)+POINTS[1][0]*p
    cy=POINTS[0][1]*(1-p)+POINTS[1][1]*p
    return (cx-48,cy-48,cx+48,cy+48)

def picture(a,size,crop=None):
    im=Image.fromarray(np.rint(np.clip(a,0,1)*255).astype(np.uint8)).convert('RGB')
    if crop:im=im.crop(crop)
    return im.resize(size,Image.Resampling.LANCZOS)

def frame(t,study=None):
    images,metrics,summary=_study();arrays=images['camera']
    if t<15:
        j=min(2,int(t/5));local=t-j*5;method,key,c=METHODS[j];crop=roi(local)
        label=['BILATERAL','PLP-INSPIRED V1','PLP-INSPIRED V2'][j]
        im,d=scene('PHOTO DETAIL / SAME RECORDED PIXELS','Follow the same patch in both images.',
            'The lens moves from sky noise to a tripod edge. The filter result was computed before the animation.')
        txt(d,(65,205),'WHERE TO LOOK',36,MUTED,True)
        txt(d,(800,205),'NOISY DETAIL',38,RED,True)
        txt(d,(1360,205),label,38,c,True,width=500)
        im.paste(picture(arrays['noisy'],(680,680)),(64,258))
        im.paste(picture(arrays['noisy'],(504,504),crop),(800,300))
        im.paste(picture(arrays[key],(504,504),crop),(1360,300))
        cx=64+(crop[0]+48)/512*680;cy=258+(crop[1]+48)/512*680;rr=48/512*680
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=AMBER,width=6)
        d.line((cx+rr,cy,760,cy,760,552,794,552),fill=AMBER,width=3)
        im.paste(picture(arrays['clean'],(160,160),crop),(558,752))
        d.rectangle((556,750,720,914),outline=FG,width=2)
        txt(d,(555,920),'CLEAN REF.',23,FG,True)
        r=metrics['camera',method]
        txt(d,(800,845),'Compare speckles and edge softness.',36,FG,True)
        txt(d,(800,909),f"{float(r['psnr_db']):.2f} dB  |  SSIM {float(r['ssim']):.4f}  |  {float(r['median_ms']):.2f} ms",36,c,True,width=1060)
    else:
        im,d=scene('PHOTO DETAIL / THREE COMPLETED RESULTS','Less noise can also mean softer detail.',
            'The same tripod crop and display scale in every panel. Metrics use the full original image.')
        crop=(190,250,382,442)
        for j,(method,key,c) in enumerate(METHODS):
            x=64+j*604;card(d,(x,232,x+584,930),c)
            txt(d,(x+24,249),['BILATERAL','PLP-INSPIRED V1','PLP-INSPIRED V2'][j],37,c,True,width=535)
            im.paste(picture(arrays[key],(536,536),crop),(x+24,322))
            r=metrics['camera',method]
            txt(d,(x+24,879),f"{float(r['psnr_db']):.2f} dB / {float(r['median_ms']):.2f} ms",32,c,True)
    footer(d,'PLP-Inspired Experimental Prototype — Not a Validated Implementation of the Original PLP Equations',
        'Shared crop, zoom and grayscale mapping. The moving lens is an illustration, not iterative filtering.',color=AMBER)
    return im
