"""A circle-to-wave explanation of phase, with no benchmark or hardware claim."""
import math
import numpy as np
from scripts.visual_style import *

DURATION=14.0
POSTER_TIME=3.8

def phase(t):return math.tau*(.08+t/6)

def _wave(d,x,cy,w,r,angle,color,cycles=1.3):
    xx=np.linspace(0,w,500);yy=cy-r*np.sin(angle+xx/w*math.tau*cycles)
    d.line((x,cy,x+w,cy),fill=LINE,width=2)
    curve(d,zip(x+xx,yy),color,7)
    glow(d,(x,cy-r*math.sin(angle)),9,color)
    return cy-r*math.sin(angle)

def _wheel(d,cx,cy,r,angle,color):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=LINE,width=5)
    for j in range(12):
        aa=j*math.tau/12
        d.line((cx+(r-10)*math.cos(aa),cy-(r-10)*math.sin(aa),cx+(r+7)*math.cos(aa),cy-(r+7)*math.sin(aa)),fill=MUTED,width=3)
    end=(cx+r*math.cos(angle),cy-r*math.sin(angle))
    d.line((cx,cy,*end),fill=color,width=9);glow(d,end,9,color)
    return end

def frame(t,study=None):
    im,d=scene('START HERE / WHAT PHASE MEANS',
        'One turn makes one wave cycle.' if t<7 else 'Same height. A different starting point.',
        'The angle on the circle and the marked point on the wave are linked.')
    if t<7:
        a=phase(t);cx,cy,r=445,585,245
        end=_wheel(d,cx,cy,r,a,CYAN)
        y=_wave(d,870,cy,960,r,a,CYAN)
        d.line((*end,870,y),fill=AMBER,width=3)
        txt(d,(220,887),'POSITION IN THE CYCLE',40,CYAN,True)
        txt(d,(1000,887),'REPEATING WAVE',40,CYAN,True)
        txt(d,(86,216),'A full circle returns to the same place.',44,FG,True)
    else:
        a=phase(t-7);b=a+math.pi/3
        for j,(aa,c,label) in enumerate([(a,BLUE,'WAVE A'),(b,GREEN,'WAVE B')]):
            cy=430+j*365
            card(d,(64,226+j*365,1856,579+j*365),c)
            txt(d,(95,241+j*365),label,42,c,True)
            end=_wheel(d,430,cy,118,aa,c)
            yy=_wave(d,710,cy,1075,118,aa,c)
            d.line((*end,710,yy),fill=c,width=3)
    footer(d,'Phase is the position of a repeating signal within one cycle. The wave height stays the same.',
        'Mathematical illustration only. No processing speed, device latency or physical PIM result is represented.',color=AMBER)
    return im
