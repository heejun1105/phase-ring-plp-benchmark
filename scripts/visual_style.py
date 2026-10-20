"""Shared procedural scientific-animation design primitives; no physical layout claim."""
from functools import lru_cache
from pathlib import Path
import math
from PIL import Image,ImageDraw,ImageFont,ImageOps
import numpy as np

W,H=1920,1080
BG='#070e1c';PANEL='#101c30';LINE='#2b405b';FG='#edf5ff';MUTED='#a0b3ce'
BLUE='#69a8ff';CYAN='#37e2dc';GREEN='#55e6a5';AMBER='#fac66e';RED='#ff825e'

@lru_cache(maxsize=64)
def font(size,bold=False,mono=False):
    names=['consolab.ttf' if bold else 'consola.ttf'] if mono else ['segoeuib.ttf' if bold else 'segoeui.ttf']
    names+=['DejaVuSansMono.ttf' if mono else ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    for name in names:
        for p in [Path('C:/Windows/Fonts')/name,Path('/usr/share/fonts/truetype/dejavu')/name]:
            if p.exists():return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)

def txt(d,xy,text,size=32,fill=FG,bold=False,mono=False,width=None):
    text=str(text)
    if width:
        while size>22 and d.textlength(text,font=font(size,bold,mono))>width:size-=1
    d.text(xy,text,font=font(size,bold,mono),fill=fill)

def card(d,box,color=LINE,radius=22,fill=PANEL):
    d.rounded_rectangle(box,radius=radius,fill=fill,outline=color,width=2)

@lru_cache(maxsize=2)
def background():
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    for y in range(205,1020,42):
        for x in range(40,1890,42):d.ellipse((x,y,x+1,y+1),fill='#1a2940')
    d.line((64,181,1856,181),fill=LINE,width=2)
    return im

def scene(kicker,title,subtitle):
    im=background().copy();d=ImageDraw.Draw(im)
    txt(d,(64,28),kicker,25,CYAN,True)
    txt(d,(60,65),title,58,FG,True,width=1790)
    txt(d,(65,141),subtitle,28,MUTED,width=1790)
    return im,d

def footer(d,first,second=None,color=MUTED):
    txt(d,(65,998 if second else 1014),first,28,color,width=1790)
    if second:txt(d,(65,1040),second,23,MUTED,width=1790)

def ease(p):return 0.5-0.5*math.cos(math.pi*max(0,min(1,p)))

def glow(d,xy,r,color):
    x,y=xy
    # Concentric solid strokes keep GIF palettes stable without artificial bloom.
    for k,c in [(r+13,LINE),(r+7,color),(r,FG)]:d.ellipse((x-k,y-k,x+k,y+k),fill=c)

def wire(d,points,color,progress=None):
    d.line(points,fill=LINE,width=10,joint='curve');d.line(points,fill=color,width=3,joint='curve')
    if progress is not None:
        lengths=[math.dist(points[i],points[i+1]) for i in range(len(points)-1)];target=sum(lengths)*(progress%1)
        for i,length in enumerate(lengths):
            if target<=length:
                p=target/length;xy=(points[i][0]*(1-p)+points[i+1][0]*p,points[i][1]*(1-p)+points[i+1][1]*p)
                glow(d,xy,5,color);break
            target-=length

def chip(d,x,y,w,h,title,color,active=False):
    # Beveled package, pins and routing are a conceptual illustration, not a die layout.
    d.polygon([(x,y+h),(x+w,y+h),(x+w+14,y+h-14),(x+w+14,y-4),(x+w,y+10)],fill='#050a12')
    d.rounded_rectangle((x,y,x+w,y+h),radius=10,fill='#183047' if active else '#101c2d',outline=color if active else LINE,width=4 if active else 2)
    for j in range(12,w-12,22):
        d.line((x+j,y-8,x+j,y),fill=color if active else LINE,width=4)
        d.line((x+j,y+h,x+j,y+h+8),fill=color if active else LINE,width=4)
    txt(d,(x+16,y+14),title,28,color if active else MUTED,True,width=w-24)
    for yy in range(int(y+54),int(y+h-8),12):d.line((x+18,yy,x+w-18,yy),fill='#294159',width=1)

def curve(d,points,color,width=3):
    points=list(points)
    if len(points)>1:d.line([(float(x),float(y)) for x,y in points],fill=color,width=width,joint='curve')

def waveform(d,box,phase,color,travel=0):
    x,y,w,h=box
    d.line((x,y+h/2,x+w,y+h/2),fill=LINE,width=1)
    xx=np.linspace(0,w,180);yy=y+h/2-np.sin(xx/w*math.tau+phase+travel)*h*0.38
    curve(d,zip(x+xx,yy),color,4)

def paste_gray(im,array,box,roi=None):
    x,y,w,h=box
    picture=Image.fromarray(np.uint8(np.rint(np.clip(array,0,1)*255))).convert('RGB')
    if roi:picture=picture.crop(roi)
    im.paste(ImageOps.fit(picture,(w,h),method=Image.Resampling.LANCZOS),(x,y))
