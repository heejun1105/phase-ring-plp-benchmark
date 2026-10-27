"""Render full conventional baselines and keep the original videos as visible archives."""
from pathlib import Path
from functools import lru_cache
import argparse,importlib,json
import numpy as np
from PIL import Image
import imageio.v2 as imageio
from scripts.visual_style import BG,FG,BLUE,CYAN,GREEN,AMBER,RED,LINE,ease
from scripts.media_history import archive_originals

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'results/conventional_comparisons'
ITEMS={
 'phase_precision_comparison':'baseline_precision_overlay',
 'public_phase_precision':'baseline_precision_stairs',
 'angle_snap_targets':'baseline_precision_targets',
 'fp32_and_phase_outputs':'baseline_wave_outputs',
}

@lru_cache(maxsize=4)
def renderer(name):
    m=importlib.import_module('scripts.'+ITEMS[name])
    return m.frame,float(m.DURATION),float(getattr(m,'POSTER_TIME',m.DURATION*.35))

def source(name,t):
    fn,duration,_=renderer(name);t=max(0,min(float(t),duration-.001));im=fn(t)
    return Image.blend(im,fn(0),ease((t-duration+.8)/.8)) if t>duration-.8 else im

def export(name,preview_only=False):
    _,duration,poster=renderer(name);FOLDER.mkdir(parents=True,exist_ok=True)
    for j,t in enumerate([.5,2.8,5.3,7.7,duration-3.0,duration-1.1]):source(name,t).save(FOLDER/f'{name}_{j}.png')
    source(name,poster).save(FOLDER/f'{name}_poster.png')
    source(name,poster).resize((720,405),Image.Resampling.LANCZOS).save(FOLDER/f'{name}_720.png')
    if preview_only:return
    archive=archive_originals()
    (FOLDER/'original_media.json').write_text(json.dumps(archive,indent=2),encoding='utf-8')
    with imageio.get_writer(str(ROOT/f'animations/video/{name}.mp4'),fps=24,codec='libx264',quality=None,
        ffmpeg_params=['-crf','18','-movflags','+faststart'],macro_block_size=1) as writer:
        for i in range(round(duration*24)):writer.append_data(np.asarray(source(name,i/24)))
    canvas=Image.new('RGB',(960,540*10))
    for j,t in enumerate(np.linspace(0,duration-.84,10)):
        canvas.paste(source(name,float(t)).resize((960,540),Image.Resampling.LANCZOS),(0,j*540))
    palette=canvas.quantize(colors=248,method=Image.Quantize.MEDIANCUT)
    palette.putpalette(palette.getpalette()[:248*3]+[int(c[i:i+2],16) for c in [BG,FG,BLUE,CYAN,GREEN,AMBER,RED,LINE] for i in [1,3,5]])
    frames=[source(name,i/25).resize((960,540),Image.Resampling.LANCZOS).quantize(palette=palette,dither=Image.Dither.NONE) for i in range(round(duration*25))]
    frames[0].save(ROOT/f'animations/{name}.gif',save_all=True,append_images=frames[1:],duration=40,loop=0,optimize=True,disposal=1)
    print(f'Updated {name}: Conventional FP32 + Z1024 + Z2048; {duration:g}s',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=list(ITEMS));p.add_argument('--preview-only',action='store_true');a=p.parse_args()
    for name in [a.only] if a.only else ITEMS:export(name,a.preview_only)

if __name__=='__main__':main()
