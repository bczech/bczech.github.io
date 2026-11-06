"""Draw the site icon: an alpha helix (protein ribbon) on a dark rounded square.

The helix is a parametric coil x = r*cos(t), y = pitch*t, z = r*sin(t),
projected on the screen and drawn as a flat band (the "cartoon" ribbon used by
PyMOL or ChimeraX). Band segments behind the axis (z < 0) are drawn first in a
darker colour (the inner face of the ribbon), segments in front on top in a
light colour. The whole helix is tilted a little.

Run from portfolio/:  python3 scripts/make_favicon.py   -> img/favicon.svg
"""

import math
from pathlib import Path

SIZE = 64
BG = "#2c3e50"
BACK = "#23757b"   # inner face of the ribbon, behind the axis
FRONT = "#5fd3d9"  # outer face, in front of the axis
WIDTH = 7.5         # ribbon width in px
TILT = -18          # degrees
TURNS = 3.25
R = 15             # helix radius in px
TOP, BOTTOM = 13, 51
STEPS = 360


def point(t):
    y = TOP + (BOTTOM - TOP) * t / (2 * math.pi * TURNS)
    x = SIZE / 2 + R * math.cos(t)
    z = math.sin(t)
    return x, y, z


def segments(front):
    """Split the coil into continuous runs that are all in front or all behind."""
    runs, cur = [], []
    for i in range(STEPS + 1):
        t = 2 * math.pi * TURNS * i / STEPS
        x, y, z = point(t)
        if (z >= 0) == front:
            cur.append((x, y, t))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def half_width(t):
    """Half of the ribbon width; narrows to a thin loop over the first and last 0.45 turn."""
    t_end = 2 * math.pi * TURNS
    ramp = 2 * math.pi * 0.45
    k = min(1.0, t / ramp, (t_end - t) / ramp)
    k = 0.5 - 0.5 * math.cos(math.pi * max(k, 0.0))  # smooth step
    return (0.9 + (WIDTH - 0.9) * k) / 2


def band(run):
    """Closed polygon: upper edge left to right, lower edge back."""
    top = [(x, y - half_width(t)) for x, y, t in run]
    bottom = [(x, y + half_width(t)) for x, y, t in reversed(run)]
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in top + bottom) + "Z"


def main():
    back = "".join(f'<path d="{band(r)}"/>' for r in segments(False))
    front = "".join(f'<path d="{band(r)}"/>' for r in segments(True))
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}">'
        f'<rect width="{SIZE}" height="{SIZE}" rx="14" fill="{BG}"/>'
        f'<g transform="rotate({TILT} {SIZE / 2} {SIZE / 2})" stroke-linejoin="round">'
        f'<g fill="{BACK}" stroke="{BACK}" stroke-width="0.6">{back}</g>'
        f'<g fill="{FRONT}" stroke="{BG}" stroke-width="0.8">{front}</g>'
        "</g></svg>"
    )
    out = Path(__file__).resolve().parent.parent / "img" / "favicon.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
