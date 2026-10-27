"""Exact bit/add/register/address replay; no physical SRAM timing is implied.

The source RTL stores one signed-Q15 sine channel. Cosine and complex output
below are explicitly marked as the existing paired-LUT software extension.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw

from scripts.visual_style import (
    AMBER, BG, BLUE, CYAN, FG, GREEN, LINE, MUTED, PANEL,
    card, ease, font, footer, glow, scene, txt,
)
from src import phase_ring as ring

ROOT = Path(__file__).resolve().parents[1]
DURATION = 18.0
CASES = ((1023, 1, 1024), (750, 400, 1024), (1500, 800, 2048))
PREVIEW_TIMES = (0.45, 1.75, 3.45, 4.65, 11.5, 17.5)
POSTER_TIME = 11.4
PITCH = 65
CELL_W, CELL_H = 52, 64
RIGHT = 1144
ROW_A, ROW_B, ROW_SUM, ROW_REG = 334, 430, 557, 704


@lru_cache(maxsize=2)
def _lut(n):
    return ring.make_lut(n)


def ripple_trace(a, b, bits):
    """Return the real LSB-first full-adder state, including the final carry."""
    trace = []
    carry = 0
    for bit in range(bits):
        aa, bb = (a >> bit) & 1, (b >> bit) & 1
        total = aa + bb + carry
        trace.append(dict(bit=bit, a=aa, b=bb, carry_in=carry,
                          sum=total & 1, carry_out=total >> 1))
        carry = total >> 1
    return trace, carry


def case_values(a, b, n):
    """Numerical contract used by the renderer and independent validators."""
    bits = n.bit_length() - 1
    trace, carry = ripple_trace(a, b, bits)
    index = sum(row['sum'] << row['bit'] for row in trace)
    expected = int(ring.add(np.array([a], dtype=np.uint16),
                            np.array([b], dtype=np.uint16), n)[0])
    assert index == expected == ((a + b) & (n - 1))
    assert (a + b) == (carry << bits) + index
    word = _lut(n)[index]
    z = ring.decode(np.array([index], dtype=np.uint16), _lut(n))[0]
    return dict(a=a, b=b, n=n, bits=bits, trace=trace, carry=carry,
                full_sum=a + b, index=index, sine_q15=int(word[1]),
                cosine_q15=int(word[0]), output=complex(z))


def _x(bit):
    return RIGHT - CELL_W - bit * PITCH


def _bit(d, bit, value, y, color, active=False, x=None, scale=1):
    x = _x(bit) if x is None else x
    h, w = CELL_H * scale, CELL_W * scale
    fill = '#173f50' if active else '#101c30'
    card(d, (x, y, x + w, y + h), color if active else LINE,
         radius=8, fill=fill)
    if value is not None:
        txt(d, (x + 14 * scale, y + 6 * scale), value,
            int(39 * scale), color, True, mono=True)
    return x + w / 2, y + h / 2


def _arrow(d, start, end, color, width=3):
    d.line((*start, *end), fill=color, width=width)
    theta = math.atan2(end[1] - start[1], end[0] - start[0])
    points = [end]
    for offset in (-0.50, 0.50):
        points.append((end[0] - 11 * math.cos(theta + offset),
                       end[1] - 11 * math.sin(theta + offset)))
    d.polygon(points, fill=color)


def _path_point(points, progress):
    lengths = [math.dist(a, b) for a, b in zip(points[:-1], points[1:])]
    target = min(1.0, max(0.0, progress)) * sum(lengths)
    for i, length in enumerate(lengths):
        if target <= length or i == len(lengths) - 1:
            frac = target / max(length, 1e-9)
            return (points[i][0] + frac * (points[i + 1][0] - points[i][0]),
                    points[i][1] + frac * (points[i + 1][1] - points[i][1]))
        target -= length
    return points[-1]


def _stage(local):
    if local < 0.80:
        return '1 / LOAD PHASE INDICES'
    if local < 2.95:
        return '2 / ADD FROM LSB TO MSB'
    if local < 3.75:
        return '3 / KEEP THE REGISTER WIDTH'
    if local < 4.65:
        return '4 / ROUTE THE RETAINED ADDRESS'
    return '5 / READ THE ADDRESSED Q15 WORD'


def _memory(d, v, selected):
    """An explicitly bounded address window, never a fictional physical layout."""
    card(d, (1200, 263, 1856, 833), CYAN if selected else LINE)
    txt(d, (1224, 278), 'SRAM SINE LUT', 35, CYAN, True)
    start = (v['index'] // 64) * 64
    txt(d, (1225, 322), f'Address window {start}–{start + 63} / {v["n"]} words',
        24, MUTED)
    chosen = None
    for offset in range(64):
        address = start + offset
        x, y = 1225 + (offset % 8) * 75, 368 + (offset // 8) * 36
        active = selected and address == v['index']
        card(d, (x, y, x + 64, y + 29), CYAN if active else LINE,
             radius=4, fill='#1a555d' if active else PANEL)
        text = str(address)
        fw = d.textlength(text, font=font(22, True, True))
        txt(d, (x + (64 - fw) / 2, y + 1), text, 22,
            FG if active else '#61758f', True, mono=True)
        if address == v['index']:
            chosen = (x + 32, y + 14.5)
    txt(d, (1225, 685), f'ADDRESS  {v["index"]}' if selected else 'ADDRESS  —',
        33, CYAN if selected else MUTED, True)
    read = selected
    txt(d, (1225, 742), f'SIN Q15  {v["sine_q15"]:+d}' if read else 'SIN Q15  —',
        40, FG if read else MUTED, True)
    txt(d, (1227, 797), f'16-bit word 0x{v["sine_q15"] & 65535:04X}' if read
        else '16-bit signed output word', 24, MUTED)
    return chosen


def _outputs(d, v, visible):
    card(d, (64, 854, 1856, 976), CYAN if visible else LINE)
    columns = [(92, 'WRAPPED INDEX', str(v['index']), CYAN),
               (426, 'SINE Q15 / RTL WORD', f'{v["sine_q15"]:+d}', CYAN),
               (913, 'SOFTWARE COS Q15', f'{v["cosine_q15"]:+d}', GREEN),
               (1368, 'SOFTWARE COMPLEX64',
                f'{v["output"].real:+.5f} {v["output"].imag:+.5f}j', FG)]
    for x, label, value, color in columns:
        txt(d, (x, 864), label, 24, MUTED, True)
        txt(d, (x, 900), value if visible else '—',
            37 if x > 1300 else 48, color if visible else LINE, True,
            mono=x > 1300, width=460 if x > 1300 else 450)


def bit_lut(t, study=None):
    """Return an 18-second 1920×1080 RGB schematic in three six-second cases."""
    t = max(0.0, min(float(t), DURATION - 1e-7))
    case = min(2, int(t // 6))
    local = t - 6 * case
    v = case_values(*CASES[case])
    bits, n = v['bits'], v['n']
    im, d = scene('TECHNICAL MODEL / ACTUAL BITS, ADDRESSES AND Q15 VALUES',
                  f'Add. Keep {bits} bits. Read a word.',
                  'Schematic motion and editorial clock; no gate delay, SRAM timing or physical chip activity is measured')
    txt(d, (66, 207), f'{case + 1:02d} / 03   Z{n}', 30, MUTED, True)
    txt(d, (520, 207), _stage(local), 31, CYAN, True)
    txt(d, (1400, 207), f'{v["a"]} + {v["b"]} = {v["index"]} mod {n}',
        29, FG, True, width=460)
    card(d, (64, 263, 1166, 833), CYAN)
    # The largest visual elements are actual 10/11-bit operands and their sum.
    for y, key, label in [(ROW_A, 'a', 'INPUT A'), (ROW_B, 'b', 'INPUT B')]:
        txt(d, (88, y + 1), label, 28, MUTED, True)
        txt(d, (88, y + 36), str(v[key]), 38, BLUE, True)
    txt(d, (88, ROW_SUM - 2), 'FULL SUM', 27, MUTED, True)
    txt(d, (88, ROW_SUM + 34), str(v['full_sum']) if local >= 2.95 else '…',
        36, FG if local >= 2.95 else MUTED, True)
    txt(d, (88, ROW_REG - 1), f'{bits}-BIT', 29, CYAN, True)
    txt(d, (88, ROW_REG + 37), 'REGISTER', 29, CYAN, True)
    # Bit positions make register width explicit without suggesting uint16 wrap.
    for bit in range(bits):
        txt(d, (_x(bit) + 13, 294), f'b{bit}', 21, MUTED, mono=True)
        for y, key in [(ROW_A, 'a'), (ROW_B, 'b')]:
            delay = (bits - 1 - bit) * 0.015
            load = ease((local - delay) / 0.55)
            yy = y - 48 * (1 - load)
            if local > delay:
                _bit(d, bit, (v[key] >> bit) & 1, yy, BLUE)
    # A real LSB-first ripple trace controls visible sum bits and carry motion.
    phase = max(0.0, min(float(bits), (local - 0.80) / 2.15 * bits))
    done = min(bits, int(phase))
    active = done if 0.80 <= local < 2.95 else None
    fraction = phase - int(phase)
    for bit in range(bits + 1):
        known = bit < done or (bit == bits and done == bits)
        value = (v['full_sum'] >> bit) & 1 if known else None
        color = AMBER if bit == bits else CYAN
        _bit(d, bit, value, ROW_SUM, color)
    if active is not None and active < bits:
        row = v['trace'][active]
        for yy in (ROW_A, ROW_B):
            _bit(d, active, (v['a' if yy == ROW_A else 'b'] >> active) & 1,
                 yy, BLUE, active=True)
        cx = _x(active) + CELL_W / 2
        _arrow(d, (cx, ROW_B + CELL_H + 4), (cx, ROW_SUM - 8), CYAN, 4)
        if fraction > 0.45:
            _bit(d, active, row['sum'], ROW_SUM, CYAN, active=True)
        txt(d, (88, 505), f'BIT {active}', 26, CYAN, True)
        txt(d, (88, 643), f'{row["a"]} + {row["b"]} + {row["carry_in"]} → {row["carry_out"]}{row["sum"]}',
            27, FG, True, mono=True)
        next_x = _x(active + 1) + CELL_W / 2
        _arrow(d, (cx, 522), (next_x, 522),
               AMBER if row['carry_out'] else LINE, 4)
        px = cx + (next_x - cx) * ease((fraction - 0.50) / 0.50)
        if fraction > 0.50:
            glow(d, (px, 522), 4, AMBER if row['carry_out'] else LINE)
            txt(d, (px - 9, 487), str(row['carry_out']), 24,
                AMBER if row['carry_out'] else MUTED, True, mono=True)
    if local >= 2.95:
        # Retained bits physically translate from the full sum into the register.
        for bit in range(bits):
            p = ease((local - 2.95 - (bits - 1 - bit) * 0.018) / 0.52)
            yy = ROW_SUM + (ROW_REG - ROW_SUM) * p
            _bit(d, bit, (v['index'] >> bit) & 1, yy, CYAN, active=True)
        # Only the upper carry leaves the fixed-width register; its value is real.
        p = ease((local - 2.97) / 0.72)
        cx = _x(bits)
        _arrow(d, (cx + 25, ROW_SUM - 6), (cx - 95, 476), AMBER, 3)
        _bit(d, bits, v['carry'], ROW_SUM - 85 * p, AMBER,
             active=True, x=cx - 116 * p)
        if local >= 3.20:
            txt(d, (88, 643), 'DROP CARRY', 27, AMBER, True)
    selected = local >= 4.65
    target = _memory(d, v, selected)
    if local >= 3.70:
        # Parallel retained bits share one logical address bus. This is routing,
        # not a serialized memory protocol, physical bus layout or cycle model.
        bus = max(0.0, min(1.0, (local - 3.70) / 0.95))
        for bit in range(bits):
            sx = _x(bit) + CELL_W / 2
            route = [(sx, ROW_REG + CELL_H + 5), (sx, 804),
                     (1180, 804), (1180, target[1]), target]
            d.line(route, fill='#173343', width=2, joint='curve')
            if bus < 1:
                px, py = _path_point(route, bus)
                d.rounded_rectangle((px - 11, py - 14, px + 11, py + 14),
                                    radius=4, fill='#164957', outline=CYAN, width=1)
                txt(d, (px - 7, py - 14), str((v['index'] >> bit) & 1),
                    22, FG, True, mono=True)
        if selected:
            # Outline the addressed word; a centered particle would hide its
            # actual address precisely when the viewer should inspect it.
            tx, ty = target
            d.rounded_rectangle((tx - 35, ty - 18, tx + 35, ty + 18),
                                radius=5, outline=FG, width=3)
    # Read data follows the addressed cell, not an independently animated value.
    if local >= 4.65:
        route = [target, (1828, target[1]), (1828, 824), (700, 824), (700, 854)]
        read = ease((local - 4.65) / 0.60)
        d.line(route, fill=CYAN, width=3, joint='curve')
        px, py = _path_point(route, read)
        if read < 1:
            card(d, (px - 66, py - 22, px + 66, py + 22), CYAN, radius=6,
                 fill='#163c4b')
            txt(d, (px - 53, py - 18), f'0x{v["sine_q15"] & 65535:04X}',
                28, FG, True, mono=True)
    _outputs(d, v, local >= 5.25)
    footer(d, 'Fixed-width addition selects the actual sine word. Motion is a schematic replay, not a physical SRAM measurement.',
           'RTL: one signed-Q15 sine channel. Software extension: paired cosine/sine LUT and complex64 restoration.')
    return im


def preview(output=None):
    folder = Path(output) if output else ROOT.parents[1] / 'work/bit_lut_v5_qa'
    folder.mkdir(parents=True, exist_ok=True)
    thumbnails = []
    for index, t in enumerate(PREVIEW_TIMES):
        frame = bit_lut(t)
        frame.save(folder / f'phase_bits_to_lut_{index}_{t:.2f}.png')
        thumbnails.append(frame.resize((960, 540), Image.Resampling.LANCZOS))
    sheet = Image.new('RGB', (1920, 1620), BG)
    for i, thumbnail in enumerate(thumbnails):
        sheet.paste(thumbnail, ((i % 2) * 960, (i // 2) * 540))
    sheet.save(folder / 'contact.png')
    bit_lut(POSTER_TIME).resize((720, 405), Image.Resampling.LANCZOS).save(folder / 'poster_720.png')
    return folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-only', action='store_true', help='Generate six review frames and a 720-pixel poster.')
    parser.add_argument('--output', help='Review-frame directory; no existing media are overwritten.')
    args = parser.parse_args()
    print(preview(args.output))
