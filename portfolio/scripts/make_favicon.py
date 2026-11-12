"""Draw the site icon: a DNA double helix on a dark rounded square.

Two strands follow x = cx + R*sin(t + phase), with phase 0 and pi, along a
straight axis that is tilted a little. Where a strand is behind the axis
(cos(t + phase) < 0) it is drawn first, in a darker colour; the parts in front
are drawn last, in a light colour. Base pairs are short rungs between the
strands, each split in two colours (one base from each strand).

Run from portfolio/:  python3 scripts/make_favicon.py [d|e]  -> img/favicon-dna.svg
Then:  rsvg-convert -w 180 img/favicon-dna.svg -o img/apple-touch-icon-dna.png
"""

import math
import sys
from pathlib import Path

SIZE = 64
BG = "#2c3e50"
STRAND_FRONT = ("#5fd3d9", "#6cb8f0")   # strand 1, strand 2 in front of the axis
STRAND_BACK = ("#2b8a92", "#2f6fa8")    # the same strands behind the axis
RUNG = ("#5fd3d9", "#6cb8f0")           # the two halves of a base pair
VARIANTS = {
    # d: the site icon (diagonal, like the DNA emoji); e: an upright alternative
    "d": dict(tilt=-28, turns=1.5, r=12, length=54, w=4.6, rungs=3, rung_op=1.0),
    "e": dict(tilt=0, turns=1.5, r=14, length=48, w=4.6, rungs=3, rung_op=1.0),
}


def build(v):
    cx = cy = SIZE / 2
    a = math.radians(v["tilt"])
    ux, uy = math.sin(-a), math.cos(-a)   # axis direction (down the helix)
    px, py = math.cos(-a), -math.sin(-a)  # sideways direction (across the helix)
    tmax = 2 * math.pi * v["turns"]
    steps = 240

    def at(t, phase):
        s = (t / tmax - 0.5) * v["length"]          # position along the axis
        off = v["r"] * math.sin(t + phase)          # sideways offset
        return cx + ux * s + px * off, cy + uy * s + py * off, math.cos(t + phase)

    def runs(phase):
        """Split one strand into pieces that are all in front or all behind."""
        out, cur, front = [], [], None
        for i in range(steps + 1):
            t = tmax * i / steps
            x, y, z = at(t, phase)
            f = z >= 0
            if front is None or f == front:
                cur.append((x, y))
            else:
                cur.append((x, y))
                out.append((front, cur))
                cur = [(x, y)]
            front = f
        out.append((front, cur))
        return out

    def path(pts):
        return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts)

    w = v["w"]
    back, front = [], []
    for k, phase in enumerate((0.0, math.pi)):
        for is_front, pts in runs(phase):
            col = STRAND_FRONT[k] if is_front else STRAND_BACK[k]
            el = (f'<path d="{path(pts)}" fill="none" stroke="{col}" stroke-width="{w}" '
                  f'stroke-linecap="round" stroke-linejoin="round"/>')
            (front if is_front else back).append(el)

    # Base pairs: evenly spaced, skipping the points where the strands cross.
    rungs = []
    n = int(round(v["turns"] * 2 * v["rungs"]))
    for i in range(n):
        t = tmax * (i + 0.5) / n
        x1, y1, _ = at(t, 0.0)
        x2, y2, _ = at(t, math.pi)
        if math.hypot(x2 - x1, y2 - y1) < 2.2 * w:
            continue
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        for (xa, ya), col in (((x1, y1), RUNG[0]), ((x2, y2), RUNG[1])):
            rungs.append(f'<line x1="{xa:.2f}" y1="{ya:.2f}" x2="{mx:.2f}" y2="{my:.2f}" '
                         f'stroke="{col}" stroke-width="{w * 0.55:.2f}" stroke-linecap="round" opacity="{v.get('rung_op', 0.8)}"/>')

    body = "\n  ".join(back + rungs + front)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}">\n'
            f'  <rect width="{SIZE}" height="{SIZE}" rx="14" fill="{BG}"/>\n'
            f'  <clipPath id="c"><rect x="3" y="3" width="{SIZE - 6}" height="{SIZE - 6}" rx="11"/></clipPath>\n'
            f'  <g clip-path="url(#c)">\n  {body}\n  </g>\n</svg>\n')


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "d"
    out = Path(__file__).resolve().parent.parent / "img" / "favicon-dna.svg"
    if len(sys.argv) > 2:
        out = Path(sys.argv[2])
    out.write_text(build(VARIANTS[name]), encoding="utf-8")
    print(f"wrote {out} (variant {name})")


if __name__ == "__main__":
    main()
