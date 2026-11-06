"""Draw the decorative Manhattan-plot skyline used behind the hero banner.

It is decoration, not data: 22 "chromosomes" of random points with a few peaks,
in two alternating teal and blue tones. A fixed seed keeps the picture the same
on every run.

Run from portfolio/:  python3 scripts/make_hero_art.py   -> img/hero_manhattan.svg
"""

import math
import random
from pathlib import Path

W, H = 1200, 260
N_CHR = 22
POINTS_PER_CHR = 90
PEAKS = {3: 0.92, 7: 0.55, 11: 0.78, 16: 0.48, 19: 0.66}  # chromosome -> peak height (0-1)
COLOURS = ("#4ec0c6", "#5dade2")

random.seed(7)


def main():
    dots = []
    chr_w = W / N_CHR
    for c in range(N_CHR):
        colour = COLOURS[c % 2]
        peak = PEAKS.get(c)
        centre = c * chr_w + chr_w * random.uniform(0.35, 0.65)
        for _ in range(POINTS_PER_CHR):
            x = c * chr_w + random.uniform(2, chr_w - 2)
            # background points: mostly low, exponential tail like -log10(p) under the null
            h = random.expovariate(6.0)
            if peak and abs(x - centre) < chr_w * 0.18:
                # points near a peak rise in a narrow bell shape
                h = max(h, peak * math.exp(-((x - centre) / (chr_w * 0.07)) ** 2) * random.uniform(0.55, 1.0))
            h = min(h, 0.97)
            y = H - 8 - h * (H - 20)
            r = 2.6 if h > 0.3 else 2.0
            dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{colour}"/>')
    threshold = H - 8 - 0.42 * (H - 20)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice">'
        f'<line x1="0" y1="{threshold:.1f}" x2="{W}" y2="{threshold:.1f}" stroke="#ffffff" '
        f'stroke-opacity="0.35" stroke-width="1.2" stroke-dasharray="6 6"/>'
        + "".join(dots)
        + "</svg>"
    )
    out = Path(__file__).resolve().parent.parent / "img" / "hero_manhattan.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(dots)} points)")


if __name__ == "__main__":
    main()
