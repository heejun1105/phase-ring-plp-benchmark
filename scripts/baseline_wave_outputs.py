"""Conventional FP32 and both phase-ring outputs on identical visible scales.

The wave example is distinct from the retained native accuracy sample. A common
zoom enlarges genuine differences; it never adds errors or encodes CPU latency.
Only this new renderer and requested preview files are written.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw

from scripts.visual_style import (
    BG, PANEL, LINE, FG, MUTED, BLUE, CYAN, GREEN, AMBER,
    background, card, curve, ease, font, glow, txt,
)
from scripts.conventional_reference import product, native_metrics, METRIC_METHODS

ROOT = Path(__file__).resolve().parents[1]
DURATION = 14.0
POSTER_TIME = 7.3
METHODS = (
    ('fp32', 'Conventional FP32', 'Optimized angle-sum', BLUE),
    ('z1024', 'Z1024 / Q15', 'Phase-ring lookup', CYAN),
    ('z2048', 'Z2048 / Q15', 'Phase-ring lookup', GREEN),
)


@lru_cache(maxsize=1)
def example():
    """The same two inputs enter every route, with separate input quantization."""
    return product(.29, .29)


def _center(d, x, y, text, size, color=FG, bold=False, mono=False):
    f = font(size, bold, mono)
    d.text((x-d.textlength(str(text), font=f)/2, y), str(text), fill=color, font=f)


def _base(title, subtitle):
    im = background().copy()
    d = ImageDraw.Draw(im)
    txt(d, (64, 36), title, 63, FG, True, width=1790)
    txt(d, (67, 124), subtitle, 38, MUTED, width=1790)
    return im, d


def display_window(t):
    """One identical window for all three paths, including during the zoom."""
    zoom = ease((float(t)-3.6)/2.4)
    width = math.exp((1-zoom)*math.log(360.0)+zoom*math.log(.85))
    center = -.275*zoom
    half_height = math.exp((1-zoom)*math.log(1.05)+zoom*math.log(.015))
    lo, hi = center-width/2, center+width/2
    # Keep the entire actual curve inside the common viewport while x and y
    # scales change. No method gets its own normalization or clipped waveform.
    scan = np.linspace(lo, hi, 160)
    largest = max(float(np.max(np.abs(wave_values(key, scan)))) for key, *_ in METHODS)
    half_height = max(half_height, largest*1.05)
    return lo, hi, -half_height, half_height, zoom


def wave_values(key, angles_deg):
    """Actual complex output supplies both amplitude and phase, without scaling."""
    return np.imag(complex(example()[key])*np.exp(1j*np.deg2rad(angles_deg)))


def _outputs(t):
    e = example()
    lo, hi, bottom, top, zoom = display_window(t)
    title = 'Same input. Three output paths.' if t < 3.6 else 'Enlarge the same zero-crossing region.'
    subtitle = 'Unit-strength inputs: 0.29° + 0.29°  •  All three methods stay visible'
    im, d = _base(title, subtitle)
    x0, width, height = 520, 1290, 131
    xs = np.linspace(lo, hi, 520)
    phase_cursor = .5-.46*math.cos(t*math.tau/4.2)
    marker_angle = lo+(hi-lo)*phase_cursor
    fp_zero = -float(e['fp32_deg'])
    for j, (key, label, description, color) in enumerate(METHODS):
        y = 231+j*224
        card(d, (64, y, 1856, y+204), color, 23)
        txt(d, (92, y+13), label, 43, color, True, width=393)
        txt(d, (92, y+70), description, 31, MUTED, width=393)
        txt(d, (92, y+119), f"{float(e[key+'_deg']):.4f}°", 47, color, True, True)
        y0 = y+17
        map_x = lambda value: x0+(np.asarray(value)-lo)/(hi-lo)*width
        map_y = lambda value: y0+(top-np.asarray(value))/(top-bottom)*height
        d.line((x0, float(map_y(0)), x0+width, float(map_y(0))), fill=LINE, width=3)
        for tick in np.linspace(lo, hi, 5):
            tx = float(map_x(tick))
            d.line((tx, y0, tx, y0+height), fill='#1b2d43', width=1)
        ys = wave_values(key, xs)
        curve(d, zip(map_x(xs), map_y(ys)), color, 7)
        # The common scan angle is the same physical point on every curve.
        mx = float(map_x(marker_angle))
        my = float(map_y(wave_values(key, marker_angle)))
        d.line((mx, y0, mx, y0+height), fill=MUTED, width=2)
        glow(d, (mx, my), 7, color)
        zero = -float(e[key+'_deg'])
        if lo <= zero <= hi:
            zx = float(map_x(zero))
            d.line((zx, y0+height+6, zx, y0+height+23), fill=color, width=4)
            d.polygon([(zx-7, y0+height+6), (zx+7, y0+height+6), (zx, y0+height-5)], fill=color)
        if zoom > .85 and key != 'fp32':
            # This bar is the actual example's angular separation from FP32,
            # mapped through the very same x-axis, not an invented disturbance.
            a, b = float(map_x(fp_zero)), float(map_x(zero))
            yy = y0+height+41
            d.line((a, yy, b, yy), fill=AMBER, width=5)
            for xx in [a, b]:
                d.line((xx, yy-6, xx, yy+6), fill=AMBER, width=3)
            gap = abs(float(e[key+'_deg'])-float(e['fp32_deg']))
            txt(d, (1131, y+149), f'Example gap: {gap:.4f}°', 30, AMBER, width=660)
        else:
            txt(d, (x0, y+158), 'Same output scale and playback angle', 30, MUTED)
    range_text = (f'Shared axes: angle {lo:+.3f}° to {hi:+.3f}°  |  '
                  f'wave value {bottom:+.4f} to {top:+.4f}')
    txt(d, (67, 940), range_text, 34, AMBER if zoom > .1 else MUTED, width=1790)
    txt(d, (67, 1004), 'Actual computed waves  •  Common magnification  •  Motion does not represent processing time',
        30, MUTED, width=1790)
    return im


def _recorded_metrics(t):
    im, d = _base('Compare measured time and error.',
        'Recorded C++ CPU run: 10 million products  •  Accuracy checked on 200,000 input pairs')
    metrics = native_metrics()
    for j, ((key, label, description, color), method) in enumerate(zip(METHODS, METRIC_METHODS)):
        row = metrics[method]
        left, width = 64+j*608, 576
        cx = left+width/2
        card(d, (left, 238, left+width, 941), color, 26)
        _center(d, cx, 277, label, 43, color, True)
        _center(d, cx, 342, description, 32, MUTED)
        _center(d, cx, 425, 'CPU median', 39, MUTED, True)
        _center(d, cx, 482, f"{float(row['median_ms']):.2f} ms", 75, color, True, True)
        _center(d, cx, 659, 'Angular RMSE', 40, MUTED, True)
        error = float(row['angular_rmse_rad'])
        number = f'{error:.2e}' if error < .00001 else f'{error:.6f}'
        _center(d, cx, 719, number+' rad', 55, FG, True, True)
        _center(d, cx, 835, f"{int(row['evaluated_samples']):,} accuracy pairs", 31, MUTED)
    txt(d, (68, 977), 'Same unit-phase task; different accuracy  •  Table setup excluded from steady-state CPU timing',
        30, MUTED, width=1780)
    txt(d, (68, 1032), 'The animated 0.29° + 0.29° pair is an illustration; RMSE comes from the separate retained audit sample.',
        27, MUTED, width=1780)
    return im


def frame(t, study=None):
    """Raw 1920x1080 RGB frame; export code owns the final loop transition."""
    t = max(0.0, min(float(t), DURATION))
    if t < 9.4:
        return _outputs(t)
    image = _recorded_metrics(t)
    if t < 9.8:
        image = Image.blend(_outputs(9.4), image, ease((t-9.4)/.4))
    return image.convert('RGB')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-dir', type=Path, default=ROOT.parents[1]/'work/baseline_wave_qa')
    args = parser.parse_args()
    args.preview_dir.mkdir(parents=True, exist_ok=True)
    for t in [1.3, 4.8, 7.3, 10.6, 12.7]:
        image = frame(t)
        image.save(args.preview_dir/f'fp32_phase_outputs_{t:04.1f}_1080.png')
        image.resize((1280, 720), Image.Resampling.LANCZOS).save(args.preview_dir/f'fp32_phase_outputs_{t:04.1f}_720.png')
    print({key: float(example()[key+'_deg']) for key, *_ in METHODS})
    print('Preview frames: '+str(args.preview_dir))


if __name__ == '__main__':
    main()
