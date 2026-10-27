"""Photo-first supplement, reusing every recorded image and metric unchanged.

The moving divider reveals a completed filter output. It is an editorial wipe,
not an algorithm iteration, convergence process or live execution recording.
Full camera scenes use the whole 512×512 image with one shared [0,1] mapping.
Detail scenes use identical crops/gain across clean, noisy and filtered images.
Only the dark-texture scene has shared linear display gain 1/0.22 and clipping;
all reported quality metrics use the original full unscaled arrays.
"""
import csv
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.visual_style import (
    AMBER, BLUE, CYAN, FG, GREEN, LINE, MUTED, RED,
    card, ease, scene, txt,
)

ROOT = Path(__file__).resolve().parents[1]
DURATION = 18.0
POSTER_TIME = 4.9
PREVIEW_TIMES = [0.7, 1.7, 3.1, 5.0, 6.8, 8.3, 9.8, 11.3, 13.5, 16.5]
METHODS = [('Bilateral', 'bilateral', BLUE), ('Legacy V1', 'legacy_v1', GREEN),
           ('Prototype V2', 'prototype_v2', CYAN)]


@lru_cache(maxsize=1)
def _study():
    folder = ROOT / 'results/visual_study'
    images = {name: dict(np.load(folder / f'{name}_outputs.npz'))
              for name in ['camera', 'microtext', 'line_grid', 'geometry', 'dark_texture']}
    with (ROOT / 'results/expanded_noise.csv').open(encoding='utf-8') as f:
        metrics = {(r['image'], r['method']): r for r in csv.DictReader(f)
                   if float(r['sigma']) == 0.06 and int(r['seed']) == 20261020}
    summary = json.loads((folder / 'study_summary.json').read_text())
    return images, metrics, summary


def _picture(array, size, roi=None, gain=1.0):
    image = Image.fromarray(np.rint(np.clip(array * gain, 0, 1) * 255).astype(np.uint8)).convert('RGB')
    if roi:
        image = image.crop(roi)
    return image.resize(size, Image.Resampling.LANCZOS)


def _foot(d, note='Editorial wipe reveals a completed output; it is not an algorithm iteration.'):
    txt(d, (64, 987), 'PLP-Inspired Experimental Prototype', 35, AMBER, True)
    txt(d, (64, 1037), note, 28, MUTED, width=1790)


def _divider(im, d, noisy, result, xy, progress, color):
    x, y = xy
    width, height = noisy.size
    im.paste(noisy, (x, y))
    cut = int(round(width * progress))
    if cut:
        im.paste(result.crop((0, 0, cut, height)), (x, y))
    if 0 < cut < width:
        dx = x + cut
        d.line((dx, y, dx, y + height), fill=FG, width=5)
        cy = y + height // 2
        d.ellipse((dx - 25, cy - 25, dx + 25, cy + 25), fill=FG, outline=color, width=3)
        d.line((dx - 10, cy, dx + 10, cy), fill=color, width=4)


def _full_photo(t):
    images, _, _ = _study()
    arrays = images['camera']
    slot = min(2, int(t / 2.0))
    method, key, color = METHODS[slot]
    label = ['Bilateral', 'PLP-inspired V1', 'PLP-inspired V2'][slot]
    local = t % 2.0
    im, d = scene('SUPPLEMENT / ACTUAL RECORDED PHOTO', 'Same photo. Revealed result.',
                  'A moving divider compares one noisy image with an already computed result.')
    txt(d, (140, 208), 'NOISY PHOTO', 46, RED, True)
    txt(d, (1080, 208), label.upper(), 46, color, True, width=700)
    noisy = _picture(arrays['noisy'], (700, 700))
    result = _picture(arrays[key], (700, 700))
    im.paste(noisy, (140, 270))
    _divider(im, d, noisy, result, (1080, 270), ease((local - 0.1) / 1.25), color)
    d.rectangle((138, 268, 842, 972), outline=RED, width=2)
    d.rectangle((1078, 268, 1782, 972), outline=color, width=2)
    txt(d, (864, 436), 'CLEAN', 31, FG, True)
    txt(d, (864, 477), 'REFERENCE', 26, MUTED, True)
    im.paste(_picture(arrays['clean'], (176, 176)), (870, 526))
    _foot(d)
    return im


def _details(t):
    images, _, _ = _study()
    slot = min(3, int((t - 6.0) / 1.5))
    name, label, roi = [
        ('microtext', 'SMALL TEXT', (8, 18, 424, 226)),
        ('line_grid', 'FINE LINES', (88, 38, 472, 230)),
        ('geometry', 'OBJECT EDGES', (26, 70, 506, 310)),
        ('dark_texture', 'DARK TEXTURE', (0, 165, 480, 405)),
    ][slot]
    gain = 1 / 0.22 if name == 'dark_texture' else 1.0
    arrays = images[name]
    im, d = scene('SUPPLEMENT / THE SAME DETAIL ON BOTH SIDES', 'Look closer.',
                  label + (' | Shared display gain 1/0.22' if gain != 1 else ' | Shared crop and magnification'))
    for x, title, color in [(64, 'NOISY INPUT', RED), (980, 'PLP-INSPIRED V2', CYAN)]:
        card(d, (x, 230, x + 876, 813), color)
        txt(d, (x + 22, 246), title, 47, color, True)
    noisy = _picture(arrays['noisy'], (840, 420), roi, gain)
    result = _picture(arrays['prototype_v2'], (840, 420), roi, gain)
    im.paste(noisy, (82, 331))
    # Fully computed result; the slow divider is solely an editorial comparison.
    p = ease(0.25 + (t - 6 - slot * 1.5) / 1.0)
    _divider(im, d, noisy, result, (998, 331), p, CYAN)
    im.paste(_picture(arrays['clean'], (250, 125), roi, gain), (82, 838))
    txt(d, (360, 853), 'Clean reference', 40, FG, True)
    txt(d, (360, 914), 'Noise can fall while fine detail softens.', 37, AMBER, True)
    _foot(d)
    return im


def _photo_scores():
    images, metrics, _ = _study()
    arrays = images['camera']
    im, d = scene('SUPPLEMENT / THIS PHOTO / SIGMA 0.06 / SEED 20261020', 'Different filters. Different tradeoffs.',
                  'These are measured full-image results. The preceding wipes are editorial effects.')
    for j, (method, key, color) in enumerate(METHODS):
        x = 64 + j * 604
        card(d, (x, 224, x + 584, 951), color)
        label = ['Bilateral', 'PLP-inspired V1', 'PLP-inspired V2'][j]
        txt(d, (x + 25, 245), label, 42, color, True, width=535)
        im.paste(_picture(arrays[key], (338, 338)), (x + 123, 319))
        r = metrics['camera', method]
        for y, label0, value in [
            (686, 'PSNR', f"{float(r['psnr_db']):.2f} dB"),
            (767, 'SSIM', f"{float(r['ssim']):.4f}"),
            (848, 'CPU time', f"{float(r['median_ms']):.2f} ms"),
        ]:
            txt(d, (x + 26, y + 6), label0, 33, MUTED, True)
            txt(d, (x + 230, y), value, 45, color, True, width=330)
    _foot(d, 'Full unscaled image metrics. Both PLP-inspired variants are experimental substitutes.')
    return im


def _suite_scores():
    _, _, summary = _study()
    im, d = scene('SUPPLEMENT / ALL 54 NOISY CASES', 'Quality and time do not have one winner.',
                  'Six images × three noise levels × three seeds | Means of recorded case metrics and timing medians')
    card(d, (64, 239, 1856, 881))
    xs = [590, 1045, 1500]
    for x, (method, _, color), label in zip(xs, METHODS, ['Bilateral', 'V1', 'V2']):
        txt(d, (x, 270), label, 50, color, True)
    for j, (key, label, fmt, unit) in enumerate([
        ('psnr_db', 'PSNR', '.2f', ' dB'),
        ('ssim', 'SSIM', '.4f', ''),
        ('median_ms', 'CPU time', '.2f', ' ms'),
    ]):
        y = 390 + j * 160
        txt(d, (95, y + 10), label, 48, FG, True)
        for x, (method, _, color) in zip(xs, METHODS):
            txt(d, (x, y), format(summary[method][key], fmt) + unit, 62, color, True, width=360)
        if j < 2:
            d.line((95, y + 111, 1826, y + 111), fill=LINE, width=2)
    txt(d, (95, 912), 'V2 is faster than V1 here; its mean PSNR and SSIM are lower.', 39, AMBER, True, width=1740)
    _foot(d, 'Not a validated implementation of the original PLP equations. No PIM hardware result is claimed.')
    return im


def photo_noise(t, study=None):
    """Return a 1920×1080 RGB frame using only committed recorded outputs."""
    if t < 6.0:
        return _full_photo(t)
    if t < 12.0:
        return _details(t)
    if t < 15.0:
        return _photo_scores()
    return _suite_scores()
