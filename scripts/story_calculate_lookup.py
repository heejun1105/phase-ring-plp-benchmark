"""A simple calculate-versus-lookup story, with genuine phase-model outputs.

Clock faces and moving cards explain a representation choice. All scene timing
is editorial and shared between routes; it does not encode CPU or chip latency.
This new renderer does not write or replace existing media or measurements.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw

from scripts.visual_style import (
    BG, PANEL, LINE, FG, MUTED, BLUE, CYAN, GREEN, AMBER,
    background, card, curve, ease, font, glow, txt, wire,
)
from src import conventional as conventional
from src import phase_ring as ring

ROOT = Path(__file__).resolve().parents[1]
DURATION = 16.0


@lru_cache(maxsize=1)
def example():
    """Shared raw angles, actual floor indices, and decoded signed-Q15 word."""
    n = 1024
    a, b = (750.25 / n) * math.tau, (400.25 / n) * math.tau
    qa, qb = ring.quantize(np.array([a, b]), n)
    address = int(ring.add(np.array([qa]), np.array([qb]), n)[0])
    lut = ring.make_lut(n)
    stored = ring.decode(np.array([address]), lut)[0]
    calculated = conventional.end_to_end(np.array([a]), np.array([b]))[0]
    angle = lambda z: math.atan2(float(z.imag), float(z.real))
    gap = abs(math.degrees(math.remainder(angle(stored) - angle(calculated), math.tau)))
    return dict(n=n, a=a, b=b, qa=int(qa), qb=int(qb), address=address,
        q15=tuple(int(x) for x in lut[address]), stored=stored,
        calculated=calculated, angle_gap_deg=gap)


def _center(d, x, y, value, size=48, color=FG, bold=False, mono=False):
    f = font(size, bold, mono)
    length = d.textlength(str(value), font=f)
    d.text((x - length / 2, y), str(value), fill=color, font=f)


def _clock_point(cx, cy, radius, angle):
    # Clock-style display: zero is at the top and increasing phase is clockwise.
    # This display convention changes no arithmetic or waveform values.
    return cx + radius * math.sin(angle), cy - radius * math.cos(angle)


def _clock(d, cx, cy, radius, angle, color, numbered=False, number=None):
    d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill='#0b1728', outline=LINE, width=5)
    for j in range(48):
        theta = j * math.tau / 48
        start = _clock_point(cx, cy, radius-8, theta)
        end = _clock_point(cx, cy, radius+3, theta)
        d.line((*start, *end), fill=MUTED if j % 12 == 0 else LINE, width=3)
    if numbered:
        for j, text in enumerate(['0', '256', '512', '768']):
            pos = _clock_point(cx, cy, radius+35, j*math.tau/4)
            _center(d, pos[0], pos[1]-22, text, 40, MUTED, True, True)
    end = _clock_point(cx, cy, radius-18, angle)
    d.line((cx, cy, *end), fill=color, width=11 if radius > 130 else 8)
    glow(d, end, 7, color)
    glow(d, (cx, cy), 5, color)
    if number is not None:
        _center(d, cx, cy+radius+14, number, 48, color, True, True)


def _wave(d, box, z, color, t, progress=1.0):
    x, y, w, h = box
    d.line((x, y+h/2, x+w, y+h/2), fill=LINE, width=2)
    if progress <= 0:
        return
    xx = np.linspace(0, w, 240)
    values = np.imag(complex(z) * np.exp(1j*(xx/w*math.tau*1.5-t*1.9)))
    count = max(2, min(len(xx), int(len(xx)*progress)))
    yy = y+h/2-values*h*.38
    curve(d, zip(x+xx[:count], yy[:count]), color, 7)
    if progress >= .99:
        position = (t*.21) % 1
        value = np.imag(complex(z)*np.exp(1j*(position*math.tau*1.5-t*1.9)))
        glow(d, (x+w*position, y+h/2-value*h*.38), 7, color)


def _base(title, subtitle=None):
    im = background().copy()
    d = ImageDraw.Draw(im)
    txt(d, (64, 40 if subtitle else 55), title, 68 if subtitle else 72, FG, True, width=1790)
    if subtitle:
        txt(d, (68, 126), subtitle, 40, MUTED, width=1780)
    txt(d, (67, 1003), 'Unit-strength waves only  •  Illustration timing, not measured CPU or chip timing',
        32, MUTED, width=1790)
    return im, d


def _intro(t, e):
    im, d = _base('Store the answers once. Reuse them.', 'Same two angles')
    reveal = ease(t/2.0)
    for cx, label, angle, color in [(610, 'A', e['a'], BLUE), (1310, 'B', e['b'], GREEN)]:
        _center(d, cx, 239, label, 60, color, True)
        _clock(d, cx, 485, 174, angle*reveal, color)
        wire(d, [(cx, 679), (cx, 706), (960, 706)], color, t*.25)
    for box, text, color in [((160, 783, 880, 943), 'Calculate again', BLUE),
                              ((1040, 783, 1760, 943), 'Use a stored answer', CYAN)]:
        card(d, box, color, 26)
        _center(d, (box[0]+box[2])/2, 825, text, 56, color, True)
        wire(d, [(960, 706), ((box[0]+box[2])/2, 706), ((box[0]+box[2])/2, 783)], color, t*.25)
    return im


def _route_inputs(d, left, e):
    for offset, label, angle, color in [(246, 'A', e['a'], BLUE), (628, 'B', e['b'], GREEN)]:
        _center(d, left+offset, 314, label, 43, color, True)
        _clock(d, left+offset, 438, 83, angle, color)


def _routes(t, e):
    im, d = _base('Same input. Two routes.')
    card(d, (64, 226, 940, 961), BLUE, 26)
    card(d, (980, 226, 1856, 961), CYAN, 26)
    _center(d, 502, 251, 'Calculate again', 54, BLUE, True)
    _center(d, 1418, 251, 'Use a stored answer', 54, CYAN, True)
    _route_inputs(d, 64, e)
    _route_inputs(d, 980, e)
    p = max(0.0, min(1.0, (t-3.2)/7.3))
    for source_x, color in [(310, BLUE), (692, GREEN)]:
        wire(d, [(source_x, 521), (source_x, 557), (502, 557), (502, 587)], color, t*.20)
    # Each function tile handles both inputs. These are explanatory function
    # blocks, not CPU instruction counts or measured pipeline stages.
    for x, text, threshold in [(231, 'sin', .08), (518, 'cos', .24)]:
        card(d, (x, 587, x+255, 701), BLUE if p >= threshold else LINE, 20,
            '#183354' if p >= threshold else PANEL)
        _center(d, x+127, 599, text, 65, BLUE if p >= threshold else MUTED, True)
    for x in [359, 645]:
        wire(d, [(x, 701), (x, 742), (502, 742)], BLUE, t*.20)
    _center(d, 502, 727, '×', 80, BLUE if p >= .52 else MUTED, True)
    output_reveal = ease(max(0, min(1, (p-.76)/.16)))
    _wave(d, (146, 842, 712, 87), e['calculated'], BLUE, t, output_reveal)

    # These are actual floors of the raw angles, rather than invented labels.
    _center(d, 1418, 527,
        f"{e['qa']} + {e['qb']} → {e['address']}" if p >= .55 else f"{e['qa']} + {e['qb']}",
        48, FG, True, True)
    adding = ease(max(0, min(1, (p-.12)/.43)))
    dial_x, dial_y, radius = 1210, 719, 98
    phase = (e['qa'] + e['qb']*adding)/e['n']*math.tau
    _clock(d, dial_x, dial_y, radius, phase, CYAN)
    _center(d, dial_x, 671, '+', 68, CYAN, True)
    for source_x, color in [(1226, BLUE), (1608, GREEN)]:
        wire(d, [(source_x, 572), (source_x, 591), (dial_x, 591), (dial_x, 621)], color, t*.20)

    # Plain index cards represent the finite stored table, not a cache chip.
    # The selected card opens only after the addition has reached its real sum.
    opening = ease(max(0, min(1, (p-.55)/.20)))
    stack_x, stack_y = 1472, 613
    for delta in [2, 1]:
        card(d, (stack_x+delta*12, stack_y-delta*14, stack_x+300+delta*12, stack_y+177-delta*14), LINE, 17)
    front_w = 126+174*opening
    card(d, (stack_x, stack_y, stack_x+front_w, stack_y+190), CYAN if opening > .3 else LINE, 18,
        '#113237' if opening > .3 else PANEL)
    _center(d, stack_x+front_w/2, stack_y+5, e['address'] if opening > .3 else '…', 67,
        CYAN if opening > .3 else MUTED, True, True)
    if opening > .3:
        _wave(d, (stack_x+20, stack_y+100, max(20, front_w-40), 65), e['stored'], CYAN, t)
    wire(d, [(dial_x+radius+9, dial_y), (1413, dial_y), (1413, stack_y+95), (stack_x, stack_y+95)],
        CYAN, t*.20)
    _center(d, 1626, 797, 'Stored answers', 42, CYAN, True)
    _wave(d, (1044, 842, 712, 87), e['stored'], CYAN, t, output_reveal)
    return im


def _outputs(t, e):
    im, d = _base('The stored answer is an approximation.')
    for left, cx, label, z, color in [(64, 502, 'Calculated answer', e['calculated'], BLUE),
                                      (980, 1418, 'Stored answer', e['stored'], CYAN)]:
        card(d, (left, 226, left+876, 944), color, 26)
        _center(d, cx, 251, label, 54, color, True)
        angle = math.atan2(float(z.imag), float(z.real))
        _clock(d, cx, 504, 154, angle, color)
        _center(d, cx, 682, f'{math.degrees(angle):.4f}°', 49, color, True, True)
        _wave(d, (cx-354, 759, 708, 151), z, color, t)
    _center(d, 960, 930, f"{e['angle_gap_deg']:.4f}° difference", 48, AMBER, True)
    txt(d, (68, 1044), f"Z1024  •  Address {e['address']}  •  Signed Q15 word ({e['q15'][0]}, {e['q15'][1]})  •  Shared output scale and playback", 26,
        MUTED, width=1780)
    return im


def frame(t, study=None):
    """Raw RGB 1920x1080 frame; the caller manages final loop crossfades."""
    t = max(0.0, min(float(t), DURATION))
    e = example()
    if t < 3.2:
        return _intro(t, e)
    if t < 10.5:
        image = _routes(t, e)
        if t < 3.6:
            image = Image.blend(_intro(3.2, e), image, ease((t-3.2)/.4))
        return image.convert('RGB')
    image = _outputs(t, e)
    if t < 10.9:
        image = Image.blend(_routes(10.5, e), image, ease((t-10.5)/.4))
    return image.convert('RGB')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-dir', type=Path, default=ROOT.parents[1]/'work/story_calc_qa')
    args = parser.parse_args()
    args.preview_dir.mkdir(parents=True, exist_ok=True)
    for t in [.8, 4.2, 7.4, 10.0, 13.4]:
        picture = frame(t)
        picture.save(args.preview_dir/f'calculate_lookup_{t:04.1f}_1080.png')
        picture.resize((1280, 720), Image.Resampling.LANCZOS).save(args.preview_dir/f'calculate_lookup_{t:04.1f}_720.png')
    print({key: example()[key] for key in ['qa', 'qb', 'address', 'q15', 'angle_gap_deg']})
    print('Preview frames: '+str(args.preview_dir))


if __name__ == '__main__':
    main()
