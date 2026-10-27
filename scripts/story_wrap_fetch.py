"""A large ring and a stored-answer drawer, using the existing arithmetic model.

Each six-second example replays exact integer increments. The first example
adds a magnified boundary strip so a single step across 1023/0 is visible.
Motion is an explanatory schematic, never a CPU or SRAM execution trace.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw

from scripts.visual_style import (
    AMBER, BG, BLUE, CYAN, FG, GREEN, LINE, MUTED, PANEL,
    card, curve, ease, font, footer, glow, scene, txt,
)
from src import phase_ring as ring

ROOT = Path(__file__).resolve().parents[1]
DURATION = 18.0
CASES = ((1023, 1, 1024), (750, 400, 1024), (1500, 800, 2048))
PREVIEW_TIMES = (0.4, 2.2, 5.3, 8.7, 17.1)
POSTER_TIME = 11.35
CX, CY, RADIUS = 596.0, 570.0, 230.0


@lru_cache(maxsize=3)
def _example(a, b, n):
    final = int(ring.add(np.array([a], dtype=np.uint16),
                         np.array([b], dtype=np.uint16), n)[0])
    return dict(a=a, b=b, n=n, final=final,
                sine_q15=int(ring.make_lut(n)[final, 1]))


def state(t):
    """Return the exact discrete arithmetic currently illustrated on screen."""
    t = max(0.0, min(float(t), DURATION - 1e-8))
    case = min(2, int(t // 6.0))
    local = t - 6.0 * case
    v = dict(_example(*CASES[case]))
    p = ease((local - 0.85) / 2.50)
    steps = min(v['b'], int(math.floor(v['b'] * p + 1e-9)))
    full = v['a'] + steps
    v.update(case=case, local=local, progress=p, steps=steps,
             full=full, position=full & (v['n'] - 1), laps=full // v['n'])
    assert v['position'] == (full % v['n'])
    return v


def _center(d, x, y, text, size, color=FG, bold=True):
    text = str(text)
    width = d.textlength(text, font=font(size, bold))
    txt(d, (x - width / 2, y), text, size, color, bold)


def _point(index, n, radius=RADIUS, cx=CX, cy=CY):
    angle = math.tau * index / n - math.pi / 2
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def _arc(d, start, end, n, color, radius=RADIUS, width=10):
    count = max(2, int(abs(end - start) / n * 220))
    curve(d, [_point(value, n, radius) for value in np.linspace(start, end, count)],
          color, width)


def _arrow(d, start, end, color=CYAN, width=6):
    d.line((*start, *end), fill=color, width=width)
    theta = math.atan2(end[1] - start[1], end[0] - start[0])
    d.polygon([end, (end[0] - 18 * math.cos(theta - .55), end[1] - 18 * math.sin(theta - .55)),
               (end[0] - 18 * math.cos(theta + .55), end[1] - 18 * math.sin(theta + .55))], fill=color)


def _ring(d, v):
    n, local = v['n'], v['local']
    d.ellipse((CX - RADIUS, CY - RADIUS, CX + RADIUS, CY + RADIUS),
              outline='#263d55', width=18)
    for k in range(32):
        index = k * n / 32
        p1, p2 = _point(index, n, RADIUS - 13), _point(index, n, RADIUS + 13)
        d.line((*p1, *p2), fill=MUTED if k % 8 == 0 else LINE,
               width=5 if k % 8 == 0 else 3)
    # Four exact landmark positions establish the scale of the full ring.
    for index, x, y in [(0, CX + 52, CY - RADIUS + 16),
                        (n // 4, CX + RADIUS + 84, CY - 29),
                        (n // 2, CX + 58, CY + RADIUS - 65),
                        (3 * n // 4, CX - RADIUS - 91, CY - 29)]:
        _center(d, x, y, index, 39, MUTED)
    if v['laps'] == 0:
        _arc(d, 0, v['a'], n, BLUE, radius=RADIUS - 10, width=8)
        _arc(d, v['a'], v['full'], n, CYAN, radius=RADIUS + 3, width=17)
    else:
        # The completed lap shrinks away; only the wrapped remainder stays lit.
        remaining = max(1, v['b'] - (n - v['a']))
        folded = (ease((local - 3.35) / .60) if v['b'] == n - v['a'] else
                  ease((v['steps'] - (n - v['a'])) / remaining))
        _arc(d, 0, v['position'], n, CYAN, radius=RADIUS + 3, width=17)
        fold_x = CX + (172 - CX) * folded
        fold_y = CY + (382 - CY) * folded
        fold_r = RADIUS + (46 - RADIUS) * folded
        d.ellipse((fold_x - fold_r, fold_y - fold_r,
                   fold_x + fold_r, fold_y + fold_r), outline=AMBER, width=5)
        if folded > .8:
            _center(d, fold_x, fold_y - 15, '1 lap', 24, AMBER)
    start = _point(v['a'], n, RADIUS - 10)
    d.ellipse((start[0] - 10, start[1] - 10, start[0] + 10, start[1] + 10), fill=BLUE)
    tip = _point(v['position'], n, RADIUS + 3)
    _arrow(d, (CX, CY), tip, CYAN, 9)
    glow(d, tip, 13, CYAN)
    # A quiet center keeps the integer position dominant over the radial line.
    d.ellipse((CX - 140, CY - 117, CX + 140, CY + 123), fill=PANEL)
    _center(d, CX, CY - 99, v['position'], 103, CYAN)
    _center(d, CX, CY + 28, 'position', 35, MUTED)
    return tip


def _zoom_boundary(d, v):
    """An explicitly magnified local view; spacing is not the full-ring angle."""
    _center(d, 597, 831, 'Close-up of the wrap', 29, MUTED)
    positions = [1021, 1022, 1023, 0, 1, 2]
    centers = [156 + i * 176 for i in range(6)]
    d.line((centers[0] - 37, 898, centers[-1] + 37, 898), fill=LINE, width=7)
    for x, number in zip(centers, positions):
        active = number == v['position']
        card(d, (x - 73, 868, x + 73, 948), CYAN if active else LINE,
             radius=16, fill='#163d49' if active else PANEL)
        _center(d, x, 873, number, 48, CYAN if active else MUTED)
    if .85 < v['local'] < 3.35:
        p = v['progress']
        # This +1 marker travels between two discrete sites; the central state
        # changes only when that one whole increment has been completed.
        x = centers[2] + (centers[3] - centers[2]) * p
        y = 841 - math.sin(math.pi * p) * 42
        card(d, (x - 37, y - 28, x + 37, y + 29), CYAN,
             radius=14, fill='#164d58')
        _center(d, x, y - 25, '+1', 37, FG)


def _fetch(im, d, v, tip):
    local = v['local']
    arrived = local >= 4.55
    opened = ease((local - 4.55) / .55)
    card(d, (1176, 241, 1856, 956), CYAN if arrived else LINE, radius=30)
    _center(d, 1516, 268, 'Stored answers', 46, CYAN)
    _center(d, 1516, 355, 'Position', 34, MUTED)
    _center(d, 1516, 399, v['final'] if arrived else '—', 104,
            CYAN if arrived else LINE)
    # A broad drawer opens after the exact address token has arrived.
    slot_top = 551
    d.rounded_rectangle((1234, slot_top, 1798, 811), radius=22,
                        fill='#08121f', outline=LINE, width=3)
    if opened > 0:
        _center(d, 1516, 594, f'{v["sine_q15"]:+,d}', 90, FG)
        _center(d, 1516, 711, 'Q15 sine value', 34, MUTED)
    lid_y = slot_top + 260 * opened
    if opened < 1:
        d.rounded_rectangle((1234, lid_y, 1798, 811), radius=20,
                            fill='#183246', outline=CYAN if arrived else LINE, width=3)
        if opened < .30:
            _center(d, 1516, lid_y + 92, 'Choose a position', 40, MUTED)
    if arrived:
        _center(d, 1516, 861, 'Same stored value. Exact address.', 28, MUTED)
    if local >= 3.55:
        p = ease((local - 3.55) / 1.0)
        end = (1516, 426)
        control = (1034, 223)
        qx = (1 - p) ** 2 * tip[0] + 2 * (1 - p) * p * control[0] + p ** 2 * end[0]
        qy = (1 - p) ** 2 * tip[1] + 2 * (1 - p) * p * control[1] + p ** 2 * end[1]
        if p < 1:
            card(d, (qx - 62, qy - 42, qx + 62, qy + 42), CYAN,
                 radius=20, fill='#164d58')
            _center(d, qx, qy - 41, v['final'], 61, FG)


def frame(t, study=None):
    """Return an 18-second, 1920×1080 RGB explanatory frame."""
    v = state(t)
    title = 'Back to the start' if v['local'] < 3.55 else 'That position selects a stored answer'
    im, d = scene('LOOPED POSITIONS / THREE EXACT EXAMPLES', title,
                  'Illustrative replay of integer steps. No CPU duration or physical memory timing is represented.')
    card(d, (64, 241, 1138, 972), CYAN, radius=30)
    txt(d, (91, 251), f'{v["case"] + 1} / 3', 30, MUTED, True)
    _center(d, 615, 253, f'Start {v["a"]:,}  ·  move {v["b"]:,} step' + ('s' if v['b'] != 1 else ''),
            39, FG)
    tip = _ring(d, v)
    if v['case'] == 0:
        _zoom_boundary(d, v)
    else:
        _center(d, 608, 878, f'{v["steps"]:,} of {v["b"]:,} steps moved', 42,
                CYAN if v['steps'] == v['b'] else MUTED)
        _center(d, 608, 936, f'{v["n"]:,} positions around the ring', 29, MUTED)
    _fetch(im, d, v, tip)
    footer(d, 'A full lap returns to zero. The remaining position chooses the actual stored sine word.',
           'Exact floor/modular reference model; Q15 values are reused from the existing LUT. Motion is explanatory.')
    return im.convert('RGB')


def preview(folder=None):
    folder = Path(folder) if folder else ROOT.parents[1] / 'work/story_wrap_qa'
    folder.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGB', (1440, 1215), BG)
    for i, t in enumerate(PREVIEW_TIMES):
        im = frame(t)
        im.save(folder / f'wrap_{i}_{t:.2f}.png')
        small = im.resize((720, 405), Image.Resampling.LANCZOS)
        small.save(folder / f'wrap_{i}_{t:.2f}_720.png')
        sheet.paste(small, ((i % 2) * 720, (i // 2) * 405))
    sheet.save(folder / 'contact.png')
    frame(POSTER_TIME).resize((720, 405), Image.Resampling.LANCZOS).save(folder / 'poster_720.png')
    return folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    print(preview(args.preview_dir))
