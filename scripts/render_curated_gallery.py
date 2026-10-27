"""Export four new editorial cuts; all original animation files stay untouched."""
import argparse
from functools import lru_cache
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image

from scripts import curated_video_edits as edits
from scripts.visual_style import BG, FG, BLUE, CYAN, GREEN, AMBER, RED, LINE, ease

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'results/curated_gallery'
ITEMS = edits.CUTS
FPS = 24
GIF_FPS = 25


@lru_cache(maxsize=4)
def renderer(name):
    item = ITEMS[name]
    return getattr(edits, item['function']), float(item['duration']), float(item['poster'])


def raw(name, t):
    fn, duration, _ = renderer(name)
    return fn(max(0.0, min(float(t), duration - 1e-6))).convert('RGB')


def source(name, t):
    """Exact decoded-media reference: 1080p RGB with one final loop dissolve."""
    _, duration, _ = renderer(name)
    t = max(0.0, min(float(t), duration - 1e-6))
    im = raw(name, t)
    if t > duration - 0.8:
        im = Image.blend(im, raw(name, 0.0), ease((t - duration + 0.8) / 0.8))
    return im


def _write_preview(name):
    _, duration, poster = renderer(name)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for j, t in enumerate(ITEMS[name]['preview_times']):
        source(name, t).save(FOLDER / f'{name}_{j}.png')
    source(name, poster).save(FOLDER / f'{name}_poster.png')
    source(name, poster).resize((720, 405), Image.Resampling.LANCZOS).save(FOLDER / f'{name}_720.png')
    metadata = {'name': name, **ITEMS[name], 'mp4_fps': FPS, 'gif_fps': GIF_FPS,
                'mp4_frames': round(duration * FPS), 'gif_sample_frames': round(duration * GIF_FPS)}
    (FOLDER / f'{name}_edit.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')


def export(name, preview_only=False):
    """Only the four curated_* names are accepted; prior filenames are excluded."""
    _, duration, _ = renderer(name)
    _write_preview(name)
    if preview_only:
        return
    target = ROOT / 'animations'
    video = target / 'video'
    video.mkdir(exist_ok=True, parents=True)
    with imageio.get_writer(str(video / f'{name}.mp4'), fps=FPS, codec='libx264', quality=None,
            ffmpeg_params=['-crf', '18', '-movflags', '+faststart'], macro_block_size=1) as writer:
        for i in range(round(duration * FPS)):
            writer.append_data(np.asarray(source(name, i / FPS)))
    canvas = Image.new('RGB', (960, 540 * 10))
    for j, t in enumerate(np.linspace(0, duration - 0.84, 10)):
        canvas.paste(source(name, float(t)).resize((960, 540), Image.Resampling.LANCZOS), (0, j * 540))
    palette = canvas.quantize(colors=248, method=Image.Quantize.MEDIANCUT)
    # Reserve warning/carry/reference colors even when palette sample scenes omit them.
    reserved = [BG, FG, BLUE, CYAN, GREEN, AMBER, RED, LINE]
    palette.putpalette(palette.getpalette()[:248 * 3] +
                       [int(c[i:i + 2], 16) for c in reserved for i in (1, 3, 5)])
    frames = [source(name, i / GIF_FPS).resize((960, 540), Image.Resampling.LANCZOS)
              .quantize(palette=palette, dither=Image.Dither.NONE)
              for i in range(round(duration * GIF_FPS))]
    frames[0].save(target / f'{name}.gif', save_all=True, append_images=frames[1:],
                   duration=40, loop=0, optimize=True, disposal=1)
    print(f'Added {name}: {duration:g}s, MP4 24fps / GIF 25fps; original media preserved.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=list(ITEMS))
    parser.add_argument('--preview-only', action='store_true')
    args = parser.parse_args()
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER / 'edit_manifest.json').write_text(json.dumps(ITEMS, indent=2), encoding='utf-8')
    for name in [args.only] if args.only else ITEMS:
        export(name, args.preview_only)


if __name__ == '__main__':
    main()
