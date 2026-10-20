"""Image-first revision using the unchanged, recorded 54-case noise study.

The wipe reveals an already computed output. It is an editorial comparison,
not a denoising iteration, convergence trace, or real-time execution recording.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.visual_style import (
    AMBER, BLUE, CYAN, FG, LINE, MUTED, RED, card, ease, scene, txt,
)

ROOT = Path(__file__).resolve().parents[1]
DURATION = 15.0
DISCLAIMER = (
    'PLP-Inspired Experimental Prototype — Not a Validated Implementation '
    'of the Original PLP Equations'
)
PREVIEW_TIMES = [0.0, 2.5, 5.5, 6.7, 7.7, 8.7, 9.7, 11.2, 13.8]
POSTER_TIME = 5.5


@lru_cache(maxsize=1)
def _line_grid():
    return dict(np.load(ROOT / 'results/visual_study/line_grid_outputs.npz'))


def _arrays(s, name):
    return _line_grid() if name == 'line_grid' else s.images[name]


def _footer(d):
    # Preserve the full caveat at a readable size rather than shrinking one line.
    txt(d, (65, 997), 'PLP-Inspired Experimental Prototype —', 28, AMBER, True)
    txt(d, (65, 1036),
        'Not a Validated Implementation of the Original PLP Equations', 27, AMBER)


def _roi(name, progress=1.0):
    """One aspect-2 crop, shared by every method and reference on a frame."""
    if name == 'microtext':
        # The 12/16-pixel labels are enlarged before inspecting larger shapes.
        width = 480.0 - 64.0 * ease(progress)
        cx, cy = 214.0, 122.0
        left = max(0.0, cx - width / 2)
        top = max(0.0, cy - width / 4)
        return left, top, left + width, top + width / 2
    return {
        'line_grid': (88, 38, 472, 230),
        'geometry': (26, 70, 506, 310),
        'dark_texture': (0, 165, 480, 405),
    }[name]


def _picture(array, roi, size, gain=1.0):
    # The same clipped linear display transform is used for all compared arrays.
    image = Image.fromarray(np.rint(np.clip(array * gain, 0, 1) * 255).astype(np.uint8))
    return image.convert('RGB').crop(roi).resize(size, Image.Resampling.LANCZOS)


def _reference(im, d, arrays, roi, gain=1.0, x=64, y=738, width=374):
    card(d, (x, y, x + width, 972), FG)
    txt(d, (x + 16, y + 8), 'CLEAN REFERENCE', 28, FG, True, width=width - 25)
    im.paste(_picture(arrays['clean'], roi, (width - 32, (width - 32) // 2), gain),
             (x + 16, y + 53))


def _metric_row(d, r, output_name, color):
    card(d, (462, 738, 1856, 972), color)
    txt(d, (488, 747), output_name + ' / THIS RECORDED FULL IMAGE', 29, color, True)
    labels = ['PSNR', 'SSIM', 'EDGE SCORE', 'MEDIAN CPU TIME']
    values = [f"{float(r['psnr_db']):.2f} dB", f"{float(r['ssim']):.4f}",
              f"{float(r['edge_preservation']):.3f}", f"{float(r['median_ms']):.2f} ms"]
    for x, label, value in zip([488, 826, 1134, 1455], labels, values):
        txt(d, (x, 801), label, 25, MUTED, True)
        txt(d, (x, 839), value, 49, color, True, width=325)
    txt(d, (488, 929), 'Metrics use the full unscaled image; shared crops are for inspection.', 25, MUTED)


def _comparison(t, s, name, method, local, duration, tour=False):
    arrays = _arrays(s, name)
    gain = 1 / 0.22 if name == 'dark_texture' else 1.0
    roi = _roi(name, min(1.0, local / 1.4))
    key, label, color = {
        'Bilateral': ('bilateral', 'BILATERAL', BLUE),
        'Prototype V2': ('prototype_v2', 'PLP-INSPIRED V2', CYAN),
    }[method]
    detail = {'microtext': 'SMALL TEXT / 12–22 PX', 'line_grid': 'FINE LINES / DENSE GRID',
              'geometry': 'OBJECT EDGES / CURVES + BARS', 'dark_texture': 'DARK TEXTURE / SHARED DISPLAY GAIN 1/0.22'}[name]
    im, d = scene('04 / NOISE REMOVAL / RECORDED OUTPUTS',
                  'Inspect the image before the score.',
                  detail + ' | Same crop, noise realization and magnification | sigma 0.06, seed 20261020')
    for x, title, color0 in [(64, 'NOISY INPUT', RED), (980, label, color)]:
        card(d, (x, 213, x + 876, 715), color0)
        txt(d, (x + 20, 224), title, 37, color0, True)
    noisy = _picture(arrays['noisy'], roi, (840, 420), gain)
    result = _picture(arrays[key], roi, (840, 420), gain)
    im.paste(noisy, (82, 280))
    # A completed output is uncovered by a moving editorial divider.
    # Detail-tour scenes stay fully uncovered to preserve viewing time.
    reveal = 1.0 if tour else ease((local - 0.20) / 1.20)
    cut = int(round(840 * reveal))
    im.paste(noisy, (998, 280))
    if cut:
        im.paste(result.crop((0, 0, cut, 420)), (998, 280))
    if 0 < cut < 840:
        d.line((998 + cut, 280, 998 + cut, 700), fill=FG, width=4)
        txt(d, (1010, 650), 'FILTERED', 26, CYAN, True)
        if cut < 600:
            txt(d, (1650, 650), 'NOISY', 26, RED, True)
    txt(d, (1310, 235), 'EDITORIAL WIPE / NOT ITERATIONS' if not tour else 'RECORDED OUTPUT / NO EXTRA FILTERING',
        22, MUTED, width=520)
    _reference(im, d, arrays, roi, gain)
    _metric_row(d, s.metric(name, method), label, color)
    _footer(d)
    return im


def _heatmap(t, s):
    mode = 'error' if t < 10.6 else 'edge'
    title = 'Absolute pixel error' if mode == 'error' else 'Edge magnitude error'
    scale = 0.20 if mode == 'error' else 1.0
    im, d = scene('04 / LATER EVIDENCE / COMMON COLOR SCALES',
                  title + ': lower is darker.',
                  f'Microtext | Both methods share range 0–{scale:.2f}; values above the range clip | No per-method normalization')
    roi = _roi('microtext', 1.0)
    for x, key, label, color in [(64, 'bilateral', 'BILATERAL', BLUE),
                                  (980, 'prototype_v2', 'PLP-INSPIRED V2', CYAN)]:
        card(d, (x, 213, x + 876, 715), color)
        txt(d, (x + 20, 226), label, 37, color, True)
        pic = s.maps['microtext', key, mode].crop(roi).resize((840, 420), Image.Resampling.NEAREST)
        im.paste(pic, (x + 18, 280))
    _reference(im, d, s.images['microtext'], roi)
    card(d, (462, 738, 1856, 972))
    txt(d, (484, 748), 'REMOVED INTENSITY  |  abs(noisy - output), shared range 0–0.20', 27, AMBER, True)
    for x, key, label, color in [(486, 'bilateral', 'BILATERAL', BLUE),
                                  (856, 'prototype_v2', 'V2', CYAN)]:
        pic = s.maps['microtext', key, 'removed'].crop(roi).resize((328, 164), Image.Resampling.NEAREST)
        im.paste(pic, (x, 790))
        txt(d, (x + 8, 794), label, 23, color, True)
    txt(d, (1224, 805), 'Removal can include', 31, FG, True)
    txt(d, (1224, 850), 'noise and signal.', 31, FG, True)
    txt(d, (1224, 904), 'Inspect clean text and edges.', 26, MUTED)
    _footer(d)
    return im


def _summary(s):
    im, d = scene('04 / ALL 54 CASES / UNCHANGED MEASUREMENTS',
                  'Faster Processing vs. Noise Removal Quality',
                  'Six images × three noise levels × three seeds | Means of per-case metrics and timing medians')
    # All four measured outcomes remain large enough to read in the README GIF.
    card(d, (64, 214, 1856, 878))
    txt(d, (94, 237), 'METRIC', 34, MUTED, True)
    txt(d, (742, 232), 'LEGACY V1', 44, BLUE, True)
    txt(d, (1290, 232), 'PROTOTYPE V2', 44, CYAN, True)
    rows = [('PSNR', 'psnr_db', '.2f', ' dB'), ('SSIM', 'ssim', '.4f', ''),
            ('EDGE SCORE', 'edge_preservation', '.3f', ''), ('CPU TIME', 'median_ms', '.2f', ' ms')]
    for j, (label, key, fmt, unit) in enumerate(rows):
        y = 324 + j * 129
        if j:
            d.line((94, y - 13, 1824, y - 13), fill=LINE, width=2)
        txt(d, (98, y + 15), label, 36, FG, True)
        for x, method, color in [(742, 'Legacy V1', BLUE), (1290, 'Prototype V2', CYAN)]:
            txt(d, (x, y - 4), format(s.summary[method][key], fmt) + unit, 70, color, True)
    txt(d, (94, 889), 'V2: lower CPU time and higher mean edge score; lower mean PSNR and SSIM.', 32, AMBER, True, width=1740)
    txt(d, (94, 939), 'Edge score is a custom clean-edge agreement metric. Both variants are experimental substitutes.', 27, MUTED)
    _footer(d)
    return im


def noise_v4(t, s):
    """Return one 1920×1080 frame; duration and final loop blend are exporter-owned."""
    if t < 3.1:
        return _comparison(t, s, 'microtext', 'Bilateral', t, 3.1)
    if t < 6.2:
        return _comparison(t, s, 'microtext', 'Prototype V2', t - 3.1, 3.1)
    if t < 9.2:
        slot = min(2, int((t - 6.2) / 1.0))
        name = ['line_grid', 'geometry', 'dark_texture'][slot]
        return _comparison(t, s, name, 'Prototype V2', 1.0, 1.0, tour=True)
    if t < 12.0:
        return _heatmap(t, s)
    return _summary(s)
