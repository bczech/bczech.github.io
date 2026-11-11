"""Co-author network for research.qmd.

Builds an inline SVG from the author lists in data/publications.toml:
  - one dot per co-author, sized by the number of papers we share;
  - colour = collaboration circle (the `area` field of each paper);
  - grey lines join two co-authors who are on the same paper.
I am the fixed centre of the layout. My own links are not drawn (every dot would
have one), but they still act as weak springs, so each circle settles around me.

The force-directed layout (Fruchterman-Reingold) is computed here, in plain
Python with a fixed random seed. The same data always gives the same picture,
so a rebuild without new papers does not change the page.
"""

import html
import math
import random

ME = "Czech B"

# Collaboration circles in palette order. Three hues is the most a network
# (any two dots can be neighbours) can carry; the rest folds into grey "Other".
# Colours: validated categorical slots 1-3, light and dark steps (see portfolio.scss).
AREAS = [
    ("genomics", "Genomics, microbiome and transcriptomics"),
    ("drug", "Drug response (pharma R&D)"),
    ("virology", "Small RNA in virology"),
    ("other", "Other: feline reproduction"),
]
AREA_NAME = dict(AREAS)
GROUP_LABEL = {"genomics": "Genomics & microbiome", "drug": "Drug response",
               "virology": "Virology", "other": "Feline reproduction"}

W, H = 860, 540          # SVG coordinate space
PAD = 34                 # keep dots and labels inside the frame
LABEL_MIN_PAPERS = 3     # name labels only for the closest collaborators


def split_authors(s):
    return [a.strip() for a in s.split(",") if a.strip()]


def build_graph(pubs):
    """Return (nodes, edges, ties).

    nodes: name -> info; edges: (a, b) -> shared papers;
    ties: (a, b) -> layout strength. Each paper adds 1 / (co-authors - 1) to every
    pair on it (Newman's weighting), so a 20-author paper does not pull its
    authors into one tight ball, while people who keep writing together stay close.
    """
    nodes = {}
    edges = {}
    ties = {}
    for p in pubs:
        names = split_authors(p["authors"])
        if ME not in names:
            continue
        area = p.get("area", "other")
        for n in names:
            if n == ME:
                continue
            info = nodes.setdefault(n, {"papers": 0, "years": [], "areas": {}})
            info["papers"] += 1
            info["years"].append(p["year"])
            info["areas"][area] = info["areas"].get(area, 0) + 1
        others = sorted(n for n in names if n != ME)
        share = 1 / max(len(others) - 1, 1)
        for i, a in enumerate(others):
            for b in others[i + 1:]:
                edges[(a, b)] = edges.get((a, b), 0) + 1
                ties[(a, b)] = ties.get((a, b), 0) + share
    order = [k for k, _ in AREAS]
    for info in nodes.values():
        # Main circle = the one with most joint papers; ties go to the earlier slot.
        info["area"] = min(info["areas"], key=lambda k: (-info["areas"][k], order.index(k)))
        info["r"] = 4.5 + 2.6 * math.sqrt(info["papers"] - 1)
    return nodes, edges, ties


def layout(nodes, ties, iterations=600, seed=7):
    """Fruchterman-Reingold with me pinned at the centre, then overlap removal."""
    rnd = random.Random(seed)
    names = sorted(nodes)
    cx, cy = W / 2, H / 2
    # Start each circle in its own sector, so the result does not depend on luck.
    sector = {k: i for i, (k, _) in enumerate(AREAS)}
    pos = {}
    for n in names:
        ang = 2 * math.pi * (sector[nodes[n]["area"]] + 0.15 + 0.7 * rnd.random()) / len(AREAS)
        rad = 120 + 80 * rnd.random()
        pos[n] = [cx + rad * math.cos(ang), cy + rad * math.sin(ang)]
    springs = [(a, b, 2.2 * w) for (a, b), w in ties.items()]
    springs += [(n, ME, 0.10 * nodes[n]["papers"]) for n in names]
    pos[ME] = [cx, cy]
    k = 1.15 * math.sqrt((W - 2 * PAD) * (H - 2 * PAD) / (len(names) + 1))
    temp = W / 8
    for _ in range(iterations):
        disp = {n: [0.0, 0.0] for n in names}
        for i, a in enumerate(names):          # repulsion between all pairs
            ax, ay = pos[a]
            for b in names[i + 1:]:
                dx, dy = ax - pos[b][0], ay - pos[b][1]
                d2 = dx * dx + dy * dy + 0.01
                f = k * k / d2
                disp[a][0] += dx * f
                disp[a][1] += dy * f
                disp[b][0] -= dx * f
                disp[b][1] -= dy * f
        for a in names:                        # the centre dot (me) pushes too
            dx, dy = pos[a][0] - cx, pos[a][1] - cy
            d2 = dx * dx + dy * dy + 0.01
            f = 1.6 * k * k / d2
            disp[a][0] += dx * f
            disp[a][1] += dy * f
        for a, b, w in springs:                # attraction along edges
            dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
            d = math.sqrt(dx * dx + dy * dy) + 0.01
            f = 0.25 * w * d * d / k              # FR attraction d^2/k, weighted
            if a in disp:
                disp[a][0] -= dx / d * f
                disp[a][1] -= dy / d * f
            if b in disp:
                disp[b][0] += dx / d * f
                disp[b][1] += dy / d * f
        for n in names:
            dx, dy = disp[n]
            d = math.sqrt(dx * dx + dy * dy) + 0.01
            step = min(d, temp)
            pos[n][0] += dx / d * step
            pos[n][1] += dy / d * step
        temp = max(temp * 0.985, 0.6)
    fit(pos, nodes)
    separate(pos, nodes)
    fit(pos, nodes)
    return pos


def fit(pos, nodes):
    """Scale the layout (around me, at the centre) so that it fills the frame."""
    cx, cy = W / 2, H / 2
    sx = max(abs(p[0] - cx) + nodes.get(n, {"r": 8})["r"] for n, p in pos.items() if n != ME)
    sy = max(abs(p[1] - cy) + nodes.get(n, {"r": 8})["r"] for n, p in pos.items() if n != ME)
    s = min((W / 2 - PAD - 70) / sx, (H / 2 - PAD) / sy)  # 70 px spare for side labels
    for n, p in pos.items():
        p[0] = cx + (p[0] - cx) * s
        p[1] = cy + (p[1] - cy) * s


def separate(pos, nodes, gap=3.0, rounds=200):
    """Push overlapping dots apart, keeping a small gap between them (me stays put)."""
    r = {n: nodes[n]["r"] for n in nodes}
    r[ME] = 15
    names = sorted(pos)
    for _ in range(rounds):
        moved = False
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                dx, dy = pos[b][0] - pos[a][0], pos[b][1] - pos[a][1]
                d = math.sqrt(dx * dx + dy * dy) or 0.01
                need = r[a] + r[b] + gap
                if d < need:
                    push = (need - d) / 2
                    ux, uy = dx / d, dy / d
                    if a != ME:
                        pos[a][0] -= ux * push * (2 if b == ME else 1)
                        pos[a][1] -= uy * push * (2 if b == ME else 1)
                    if b != ME:
                        pos[b][0] += ux * push * (2 if a == ME else 1)
                        pos[b][1] += uy * push * (2 if a == ME else 1)
                    moved = True
        if not moved:
            break


def years(ys):
    lo, hi = min(ys), max(ys)
    return str(lo) if lo == hi else f"{lo}–{hi}"


def network_web(pubs):
    nodes, edges, ties = build_graph(pubs)
    pos = layout(nodes, ties)
    names = sorted(nodes)
    idx = {n: i for i, n in enumerate(names)}
    neigh = {n: set() for n in names}
    for a, b in edges:
        neigh[a].add(b)
        neigh[b].add(a)
    f = lambda v: f"{v:.1f}"

    out = ['<figure class="pf-chart pf-net">']
    out.append('<figcaption class="pf-chart-title">People I have published with</figcaption>')
    out.append('<ul class="pf-net-legend">' + "".join(
        f'<li><span class="pf-net-key pf-a-{k}"></span>{html.escape(v)}</li>' for k, v in AREAS) + "</ul>")
    total = len(names)
    out.append('<div class="pf-net-scroll">')
    out.append(
        f'<svg class="pf-chart-svg pf-net-svg" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Network of {total} co-authors, grouped into collaboration circles. '
        f'The table below lists the co-authors with two or more joint papers.">')
    out.append('<g class="pf-net-edges">')
    for n in names:  # faint spokes from me to everyone
        x, y = pos[n]
        out.append(f'<line class="pf-net-spoke" data-a="{idx[n]}" x1="{f(W / 2)}" y1="{f(H / 2)}" x2="{f(x)}" y2="{f(y)}"/>')
    for (a, b), w in sorted(edges.items()):
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        out.append(f'<line class="pf-net-edge" data-a="{idx[a]}" data-b="{idx[b]}" '
                   f'x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}"'
                   + (f' stroke-width="{1 + 0.5 * (w - 1):.1f}"' if w > 1 else "") + "/>")
    out.append("</g>")

    cx, cy = W / 2, H / 2
    # Circle labels: centred above the top dot of each circle.
    out.append('<g class="pf-net-groups">')
    for k, v in AREAS:
        members = [n for n in names if nodes[n]["area"] == k]
        if not members:
            continue
        short = GROUP_LABEL[k]
        half = 3.8 * len(short)  # rough half-width of the label at 12px
        mx = sum(pos[n][0] for n in members) / len(members)
        top = min(pos[n][1] - nodes[n]["r"] for n in members)
        lx = min(max(mx, 8 + half), W - 8 - half)
        ly = max(top - 10, 14)
        out.append(f'<text class="pf-net-group" x="{f(lx)}" y="{f(ly)}" text-anchor="middle">'
                   f'{html.escape(short)}</text>')
    out.append("</g>")

    out.append('<g class="pf-net-nodes">')
    for n in names:
        info = nodes[n]
        x, y = pos[n]
        papers = info["papers"]
        tip = (f"{n} · {papers} joint paper{'s' if papers > 1 else ''} ({years(info['years'])}) · "
               f"{AREA_NAME[info['area']]}")
        nb = " ".join(str(idx[m]) for m in sorted(neigh[n]))
        out.append(f'<g class="pf-net-node" data-i="{idx[n]}" data-n="{nb}">')
        out.append(f'<circle class="pf-net-dot pf-a-{info["area"]}" cx="{f(x)}" cy="{f(y)}" r="{f(info["r"])}"/>')
        if papers >= LABEL_MIN_PAPERS:
            right = x >= cx
            tx = x + (info["r"] + 5) * (1 if right else -1)
            out.append(f'<text class="pf-net-label" x="{f(tx)}" y="{f(y + 4)}" '
                       f'text-anchor="{"start" if right else "end"}">{html.escape(n)}</text>')
        out.append(f'<circle class="pf-hit" tabindex="0" cx="{f(x)}" cy="{f(y)}" r="{f(max(info["r"] + 4, 12))}" '
                   f'data-tip="{html.escape(tip)}"><title>{html.escape(tip)}</title></circle>')
        out.append("</g>")
    out.append(f'<g class="pf-net-me"><circle cx="{f(cx)}" cy="{f(cy)}" r="15"/>'
               f'<text x="{f(cx)}" y="{f(cy + 4.5)}" text-anchor="middle">me</text></g>')
    out.append("</g></svg></div></figure>")

    singles = sum(1 for n in names if nodes[n]["papers"] == 1)
    out.append(f'<p class="pf-note">{total} co-authors on {sum(1 for p in pubs if ME in split_authors(p["authors"]))} '
               'papers and preprints. Bigger dots mean more joint papers; lines join people who share a paper. '
               'Hover over or tab to a dot to see the name.</p>')
    rows = sorted((n for n in names if nodes[n]["papers"] > 1),
                  key=lambda n: (-nodes[n]["papers"], n))
    out.append('<details class="pf-chart-data"><summary>Show the co-authors as a table</summary>')
    out.append('<table class="table table-sm"><thead><tr><th>Co-author</th><th>Joint papers</th>'
               '<th>Years</th><th>Circle</th></tr></thead><tbody>')
    for n in rows:
        i = nodes[n]
        out.append(f"<tr><td>{html.escape(n)}</td><td>{i['papers']}</td><td>{years(i['years'])}</td>"
                   f"<td>{html.escape(AREA_NAME[i['area']])}</td></tr>")
    out.append(f'</tbody></table><p class="pf-note">Plus {singles} co-authors with one joint paper.</p></details>')
    return "```{=html}\n" + "\n".join(out) + "\n```\n"
