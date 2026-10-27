"""Large true-floor stair motions for a public introduction to phase precision.

The 0--2.109375 degree display window is magnified, not a full-circle scale.
Single-input stairs and a separate two-input example use src.phase_ring.quantize.
The final RMSE values are the recorded native audit, first 200000 input pairs
of the 10-million-product workload. No new numerical experiment is performed.
"""
import csv
from functools import lru_cache
import math
from pathlib import Path

import numpy as np

from scripts.visual_style import (
    AMBER, BLUE, CYAN, FG, GREEN, LINE, MUTED, RED,
    card, curve, glow, scene, txt,
)
from src import phase_ring as ring

ROOT = Path(__file__).resolve().parents[1]
DURATION = 15.0
POSTER_TIME = 4.8
PREVIEW_TIMES = [0.5, 2.2, 3.0, 4.8, 7.0, 9.8, 13.0]
WINDOW_DEG = 6 * 360 / 1024


def quantized_deg(angle_deg, n):
    """Use the implementation's actual floor-and-wrap quantizer."""
    return ring.quantize(np.deg2rad(angle_deg), n).astype(np.float64) * (360.0 / n)


@lru_cache(maxsize=1)
def accuracy_rows():
    with (ROOT / 'results/native_audit_accuracy.csv').open(encoding='utf-8') as f:
        return {r['method']: r for r in csv.DictReader(f) if int(r['n']) == 10_000_000}


@lru_cache(maxsize=2)
def _stairs(n):
    x = np.linspace(0, WINDOW_DEG, 1800)
    return x, quantized_deg(x, n)


def _foot(d, first, second):
    txt(d, (65, 982), first, 34, AMBER, True, width=1790)
    txt(d, (65, 1030), second, 29, MUTED, width=1790)


def _stair_scene(t):
    im, d = scene('C / PRECISION / SAME INPUT', 'One smooth input. Two step sizes.',
                  'Magnified phase window: 0–2.109375° | White = smooth input | Orange gap = actual floor error')
    # Smooth continuous input, common to both panels; no artificial error added.
    angle = WINDOW_DEG * (0.5 - 0.45 * math.cos(math.tau * t / 8.8))
    for j, (n, color) in enumerate([(1024, CYAN), (2048, GREEN)]):
        x = 64 + j * 916
        card(d, (x, 215, x + 876, 932), color)
        txt(d, (x + 30, 236), f'Z{n}', 64, color, True)
        bin_text = '0.3515625°' if n == 1024 else '0.17578125°'
        txt(d, (x + 315, 252), bin_text + ' / step', 43, FG, True, width=535)
        px, py, pw, ph = x + 56, 373, 764, 416
        sx, sy = _stairs(n)
        points = list(zip(px + sx / WINDOW_DEG * pw,
                          py + ph - sy / WINDOW_DEG * ph))
        # A broad terrace, rather than a small axis-heavy plot, owns the frame.
        d.polygon([(px, py + ph), *points, (px + pw, py + ph)], fill='#123b42' if n == 1024 else '#153d32')
        # The entire true gap is colored, including intervals away from the cursor.
        # The enclosed area is exactly the space between floor output and input.
        d.polygon([*points, (px + pw, py), (px, py + ph)], fill='#62492d')
        curve(d, points, color, 12)
        d.line((px, py + ph, px + pw, py), fill='#6d7b8e', width=3)
        q = float(quantized_deg(angle, n))
        xx = px + angle / WINDOW_DEG * pw
        yy = py + ph - q / WINDOW_DEG * ph
        reference_y = py + ph - angle / WINDOW_DEG * ph
        d.line((xx, reference_y, xx, yy), fill=AMBER, width=17)
        d.ellipse((xx - 14, reference_y - 14, xx + 14, reference_y + 14), fill=FG)
        glow(d, (xx, yy), 10, color)
        if yy > reference_y + 0.1:
            bx = xx + 37
            d.line((bx, reference_y, bx, yy), fill=AMBER, width=7)
            d.line((bx - 8, reference_y, bx + 8, reference_y), fill=AMBER, width=4)
            d.line((bx - 8, yy, bx + 8, yy), fill=AMBER, width=4)
        txt(d, (x + 31, 817), 'Larger steps' if n == 1024 else 'Finer steps', 48, color, True)
        txt(d, (x + 31, 883), f'Current gap: {angle - q:.4f}°', 36, AMBER, True)
    _foot(d, 'Same input and display scale. Every step comes from the actual floor function.',
          'One-input illustration. Two input errors can accumulate when phase products are formed.')
    return im


def _two_inputs():
    im, d = scene('C / PRECISION / TWO INPUTS', 'Two input errors can add.',
                  'Actual example: 0.29° + 0.29° | Orange segments show each input’s floor error before LUT rounding')
    a = b = 0.29
    for j, (n, color) in enumerate([(1024, CYAN), (2048, GREEN)]):
        y = 240 + j * 336
        card(d, (64, y, 1856, y + 296), color)
        txt(d, (96, y + 27), f'Z{n}', 61, color, True)
        qa, qb = float(quantized_deg(a, n)), float(quantized_deg(b, n))
        ea, eb = a - qa, b - qb
        x0, scale, by = 462, 2010, y + 144
        output_x = x0 + (qa + qb) * scale
        true_x = x0 + (a + b) * scale
        d.rounded_rectangle((x0, by, true_x, by + 55), radius=16, fill='#26384d')
        if output_x > x0:
            d.rounded_rectangle((x0, by, output_x, by + 55), radius=16, fill=color)
        split = output_x + ea * scale
        d.rectangle((output_x, by, split, by + 55), fill=AMBER)
        d.rectangle((split, by, true_x, by + 55), fill=RED)
        d.line((split, by - 14, split, by + 70), fill=FG, width=3)
        d.ellipse((true_x - 16, by + 11, true_x + 16, by + 44), fill=FG)
        txt(d, (output_x + 14, by - 58), 'Error A', 36, AMBER, True)
        txt(d, (split + 14, by + 77), 'Error B', 36, RED, True)
        txt(d, (98, y + 206), f'Total gap: {ea + eb:.5f}°', 44, AMBER, True)
    _foot(d, 'The two gaps are computed, not invented for the animation.',
          'The final measured product error also includes Q15 table reconstruction and floating-point rounding.')
    return im


def _measured():
    im, d = scene('C / PRECISION / RECORDED CPU AUDIT', 'Finer resolution. Smaller measured error.',
                  'Angular RMSE of phase products | First 200,000 pairs in the recorded 10-million-product workload')
    rows = accuracy_rows()
    values = [float(rows[f'Z{n} Q15 end-to-end']['angular_rmse_rad']) for n in (1024, 2048)]
    for j, (n, value, color) in enumerate(zip((1024, 2048), values, (CYAN, GREEN))):
        x = 64 + j * 916
        card(d, (x, 245, x + 876, 865), color)
        txt(d, (x + 35, 278), f'Z{n}', 68, color, True)
        txt(d, (x + 35, 391), f'{value:.6f}', 109, color, True)
        txt(d, (x + 35, 530), 'radians / angular RMSE', 43, FG, True)
        d.rounded_rectangle((x + 35, 639, x + 811, 699), radius=15, fill='#1e3046')
        d.rounded_rectangle((x + 35, 639, x + 35 + value / max(values) * 776, 699), radius=15, fill=color)
        txt(d, (x + 35, 761), 'Includes both inputs + Q15 output', 34, MUTED, width=810)
    fp = float(rows['FP32 four-trig product']['angular_rmse_rad'])
    txt(d, (87, 900), f'FP32 four-trig reference: {fp:.2e} rad RMSE', 37, BLUE, True)
    _foot(d, 'A measured accuracy tradeoff. This scene makes no speed ranking.',
          'Source: native_audit_accuracy.csv | Same recorded inputs; double summed-angle reference.')
    return im


def precision_legacy(t, study=None):
    """Return a 1920×1080 RGB frame; the exporter manages the loop transition."""
    if t < 8.8:
        return _stair_scene(t)
    if t < 11.5:
        return _two_inputs()
    return _measured()


def precision(t, study=None):
    from scripts.baseline_precision_stairs import frame
    return frame(t,study)
