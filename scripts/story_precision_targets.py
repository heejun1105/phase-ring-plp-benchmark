"""Alternate precision story: a smooth target and snapping stored positions.

Every horizontal coordinate uses the same magnified 0--2.109375 degree window.
The smooth input and its floor-quantized position are calculated independently
of editorial time. Vertical offsets separate the two symbols; only the orange
horizontal bracket represents angular error. The two-input scene adds the two
separately floor-quantized inputs, not the quantization of their sum.

The final accuracy values are unchanged native-audit records for the first
200000 pairs of the 10-million-product workload. No new benchmark is performed.
"""
import csv
from functools import lru_cache
import math
from pathlib import Path

import numpy as np

from scripts.visual_style import (
    AMBER, BLUE, CYAN, FG, GREEN, LINE, MUTED,
    card, scene, txt,
)
from src import phase_ring as ring

ROOT = Path(__file__).resolve().parents[1]
DURATION = 16.0
POSTER_TIME = 6.4
PREVIEW_TIMES = [1.0, 3.2, 6.4, 11.2, 14.2]
WINDOW_DEG = 6 * 360 / 1024
TRACK_X = 480.0
TRACK_WIDTH = 1300.0


def quantized_deg(angle_deg, n):
    """Actual implementation floor/wrap, converted back to degrees."""
    return ring.quantize(np.deg2rad(angle_deg), n).astype(np.float64) * 360.0 / n


def target_angle(t):
    """One common smooth angle; its motion is editorial, its quantization is real."""
    return WINDOW_DEG * (0.5 - 0.43 * math.cos(math.tau * t / 10.0))


@lru_cache(maxsize=1)
def recorded_accuracy():
    with (ROOT / 'results/native_audit_accuracy.csv').open(encoding='utf-8') as f:
        return {r['method']: r for r in csv.DictReader(f)
                if int(r['n']) == 10_000_000}


def _x(angle_deg):
    return TRACK_X + float(angle_deg) / WINDOW_DEG * TRACK_WIDTH


def _bullseye(d, x, y, radius, color=FG):
    d.ellipse((x - radius, y - radius, x + radius, y + radius),
              fill='#0b1627', outline=color, width=6)
    inner = radius * 0.55
    d.ellipse((x - inner, y - inner, x + inner, y + inner), outline=color, width=3)
    d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
    d.line((x - radius - 12, y, x - radius + 8, y), fill=color, width=4)
    d.line((x + radius - 8, y, x + radius + 12, y), fill=color, width=4)


def _pin(d, x, y, radius, color):
    d.polygon([(x, y - radius - 18), (x - radius * 0.6, y - radius * 0.5),
               (x + radius * 0.6, y - radius * 0.5)], fill=color)
    d.ellipse((x - radius, y - radius, x + radius, y + radius),
              fill=color, outline=FG, width=3)
    d.ellipse((x - radius * 0.34, y - radius * 0.34,
               x + radius * 0.34, y + radius * 0.34), fill='#0b1627')


def _lane(d, y, n, angle, stored, color, large=False, gap_label=None):
    """One physical x scale for input, slots, stored position and gap."""
    offset = 122 if large else 79
    radius = 49 if large else 30
    txt(d, (96, y - 103 if large else y - 97), f'Z{n}', 64 if large else 57, color, True)
    txt(d, (96, y - 17), '0.3515625° / slot' if n == 1024 else '0.17578125° / slot',
        35, FG, True, width=356)
    txt(d, (96, y + 42), 'Stored positions', 34, MUTED)
    # Stored positions are the exact 10/11-bit grid within this zoom window.
    slots = int(round(WINDOW_DEG / (360.0 / n)))
    d.line((TRACK_X, y, TRACK_X + TRACK_WIDTH, y), fill=LINE, width=7)
    d.line((TRACK_X, y - offset, TRACK_X + TRACK_WIDTH, y - offset), fill='#24354a', width=2)
    for k in range(slots + 1):
        xx = _x(k * 360.0 / n)
        r = 13 if large else 10
        active = abs(k * 360.0 / n - stored) < 1e-9
        d.line((xx, y - 20, xx, y + 20), fill=color if active else '#456079', width=3)
        d.ellipse((xx - r, y - r, xx + r, y + r),
                  fill=color if active else '#14243a', outline=color if active else '#65809a', width=3)
    ix, qx = _x(angle), _x(stored)
    # Vertical offsets distinguish symbols; the error is the horizontal span only.
    d.line((ix, y - offset + radius + 10, ix, y), fill=FG, width=3)
    d.line((qx, y + 1, qx, y + offset - radius - 19), fill=color, width=4)
    if ix > qx + 0.01:
        d.line((qx, y, ix, y), fill=AMBER, width=16)
        for xx in (qx, ix):
            d.line((xx, y - 23, xx, y + 23), fill=AMBER, width=4)
    _bullseye(d, ix, y - offset, radius, FG)
    _pin(d, qx, y + offset, radius, color)
    label = gap_label or f'Gap: {angle - stored:.4f}°'
    txt(d, (TRACK_X, y + (202 if large else 112)), label,
        42 if large else 36, AMBER, True)


def _scope(d, note='The colored follower snaps to the actual floor-quantized position.'):
    txt(d, (65, 982), 'Magnified 0–2.109375° window. Same horizontal angle scale throughout.',
        33, AMBER, True, width=1790)
    txt(d, (65, 1031), note, 30, MUTED, width=1790)


def _one_input(t):
    im, d = scene('PRECISION / AN ALTERNATIVE VIEW', 'An angle falls between stored positions.',
                  'White target = smooth input | Colored pin = stored position | Orange span = actual gap')
    card(d, (64, 232, 1856, 937), CYAN)
    angle = target_angle(t)
    _lane(d, 579, 1024, angle, float(quantized_deg(angle, 1024)), CYAN, large=True)
    _scope(d)
    return im


def _two_resolutions(t):
    im, d = scene('PRECISION / THE SAME INPUT', 'More positions. Smaller gaps.',
                  'The white targets share one angle. Followers use the same floor rule at different resolutions.')
    angle = target_angle(t)
    for y, n, color in [(386, 1024, CYAN), (734, 2048, GREEN)]:
        card(d, (64, y - 171, 1856, y + 171), color)
        _lane(d, y, n, angle, float(quantized_deg(angle, n)), color)
    _scope(d, 'No artificial error is added. More positions change precision; this is not a speed ranking.')
    return im


def _two_inputs():
    im, d = scene('PRECISION / TWO SEPARATELY QUANTIZED INPUTS', 'Both input gaps can add.',
                  'Actual example: 0.29° + 0.29° | The white target is their true sum: 0.58°')
    a = b = 0.29
    for y, n, color in [(386, 1024, CYAN), (734, 2048, GREEN)]:
        card(d, (64, y - 171, 1856, y + 171), color)
        qa, qb = float(quantized_deg(a, n)), float(quantized_deg(b, n))
        ea, eb = a - qa, b - qb
        _lane(d, y, n, a + b, qa + qb, color,
              gap_label=f'Input gaps: {ea:.5f}° + {eb:.5f}° = {ea + eb:.5f}°')
    _scope(d, 'Pins show the sum of two stored positions. Q15 reconstruction error is separate from this example.')
    return im


def _measured():
    im, d = scene('PRECISION / RECORDED ACCURACY', 'The measured product error is smaller too.',
                  'Angular RMSE | First 200,000 pairs of the recorded 10-million-product native CPU workload')
    rows = recorded_accuracy()
    for j, (n, color) in enumerate([(1024, CYAN), (2048, GREEN)]):
        x = 64 + j * 916
        r = rows[f'Z{n} Q15 end-to-end']
        value = float(r['angular_rmse_rad'])
        card(d, (x, 239, x + 876, 888), color)
        txt(d, (x + 36, 274), f'Z{n}', 68, color, True)
        # Equal angle scale for both literal error-length strips; no target motion
        # or hypothetical distribution is inferred from an aggregate RMSE.
        start = x + 39
        d.line((start, 441, x + 813, 441), fill=LINE, width=6)
        end = start + math.degrees(value) / WINDOW_DEG * TRACK_WIDTH
        d.line((start, 441, end, 441), fill=AMBER, width=20)
        d.line((start, 417, start, 465), fill=AMBER, width=4)
        d.line((end, 417, end, 465), fill=AMBER, width=4)
        txt(d, (x + 36, 513), f'{math.degrees(value):.4f}°', 100, color, True)
        txt(d, (x + 36, 648), f'{value:.6f} rad RMSE', 45, FG, True)
        txt(d, (x + 36, 751), 'Both inputs + Q15 output', 39, MUTED, True)
        txt(d, (x + 36, 819), 'Recorded value, not a live reading', 30, MUTED)
    fp = float(rows['FP32 four-trig product']['angular_rmse_rad'])
    txt(d, (83, 920), f'FP32 four-trig reference: {fp:.2e} rad RMSE', 34, BLUE, True)
    txt(d, (65, 982), 'Accuracy comparison only. The recorded values do not establish a speed ranking.',
        33, AMBER, True, width=1790)
    txt(d, (65, 1031), 'Source: native_audit_accuracy.csv. RMSE includes phase quantization and Q15 reconstruction.',
        30, MUTED, width=1790)
    return im


def frame(t, study=None):
    """Return one 1920×1080 RGB frame; the exporter owns the loop transition."""
    if t < 4.0:
        return _one_input(t)
    if t < 10.0:
        return _two_resolutions(t)
    if t < 12.8:
        return _two_inputs()
    return _measured()
