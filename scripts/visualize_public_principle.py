"""A public-facing, numerically grounded unit-phasor arithmetic illustration.

The two routes use equal editorial stage pacing. They do not encode CPU runtime
or physical hardware latency. All phase indices and Q15 values use the retained
reference implementation; the four real products use its complex64 operands.
Only this new module and explicitly requested preview files are written.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw

from scripts.visual_style import (
    W, H, BG, PANEL, LINE, FG, MUTED, BLUE, CYAN, GREEN, AMBER,
    background, card, curve, ease, font, glow, txt, wire,
)
from src import conventional as fp
from src import phase_ring as ring

ROOT = Path(__file__).resolve().parents[1]
DURATION = 14.0


@lru_cache(maxsize=2)
def numerical_example(n=1024):
    """Keep raw angles shared; changing n never substitutes rounded indices."""
    # Quarter-bin offsets expose a real floor-quantization error without making
    # up a residual. The public animation keeps N=1024 throughout for continuity.
    a = (750.25 / 1024) * math.tau
    b = (400.25 / 1024) * math.tau
    x, y = fp.encode_pair(np.array([a]), np.array([b]))
    conventional = fp.multiply(x, y)[0]
    qa, qb = ring.quantize(np.array([a, b]), n)
    index = int(ring.add(np.array([qa]), np.array([qb]), n)[0])
    lut = ring.make_lut(n)
    output = ring.decode(np.array([index]), lut)[0]
    ac = np.float32(x[0].real * y[0].real)
    bd = np.float32(x[0].imag * y[0].imag)
    ad = np.float32(x[0].real * y[0].imag)
    bc = np.float32(x[0].imag * y[0].real)
    angle_error = math.remainder(
        math.atan2(float(output.imag), float(output.real)) -
        math.atan2(float(conventional.imag), float(conventional.real)), math.tau)
    return dict(n=n, a=a, b=b, x=x[0], y=y[0], conventional=conventional,
        qa=int(qa), qb=int(qb), index=index, q15=tuple(int(v) for v in lut[index]),
        output=output, products=(float(ac), float(bd), float(ad), float(bc)),
        angle_error_rad=angle_error, angle_error_deg=math.degrees(angle_error),
        complex_error=float(abs(output - conventional)))


def _center(d, xy, text, size, color=FG, bold=False, mono=False):
    f = font(size, bold, mono)
    box = d.textbbox((0, 0), str(text), font=f)
    d.text((xy[0] - (box[2] - box[0]) / 2, xy[1]), str(text), font=f, fill=color)


def _point(cx, cy, r, angle):
    return cx + r * math.cos(angle), cy - r * math.sin(angle)


def _arc(d, cx, cy, r, start, end, color, width=8):
    count = max(2, int(abs(end - start) * 42))
    points = [_point(cx, cy, r, value) for value in np.linspace(start, end, count)]
    curve(d, points, color, width)


def _hand(d, cx, cy, r, angle, color, width=7, tip=True):
    end = _point(cx, cy, r, angle)
    d.line((cx, cy, *end), fill=color, width=width)
    if tip:
        glow(d, end, 6, color)
    return end


def _signal(d, box, z, color, t, active=True, marker=True):
    """Actual complex output drives amplitude and phase of the displayed wave."""
    x, y, w, h = box
    d.line((x, y + h / 2, x + w, y + h / 2), fill=LINE, width=2)
    xx = np.linspace(0, w, 250)
    carrier = 2 * math.tau * xx / w - t * 2.25
    values = np.imag(complex(z) * np.exp(1j * carrier))
    yy = y + h / 2 - values * h * 0.39
    curve(d, zip(x + xx, yy), color if active else LINE, 6 if active else 3)
    if marker and active:
        px = (t * 0.23) % 1
        py = y + h / 2 - np.imag(complex(z) * np.exp(1j * (2 * math.tau * px - t * 2.25))) * h * 0.39
        glow(d, (x + px * w, py), 6, color)


def _base(title):
    im = background().copy()
    d = ImageDraw.Draw(im)
    txt(d, (64, 61), title, 76, FG, True)
    card(d, (64, 224, 940, 964), BLUE, 26)
    card(d, (980, 224, 1856, 964), CYAN, 26)
    txt(d, (96, 244), 'Conventional computing', 44, BLUE, True)
    txt(d, (1012, 244), 'Phase-Ring computing', 44, CYAN, True)
    txt(d, (1682, 251), 'Z1024', 36, MUTED, True, True)
    txt(d, (66, 1008), 'Unit phasors only  |  Floor/Q15 approximation  |  Conceptual flow, not hardware timing',
        32, MUTED, width=1790)
    return im, d


def _input_pair(d, left, values, t):
    for j, (z, color, letter) in enumerate([(values['x'], BLUE, 'A'), (values['y'], GREEN, 'B')]):
        x = left + 42 + j * 405
        txt(d, (x, 320), letter, 36, color, True)
        _signal(d, (x + 42, 314, 310, 91), z, color, t)


def _product_block(d, cx, y, value, active):
    card(d, (cx - 73, y, cx + 73, y + 124), BLUE if active else LINE, 18,
        '#183656' if active else PANEL)
    _center(d, (cx, y + 1), '×', 54, BLUE if active else MUTED, True)
    _center(d, (cx, y + 68), f'{value:+.3f}', 36, FG if active else MUTED, True, True)


def _pipeline(t, values):
    title = 'Same input' if t < 2.6 else ('Different arithmetic' if t < 7.4 else 'Lookup result')
    im, d = _base(title)
    _input_pair(d, 64, values, t)
    _input_pair(d, 980, values, t)
    p = max(0.0, min(1.0, (t - 1.6) / 6.5))
    # Each side follows the same normalized editorial stage progress.
    active_product = p >= 0.10
    active_combine = p >= 0.48
    active_output = p >= 0.82
    pulse = t * 0.30
    centers = [177, 377, 577, 777]
    for j, cx in enumerate(centers):
        # Both component buses feed all four real products. These are conceptual
        # wires, not a gate count, implementation floorplan or timing diagram.
        for bus_y, pin, color, source in [(434, -19, BLUE, 292), (454, 19, GREEN, 697)]:
            wire(d, [(source, 405), (source, bus_y), (cx + pin, bus_y), (cx + pin, 488)],
                color, pulse + j * .12)
        _product_block(d, cx, 488, values['products'][j], active_product)
    for pair, out_x, symbol in [((0, 1), 277, '−'), ((2, 3), 677, '+')]:
        for j in pair:
            wire(d, [(centers[j], 612), (centers[j], 654), (out_x, 654), (out_x, 682)],
                BLUE, pulse + j * .11)
        card(d, (out_x - 61, 682, out_x + 61, 764), BLUE if active_combine else LINE, 17)
        _center(d, (out_x, 679), symbol, 63, BLUE if active_combine else MUTED, True)
        wire(d, [(out_x, 764), (out_x, 802), (477, 802), (477, 838)], BLUE, pulse)
    _signal(d, (122, 867, 720, 70), values['conventional'], BLUE, t, active_output)

    # The two input phases remain explicit. The green input hand rotates into an
    # accumulated phase; a separate cyan needle indicates the wrapped result.
    cx, cy, radius = 1239, 638, 165
    qa_angle = values['qa'] / values['n'] * math.tau
    qb_angle = values['qb'] / values['n'] * math.tau
    addition = ease(max(0, min(1, (p - 0.10) / .38)))
    wire(d, [(1208, 405), (1208, 438), (cx, 438), (cx, 473)], CYAN, pulse)
    wire(d, [(1613, 405), (1613, 438), (cx, 438), (cx, 473)], GREEN, pulse)
    d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill='#0a1726', outline=LINE, width=6)
    for j in range(32):
        angle = j * math.tau / 32
        start, end = _point(cx, cy, radius - 7, angle), _point(cx, cy, radius + 5, angle)
        d.line((*start, *end), fill=MUTED if j % 8 == 0 else LINE, width=3)
    _arc(d, cx, cy, radius + 13, 0, qa_angle, BLUE, 5)
    _arc(d, cx, cy, radius + 29, qa_angle, qa_angle + qb_angle * addition, GREEN, 8)
    _hand(d, cx, cy, radius - 14, qa_angle, BLUE, 6)
    # The input needles keep their actual absolute phases. The cyan accumulator
    # starts at A and adds B around the same dial; its tip follows the growing
    # addition arc exactly. Intermediate motion is editorial, not an RTL trace.
    _hand(d, cx, cy, radius - 24, qb_angle, GREEN, 6)
    if p >= .10:
        _hand(d, cx, cy, radius - 8, (qa_angle + qb_angle * addition) % math.tau, CYAN, 10)
    d.ellipse((cx - 57, cy - 57, cx + 57, cy + 57), fill=BG, outline=LINE, width=2)
    _center(d, (cx, cy - 36), values['index'] if active_combine else '+', 56, CYAN, True, True)
    # A solid label backplate keeps the dial arc and input wire out of the text.
    d.rounded_rectangle((1074, 439, 1417, 490), radius=10, fill=PANEL)
    txt(d, (1090, 444), 'Phase addition', 36, CYAN, True)
    _center(d, (cx, 835), f"{values['qa']} + {values['qb']}" +
        (f" → {values['index']}" if active_combine else ''), 36, FG, True, True)

    # The selected neighborhood and its actual int16 contents come from the LUT.
    selected = values['index']
    first = (selected // 12) * 12
    lookup_x, lookup_y = 1488, 512
    txt(d, (1491, 449), 'Lookup', 40, CYAN, True)
    for j in range(12):
        address = first + j
        x, y = lookup_x + (j % 4) * 72, lookup_y + (j // 4) * 64
        is_selected = active_combine and address == selected
        fill = '#1a4e54' if is_selected else '#122237'
        d.rounded_rectangle((x, y, x + 67, y + 58), radius=8, fill=fill,
            outline=CYAN if is_selected else LINE, width=4 if is_selected else 2)
        _center(d, (x + 34, y + 7), address, 36, FG if is_selected else MUTED, True, True)
    selected_row = (selected - first) // 4
    selected_col = (selected - first) % 4
    gutter_y = lookup_y + selected_row * 64 - 4
    selected_x = lookup_x + selected_col * 72
    selected_y = lookup_y + selected_row * 64 + 29
    wire(d, [(cx + radius + 31, cy), (1457, cy), (1457, gutter_y),
        (selected_x - 4, gutter_y), (selected_x - 4, selected_y), (selected_x, selected_y)], CYAN, pulse)
    txt(d, (1495, 730), 'Q15', 36, CYAN, True)
    txt(d, (1492, 774), f"{values['q15'][0]:+d}, {values['q15'][1]:+d}", 36,
        FG if active_output else MUTED, True, True)
    wire(d, [(1640, 815), (1640, 857)], CYAN, pulse)
    _signal(d, (1038, 867, 720, 70), values['output'], CYAN, t, active_output)
    return im


def _outputs(t, values):
    im, d = _base('Approximate match')
    for cx, z, color in [(502, values['conventional'], BLUE), (1418, values['output'], CYAN)]:
        cy, radius = 513, 151
        d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill='#0a1726', outline=LINE, width=5)
        d.line((cx - radius - 19, cy, cx + radius + 19, cy), fill=LINE, width=2)
        d.line((cx, cy - radius - 19, cx, cy + radius + 19), fill=LINE, width=2)
        for j in range(48):
            angle = j * math.tau / 48
            a, b = _point(cx, cy, radius - 6, angle), _point(cx, cy, radius + 4, angle)
            d.line((*a, *b), fill=MUTED if j % 12 == 0 else LINE, width=2)
        angle = math.atan2(float(z.imag), float(z.real))
        _arc(d, cx, cy, radius + 16, 0, angle, color, 8)
        _hand(d, cx, cy, radius - 12, angle, color, 11)
        glow(d, (cx, cy), 7, color)
        _center(d, (cx, 686), f'{math.degrees(angle):.5f}°', 49, color, True, True)
        _signal(d, (cx - 365, 771, 730, 136), z, color, t, True)
    # The wave discrepancy is smaller than a screen pixel; its true value is
    # stated rather than enlarged or hidden. Both waves share a carrier clock.
    _center(d, (960, 928), f"Angular gap {abs(values['angle_error_deg']):.4f}°", 43, AMBER, True)
    return im


def principle(t, study=None):
    """Return a raw 1920x1080 RGB frame; exporter controls loop crossfades."""
    t = max(0.0, min(float(t), DURATION))
    values = numerical_example(1024)
    frame = _pipeline(t, values) if t < 9.7 else _outputs(t, values)
    # A short local dissolve links stages, without implying algorithm iteration.
    if 9.7 <= t < 10.1:
        frame = Image.blend(_pipeline(9.7, values), frame, ease((t - 9.7) / .4))
    return frame.convert('RGB')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-dir', type=Path, default=ROOT.parents[1] / 'work/public_principle_qa')
    args = parser.parse_args()
    args.preview_dir.mkdir(parents=True, exist_ok=True)
    for t in [0.5, 3.0, 5.8, 8.7, 10.8, 12.8]:
        frame = principle(t)
        frame.save(args.preview_dir / f'principle_{t:04.1f}_1080.png')
        frame.resize((1280, 720), Image.Resampling.LANCZOS).save(args.preview_dir / f'principle_{t:04.1f}_720.png')
    values = numerical_example()
    print({k: values[k] for k in ['n', 'qa', 'qb', 'index', 'q15', 'angle_error_deg', 'complex_error']})
    print('Preview frames written to ' + str(args.preview_dir))


if __name__ == '__main__':
    main()
