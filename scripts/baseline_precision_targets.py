"""Three equally prominent computed outputs follow one ideal phase target.

Conventional FP32 and both ring paths use the shared reference helper. Output
marker coordinates come from float64 atan2 of the actual restored complex64
channels, including Q15 reconstruction in the ring paths. No visible error is
invented for FP32: errors below a pixel remain numerically reported.

All three lanes share one magnified 0--2.109375 degree window and one horizontal
pixel-per-degree gain. The vertical separation distinguishes ideal and output
symbols; it does not represent angular error. Orange horizontal spans show the
absolute magnitude while the numeric error retains output-minus-ideal sign.
"""
import math

from scripts.visual_style import (
    AMBER, BLUE, CYAN, FG, GREEN, LINE, MUTED,
    card, scene, txt,
)
from scripts import conventional_reference as reference

DURATION = 16.0
POSTER_TIME = 3.0
PREVIEW_TIMES = [0.8, 3.0, 6.1, 10.5, 14.0]
WINDOW_DEG = reference.WINDOW_DEG
TRACK_X = 590.0
TRACK_WIDTH = 1190.0
COLORS = (BLUE, CYAN, GREEN)
KEYS = ('fp32', 'z1024', 'z2048')
LABELS = ('Conventional FP32', 'Z1024', 'Z2048')
LANES = (330, 576, 822)


def _x(angle_deg):
    return TRACK_X + float(angle_deg) / WINDOW_DEG * TRACK_WIDTH


def signed_error(output_deg, ideal_deg):
    """Shortest signed phase error, with full precision for tiny FP32 gaps."""
    value = float(output_deg) - float(ideal_deg)
    return math.degrees(math.atan2(math.sin(math.radians(value)), math.cos(math.radians(value))))


def _error_text(value):
    return f'{value:+.2e}°' if abs(value) < 0.001 else f'{value:+.5f}°'


def _bullseye(d, x, y):
    r = 25
    d.ellipse((x - r, y - r, x + r, y + r), fill='#0b1627', outline=FG, width=4)
    d.ellipse((x - 14, y - 14, x + 14, y + 14), outline=FG, width=3)
    d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=FG)
    d.line((x - r - 9, y, x - r + 6, y), fill=FG, width=3)
    d.line((x + r - 6, y, x + r + 9, y), fill=FG, width=3)


def _pin(d, x, y, color):
    r = 26
    d.polygon([(x, y - r - 14), (x - r * 0.6, y - r * 0.5),
               (x + r * 0.6, y - r * 0.5)], fill=color)
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=FG, width=3)
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill='#0b1627')


def _lane(d, y, key, label, color, values, product=False):
    card(d, (64, y - 113, 1856, y + 123), color)
    # Conventional FP32 is a full-size lane, not an annotation beneath the rings.
    txt(d, (91, y - 90), label, 48 if key == 'fp32' else 58, color, True, width=465)
    note = {'fp32': 'Restored FP32 phase', 'z1024': '0.3515625° / phase bin',
            'z2048': '0.17578125° / phase bin'}[key]
    txt(d, (94, y - 18), note, 33, FG, True, width=455)
    txt(d, (94, y + 38), 'Computed product' if product else 'Computed output', 33, MUTED)
    ideal = float(values['ideal_deg'])
    output = float(values[key + '_deg'])
    error = signed_error(output, ideal)
    d.line((TRACK_X, y, TRACK_X + TRACK_WIDTH, y), fill=LINE, width=7)
    if key == 'fp32':
        # A continuous reconstructed phase route, rather than invented phase slots.
        d.line((TRACK_X, y, TRACK_X + TRACK_WIDTH, y), fill='#284a75', width=4)
        for k in range(7):
            xx = TRACK_X + TRACK_WIDTH * k / 6
            d.line((xx, y - 11, xx, y + 11), fill='#456686', width=2)
    else:
        n = 1024 if key == 'z1024' else 2048
        count = 6 if n == 1024 else 12
        for k in range(count + 1):
            xx = _x(k * 360.0 / n)
            d.line((xx, y - 14, xx, y + 14), fill='#456079', width=2)
            d.ellipse((xx - 7, y - 7, xx + 7, y + 7), fill='#14243a', outline='#65809a', width=2)
    ix, ox = _x(ideal), _x(output)
    d.line((ix, y - 29, ix, y), fill=FG, width=3)
    d.line((ox, y + 1, ox, y + 15), fill=color, width=4)
    # No minimum-length amplification: subpixel FP32/Q15 spans stay subpixel.
    if abs(ix - ox) >= 0.75:
        left, right = sorted((ix, ox))
        d.line((left, y, right, y), fill=AMBER, width=13)
        for xx in (ix, ox):
            d.line((xx, y - 16, xx, y + 16), fill=AMBER, width=3)
    _bullseye(d, ix, y - 58)
    _pin(d, ox, y + 52, color)
    txt(d, (TRACK_X, y + 76), 'Signed error: ' + _error_text(error), 32,
        color if key == 'fp32' else AMBER, True)


def _scope(d):
    txt(d, (65, 976), 'Magnified 0–2.109375° window. All three tracks use the same angle scale.',
        33, AMBER, True, width=1790)
    txt(d, (65, 1024), 'Horizontal span = phase error. Vertical offsets only separate symbols. Error = output − ideal.',
        29, MUTED, width=1790)


def _following(t):
    im, d = scene('PRECISION / CONVENTIONAL FP32 AND PHASE-RING', 'Follow one angle three ways.',
                  'White target = ideal input | Colored pin = reconstructed output | Orange span = actual error')
    values = reference.sample(float(reference.input_angle(t)))
    for y, key, label, color in zip(LANES, KEYS, LABELS, COLORS):
        _lane(d, y, key, label, color, values)
    _scope(d)
    return im


def _products():
    im, d = scene('PRECISION / THE SAME TWO INPUTS', 'Two inputs. Three computed products.',
                  'Actual example: 0.29° + 0.29° | Rings quantize each input separately, then restore Q15 output')
    values = reference.product(0.29, 0.29)
    for y, key, label, color in zip(LANES, KEYS, LABELS, COLORS):
        _lane(d, y, key, label, color, values, product=True)
    _scope(d)
    return im


def _measured():
    im, d = scene('RECORDED NATIVE CPU AUDIT / SAME INPUT AND COMPLEX OUTPUT', 'Accuracy and time are a tradeoff.',
                  '10,000,000 unit-phase products | Accuracy: first 200,000 pairs | Timing: median of nine runs')
    metrics = reference.native_metrics()
    for j, (method, label, color) in enumerate(zip(reference.METRIC_METHODS, LABELS, COLORS)):
        x = 64 + j * 604
        r = metrics[method]
        error = float(r['angular_rmse_rad'])
        ms = float(r['median_ms'])
        card(d, (x, 224, x + 584, 902), color)
        txt(d, (x + 25, 250), label, 43, color, True, width=536)
        txt(d, (x + 25, 321), 'Optimized angle sum' if j == 0 else 'Floor + Q15 reconstruction',
            32, MUTED, width=536)
        txt(d, (x + 25, 414), 'ANGULAR RMSE', 32, MUTED, True)
        # Scientific notation preserves the tiny, nonzero conventional error.
        number = f'{error:.2e}' if j == 0 else f'{error:.6f}'
        txt(d, (x + 25, 461), number, 77, color, True, width=532)
        txt(d, (x + 25, 563), 'radians', 35, FG, True)
        txt(d, (x + 25, 647), 'MEDIAN CPU TIME', 32, MUTED, True)
        txt(d, (x + 25, 692), f'{ms:.2f} ms', 75, color, True, width=532)
        txt(d, (x + 25, 815), 'Same 10-million-product task', 31, MUTED, width=532)
    txt(d, (83, 934), 'Conventional FP32 keeps far smaller phase error; the ring paths take less CPU time here.',
        35, AMBER, True, width=1750)
    txt(d, (65, 991), 'FP32 baseline: add angles, then one cos/sin pair. All paths restore complex<float> output.',
        30, MUTED, width=1790)
    txt(d, (65, 1036), 'This result concerns one optimized CPU task. Physical PIM speed and energy were not measured.',
        27, MUTED, width=1790)
    return im


def frame(t, study=None):
    """Return a 1920×1080 RGB frame; exporter owns the final loop transition."""
    if t < 9.0:
        return _following(t)
    if t < 12.5:
        return _products()
    return _measured()
