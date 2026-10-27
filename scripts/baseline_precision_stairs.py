"""Three equal precision panels with the same conventional FP32 reference.

All plotted phases are outputs from conventional_reference.sample, including
the ring's Q15 reconstruction. The white ideal guide is identical in all panels.
The FP32 deviation is not visually exaggerated when it is below a display pixel.
The final cards use the retained optimized summed-angle native CPU experiment.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw

from scripts.visual_style import (
    AMBER, BG, BLUE, CYAN, FG, GREEN, LINE, MUTED,
    card, curve, footer, scene, txt,
)
from scripts.conventional_reference import (
    WINDOW_DEG, METRIC_METHODS, sample, native_metrics, input_angle,
)

ROOT = Path(__file__).resolve().parents[1]
DURATION = 15.0
POSTER_TIME = 3.0
PREVIEW_TIMES = (0.6, 2.5, 4.8, 8.0, 12.6)
KEYS = ('fp32', 'z1024', 'z2048')
LABELS = ('Conventional FP32', 'Z1024', 'Z2048')
COLORS = (BLUE, CYAN, GREEN)


@lru_cache(maxsize=1)
def reference_curves():
    """One shared input grid; no idealized or hand-drawn staircase is used."""
    angles = np.linspace(0, WINDOW_DEG, 2401)
    values = sample(angles)
    return angles, values


def _ideal_dashes(d, points):
    # The same thin white guide remains visible over the near-coincident FP32
    # curve without displacing either curve to invent a visible FP32 error.
    for k in range(0, len(points) - 1, 64):
        curve(d, points[k:min(k + 29, len(points))], FG, 2)


def _plot(t):
    im, d = scene('PRECISION / CONVENTIONAL FP32 + TWO PHASE GRIDS',
                  'Same input. A smooth reference and two step sizes.',
                  'One magnified 0–2.109375° window for all three | White dashes = ideal | Color = reconstructed output')
    angle = float(input_angle(t))
    current = sample(angle)
    txt(d, (65, 204), f'SHARED INPUT  {angle:.5f}°', 32, FG, True)
    txt(d, (1138, 208), 'Identical angle and display scale', 29, MUTED, True)
    angles, values = reference_curves()
    for j, (key, label, color) in enumerate(zip(KEYS, LABELS, COLORS)):
        x = 64 + j * 604
        card(d, (x, 253, x + 584, 961), color)
        txt(d, (x + 26, 273), label, 43, color, True, width=535)
        note = ('FP32 trig reconstruction' if j == 0 else
                ('0.3515625° input bin' if j == 1 else '0.17578125° input bin'))
        txt(d, (x + 26, 333), note, 28, MUTED, True, width=535)
        px, py, pw, ph = x + 42, 416.0, 500.0, 314.0
        # A light scaffold avoids giving the conventional panel a different
        # apparent precision through a different y range or plot size.
        d.line((px, py, px, py + ph, px + pw, py + ph), fill=LINE, width=2)
        actual = np.asarray(values[key + '_deg'], dtype=np.float64)
        ideal = np.asarray(values['ideal_deg'], dtype=np.float64)
        colored = [(px + float(a) / WINDOW_DEG * pw,
                    py + ph - float(v) / WINDOW_DEG * ph)
                   for a, v in zip(angles, actual)]
        guide = [(px + float(a) / WINDOW_DEG * pw,
                  py + ph - float(v) / WINDOW_DEG * ph)
                 for a, v in zip(angles, ideal)]
        # The filled band is exactly the actual angular residual. Tiny Q15
        # overshoots at a grid boundary are retained, not clamped to zero.
        d.polygon([*colored, *reversed(guide)], fill='#62492d')
        curve(d, colored, color, 8)
        _ideal_dashes(d, guide)
        output = float(current[key + '_deg'])
        target = float(current['ideal_deg'])
        xx = px + angle / WINDOW_DEG * pw
        yy = py + ph - output / WINDOW_DEG * ph
        true_y = py + ph - target / WINDOW_DEG * ph
        d.line((xx, true_y, xx, yy), fill=AMBER, width=9)
        d.ellipse((xx - 10, yy - 10, xx + 10, yy + 10), fill=color,
                  outline='#0b1625', width=2)
        d.ellipse((xx - 15, true_y - 15, xx + 15, true_y + 15),
                  outline=FG, width=3)
        txt(d, (px - 4, py + ph + 12), '0°', 23, MUTED)
        txt(d, (px + pw - 83, py + ph + 12), '2.109°', 23, MUTED)
        descriptor = ('Smooth at this scale', 'Larger steps', 'Finer steps')[j]
        txt(d, (x + 26, 785), descriptor, 35, color, True, width=535)
        txt(d, (x + 26, 838), f'Output  {output:.6f}°', 31, FG, True)
        gap = abs(output - target)
        gap_text = f'{gap:.2e}°' if j == 0 else f'{gap:.5f}°'
        txt(d, (x + 26, 892), 'Actual gap  ' + gap_text, 29, AMBER, True, width=535)
    footer(d, 'All three reconstruct the same input. FP32 rounding is real but smaller than a display pixel at this scale.',
           'Single-input view. The separately recorded product RMSE includes two inputs, Q15 reconstruction and floating-point rounding.')
    return im


def _metrics():
    im, d = scene('PRECISION / SAME THREE METHODS / RETAINED NATIVE CPU AUDIT',
                  'Compare the measured accuracy and processing time.',
                  'Same 10-million-product raw-double-angle workload → complex<float> output | FP32 uses the optimized angle-sum route')
    rows = native_metrics()
    for j, (method, label, color) in enumerate(zip(METRIC_METHODS, LABELS, COLORS)):
        x = 64 + j * 604
        r = rows[method]
        rmse, ms = float(r['angular_rmse_rad']), float(r['median_ms'])
        card(d, (x, 253, x + 584, 961), color)
        txt(d, (x + 26, 273), label, 43, color, True, width=535)
        txt(d, (x + 26, 363), 'Angular RMSE / radians', 29, MUTED, True)
        txt(d, (x + 26, 409), f'{rmse:.3e}', 69, color, True, width=535)
        txt(d, (x + 26, 530), 'Median CPU time', 30, MUTED, True)
        txt(d, (x + 26, 579), f'{ms:.2f} ms', 68, color, True, width=535)
        txt(d, (x + 26, 695), '10,000,000 phase products', 29, FG, True, width=535)
        txt(d, (x + 26, 747), f'Accuracy sample: {int(r["evaluated_samples"]):,} pairs',
            26, MUTED, width=535)
        scope = ('Add angles, then sin / cos' if j == 0 else 'Two quantizers + Q15 lookup')
        txt(d, (x + 26, 830), scope, 30, color, True, width=535)
        txt(d, (x + 26, 881), 'Recorded result, not a live reading', 25, MUTED, width=535)
    footer(d, 'FP32 has lower measured phase error; the Q15 paths have shorter runtime in this specific CPU workload.',
           'Source: native_audit_benchmark.csv and native_audit_accuracy.csv. No physical PIM chip result is claimed.', color=AMBER)
    return im


def frame(t, study=None):
    """Return 1920×1080 RGB; the shared exporter owns the final loop dissolve."""
    return (_plot(float(t)) if float(t) < 10.5 else _metrics()).convert('RGB')


def preview(folder=None):
    folder = Path(folder) if folder else ROOT.parents[1] / 'work/baseline_stairs_qa'
    folder.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGB', (1440, 1215), BG)
    for i, t in enumerate(PREVIEW_TIMES):
        im = frame(t)
        im.save(folder / f'baseline_stairs_{i}_{t:.2f}.png')
        small = im.resize((720, 405), Image.Resampling.LANCZOS)
        small.save(folder / f'baseline_stairs_{i}_{t:.2f}_720.png')
        sheet.paste(small, ((i % 2) * 720, (i // 2) * 405))
    sheet.save(folder / 'contact.png')
    frame(POSTER_TIME).resize((720, 405), Image.Resampling.LANCZOS).save(folder / 'poster_720.png')
    return folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    print(preview(args.preview_dir))
