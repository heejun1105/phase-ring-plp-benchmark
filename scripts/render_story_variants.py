"""Render additional visual explanations; every previous animation keeps its filename."""
from pathlib import Path
from functools import lru_cache
import argparse,importlib
import numpy as np
from PIL import Image
import imageio.v2 as imageio
from scripts.visual_style import BG,FG,BLUE,CYAN,GREEN,AMBER,RED,LINE,ease

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'results/story_variants'
ITEMS={
 'phase_wave_basics':('story_phase_wave','A turn on a circle becomes a wave','The moving circle hand and the marked wave point always have the same height. This introduces phase before any computation.'),
 'calculate_or_lookup':('story_calculate_lookup','Calculate again or fetch a stored answer','Two shared angles take different routes: calculate the result, or add numbered positions and select a prepared answer.'),
 'angle_snap_targets':('story_precision_targets','A moving target between stored positions','A white target moves smoothly while colored pins snap down to real stored angles. The gap is shown at one shared magnification.'),
 'wrap_and_fetch':('story_wrap_fetch','Back to the start, then read an answer','A token passes the last position on the ring and returns to the beginning. Its actual final position selects the stored sine value.'),
 'noise_detail_lens':('story_noise_lens','A moving lens over real photo details','The lens visits the same sky and tripod pixels in noisy and filtered images. The displayed filter outputs are already complete.')}

@lru_cache(maxsize=8)
def renderer(name):
    m=importlib.import_module('scripts.'+ITEMS[name][0])
    return m.frame,float(m.DURATION),float(getattr(m,'POSTER_TIME',m.DURATION*.45))

def source(name,t):
    fn,duration,_=renderer(name);t=max(0,min(duration-.001,float(t)))
    im=fn(t)
    return Image.blend(im,fn(0),ease((t-duration+.8)/.8)) if t>duration-.8 else im

def gif_interval_ms(name):return 50 if name=='noise_detail_lens' else 40

def export(name,preview_only=False,gif_only=False):
    fn,duration,poster=renderer(name);FOLDER.mkdir(parents=True,exist_ok=True)
    times=[.5,2.6,5.5,8.7,11.7,duration-1.1]
    for j,t in enumerate(times):source(name,t).save(FOLDER/f'{name}_{j}.png')
    source(name,poster).save(FOLDER/f'{name}_poster.png')
    source(name,poster).resize((720,405),Image.Resampling.LANCZOS).save(FOLDER/f'{name}_720.png')
    if preview_only:return
    target=ROOT/'animations'
    if not gif_only:
        with imageio.get_writer(str(target/'video'/f'{name}.mp4'),fps=24,codec='libx264',quality=None,
            ffmpeg_params=['-crf','18','-movflags','+faststart'],macro_block_size=1) as writer:
            for i in range(round(duration*24)):writer.append_data(np.asarray(source(name,i/24)))
    canvas=Image.new('RGB',(960,540*10))
    for j,t in enumerate(np.linspace(0,duration-.85,10)):
        canvas.paste(source(name,float(t)).resize((960,540),Image.Resampling.LANCZOS),(0,540*j))
    palette=canvas.quantize(colors=248,method=Image.Quantize.MEDIANCUT)
    colors=[BG,FG,BLUE,CYAN,GREEN,AMBER,RED,LINE]
    palette.putpalette(palette.getpalette()[:248*3]+[int(c[i:i+2],16) for c in colors for i in [1,3,5]])
    interval=gif_interval_ms(name);fps=1000/interval
    frames=[source(name,i/fps).resize((960,540),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for i in range(round(duration*fps))]
    frames[0].save(target/f'{name}.gif',save_all=True,append_images=frames[1:],duration=interval,loop=0,optimize=True,disposal=1)
    print(f'Added {name}: {duration:g}s, MP4 24fps / GIF {fps:g}fps',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=list(ITEMS));p.add_argument('--preview-only',action='store_true');p.add_argument('--gif-only',action='store_true');a=p.parse_args()
    for name in [a.only] if a.only else ITEMS:export(name,a.preview_only,a.gif_only)

if __name__=='__main__':main()
