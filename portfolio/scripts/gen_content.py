"""Build page snippets from data/publications.toml, data/skills.toml and data/metrics.toml.

Runs automatically before every `quarto render` (pre-render hook in
_quarto.yml). Writes the files that the pages include:

  _pubs_web.md      expandable publication cards for research.qmd
  _pubs_cv.md       plain reference list for cv.qmd (HTML and PDF)
  _skills_web.md    skill cards with chips for index.qmd
  _skills_cv.md     one line per skill group for cv.qmd
  _charts_web.md    "articles per year" and "citations per year" charts for research.qmd
  _network_web.md   co-author network for research.qmd (scripts/coauthors.py)
  _variables.yml    numbers used in the text, e.g. {{< var pubs.articles >}}

Only the Python standard library is needed (tomllib, Python 3.11+).
Run by hand from portfolio/:  python3 scripts/gen_content.py
"""

import html
import tomllib
from pathlib import Path

from coauthors import network_web

ROOT = Path(__file__).resolve().parent.parent
ME = "Czech B"


def load(name, key):
    with open(ROOT / "data" / name, "rb") as f:
        return tomllib.load(f)[key]


def authors_html(authors):
    # Escape first, then mark my name in bold.
    return html.escape(authors).replace(ME, f"<strong>{ME}</strong>")


def authors_md(authors):
    return authors.replace(ME, f"**{ME}**")


def card(p):
    """One <details> card; summary row is always visible, body opens on click."""
    doi_url = f"https://doi.org/{p['doi']}"
    cite = f" {html.escape(p['cite'])}" if p.get("cite") else ""
    badge = '<span class="pf-pub-badge">First author</span>' if p.get("first") else ""

    methods = "".join(f"<li>{html.escape(m)}</li>" for m in p.get("methods", []))
    tags = "".join(f'<span class="pf-tag">{html.escape(t)}</span>' for t in p.get("tags", []))
    img = ""
    if p.get("img"):
        img = (f'<a href="{doi_url}" class="pf-pub-fig">'
               f'<img src="{p["img"]}" alt="Figure from the paper" loading="lazy"></a>')

    body = ""
    if p.get("summary") or methods or img:
        body = (
            '<div class="pf-pub-body">'
            '<div class="pf-pub-text">'
            + (f'<p>{html.escape(p["summary"])}</p>' if p.get("summary") else "")
            + (f'<p class="pf-pub-label">Methods</p><ul>{methods}</ul>' if methods else "")
            + (f'<div class="pf-tags">{tags}</div>' if tags else "")
            + f'<a class="pf-btn pf-btn-sm" href="{doi_url}"><i class="bi bi-box-arrow-up-right"></i> Read the paper</a>'
            "</div>"
            + img
            + "</div>"
        )

    return (
        '<details class="pf-pub">'
        "<summary>"
        f'<span class="pf-pub-year">{p["year"]}</span>'
        '<span class="pf-pub-main">'
        f'<span class="pf-pub-title">{html.escape(p["title"])}</span>'
        f'<span class="pf-pub-authors">{authors_html(p["authors"])}</span>'
        f'<span class="pf-pub-journal"><em>{html.escape(p["journal"])}</em>{cite}</span>'
        "</span>"
        f"{badge}"
        '<i class="bi bi-chevron-down pf-pub-arrow"></i>'
        "</summary>"
        f"{body}"
        "</details>"
    )


def web(pubs):
    articles = [p for p in pubs if p["type"] == "article"]
    preprints = [p for p in pubs if p["type"] == "preprint"]
    out = ["## Peer-reviewed articles {#articles}", "",
           "Click a paper to see the question, the methods and a figure.", "",
           "```{=html}", '<div class="pf-pubs">']
    out += [card(p) for p in articles]
    out += ["</div>", "```", ""]
    if preprints:
        out += ["## Preprints {#preprints}", "", "```{=html}", '<div class="pf-pubs">']
        out += [card(p) for p in preprints]
        out += ["</div>", "```", ""]
    return "\n".join(out)


def ref_md(p):
    cite = f", {p['cite']}" if p.get("cite") else ""
    return (f"{authors_md(p['authors'])} ({p['year']}). {p['title']}. "
            f"*{p['journal']}*{cite}. [doi:{p['doi']}](https://doi.org/{p['doi']})")


def cv(pubs):
    articles = [p for p in pubs if p["type"] == "article"]
    preprints = [p for p in pubs if p["type"] == "preprint"]
    out = ["### Peer-reviewed articles", ""]
    out += [f"{i}. {ref_md(p)}" for i, p in enumerate(articles, 1)]
    if preprints:
        out += ["", "### Preprints", ""]
        out += [f"{i}. {ref_md(p)}" for i, p in enumerate(preprints, 1)]
    return "\n".join(out) + "\n"


def skills_web(groups):
    """Grid of cards, one per skill group, each with a row of chips."""
    out = ["```{=html}", '<div class="pf-grid pf-skills">']
    for g in groups:
        chips = "".join(f'<span class="pf-tag">{html.escape(i)}</span>' for i in g["items"])
        out.append(
            '<div class="pf-card">'
            f'<span class="pf-card-ic"><i class="bi bi-{g["icon"]}"></i></span>'
            f'<h3>{html.escape(g["name"])}</h3>'
            f'<div class="pf-tags">{chips}</div>'
            "</div>"
        )
    out += ["</div>", "```", ""]
    return "\n".join(out)


def skills_cv(groups):
    return "\n".join(f"- **{g['name']}:** {', '.join(g['items'])}." for g in groups) + "\n"


def nice_ticks(vmax):
    """Round axis ticks: 0 and 2-4 more steps of 1, 2 or 5 x 10^k covering vmax."""
    if vmax <= 0:
        return [0, 1]
    for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        n = -(-vmax // step)  # ceil
        if n <= 4:
            return [i * step for i in range(int(n) + 1)]
    return [0, vmax]


def column_chart(cid, title, values, unit_one, unit_many):
    """One single-series column chart as inline SVG (no legend: the title names the series).

    Follows the dataviz skill: one y axis, columns <= 24 px with a 4 px rounded top and a
    square base, hairline recessive grid, labels only on the highest and the latest column,
    a hover/focus tooltip on a hit area larger than the column, and a data table elsewhere.
    """
    W, H = 440, 210
    left, right, top, bottom = 34, 8, 18, 26
    years = sorted(values)
    ticks = nice_ticks(max(values.values()))
    ymax = ticks[-1]
    band = (W - left - right) / len(years)
    bw = min(24, band * 0.55)
    ph = H - top - bottom

    def y(v):
        return top + ph * (1 - v / ymax)

    parts = [f'<svg viewBox="0 0 {W} {H}" class="pf-chart-svg" role="img" '
             f'aria-label="{html.escape(title)}, {years[0]} to {years[-1]}">']
    for t in ticks:  # grid + y labels
        parts.append(f'<line class="pf-grid" x1="{left}" x2="{W - right}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>')
        parts.append(f'<text class="pf-axis" x="{left - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{t}</text>')
    vmax = max(values.values())
    labelled = {years[-1]} | {yr for yr in years if values[yr] == vmax}
    for i, yr in enumerate(years):
        v = values[yr]
        cx = left + band * (i + 0.5)
        x0, x1 = cx - bw / 2, cx + bw / 2
        base = y(0)
        if v > 0:
            yt = y(v)
            r = min(4, (base - yt) / 2)
            parts.append(
                f'<path class="pf-col" d="M{x0:.1f},{base:.1f} L{x0:.1f},{yt + r:.1f} '
                f'Q{x0:.1f},{yt:.1f} {x0 + r:.1f},{yt:.1f} L{x1 - r:.1f},{yt:.1f} '
                f'Q{x1:.1f},{yt:.1f} {x1:.1f},{yt + r:.1f} L{x1:.1f},{base:.1f} Z"/>')
        if yr in labelled and v > 0:
            parts.append(f'<text class="pf-val" x="{cx:.1f}" y="{y(v) - 6:.1f}" text-anchor="middle">{v}</text>')
        label_year = f"{yr}" if len(years) <= 10 else f"’{str(yr)[2:]}"
        parts.append(f'<text class="pf-axis" x="{cx:.1f}" y="{H - 8}" text-anchor="middle">{label_year}</text>')
        tip = f"{v} {unit_one if v == 1 else unit_many} in {yr}"
        parts.append(f'<rect class="pf-hit" x="{cx - band / 2:.1f}" y="{top}" width="{band:.1f}" height="{ph:.1f}" '
                     f'tabindex="0" data-tip="{html.escape(tip)}"><title>{html.escape(tip)}</title></rect>')
    parts.append(f'<line class="pf-baseline" x1="{left}" x2="{W - right}" y1="{y(0):.1f}" y2="{y(0):.1f}"/>')
    parts.append("</svg>")
    return (f'<figure class="pf-chart" id="{cid}"><figcaption class="pf-chart-title">{html.escape(title)}</figcaption>'
            + "".join(parts) + "</figure>")


def charts_web(pubs, metrics):
    cites = {int(k): v for k, v in metrics["citations_by_year"].items()}
    arts = {}
    for p in pubs:
        if p["type"] == "article":
            arts[p["year"]] = arts.get(p["year"], 0) + 1
    first = min(min(arts), min(cites))
    last = max(max(arts), max(cites))
    years = range(first, last + 1)
    arts = {yr: arts.get(yr, 0) for yr in years}
    cites = {yr: cites.get(yr, 0) for yr in years}
    rows = "".join(f"<tr><td>{yr}</td><td>{arts[yr]}</td><td>{cites[yr]}</td></tr>" for yr in years)
    return "\n".join([
        "```{=html}",
        '<div class="pf-charts">',
        column_chart("chart-articles", "Peer-reviewed articles per year", arts, "article", "articles"),
        column_chart("chart-citations", "Citations per year", cites, "citation", "citations"),
        "</div>",
        f'<p class="pf-note">Articles from the list below; citations from {metrics["source"]}, '
        f'updated {metrics["updated"]}. The current year is not complete.</p>',
        '<details class="pf-chart-data"><summary>Show the numbers as a table</summary>'
        f'<table class="table table-sm"><thead><tr><th>Year</th><th>Articles</th><th>Citations</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></details>",
        "```",
        "",
    ])


def main():
    pubs = load("publications.toml", "pub")
    with open(ROOT / "data" / "metrics.toml", "rb") as f:
        metrics = tomllib.load(f)
    (ROOT / "_charts_web.md").write_text(charts_web(pubs, metrics), encoding="utf-8")
    (ROOT / "_network_web.md").write_text(network_web(pubs), encoding="utf-8")
    groups = load("skills.toml", "group")
    (ROOT / "_skills_web.md").write_text(skills_web(groups), encoding="utf-8")
    (ROOT / "_skills_cv.md").write_text(skills_cv(groups), encoding="utf-8")
    n_art = sum(p["type"] == "article" for p in pubs)
    n_first = sum(p["type"] == "article" and p.get("first", False) for p in pubs)
    (ROOT / "_pubs_web.md").write_text(web(pubs), encoding="utf-8")
    (ROOT / "_pubs_cv.md").write_text(cv(pubs), encoding="utf-8")
    (ROOT / "_variables.yml").write_text(
        f"pubs:\n  articles: {n_art}\n  first: {n_first}\n"
        f"metrics:\n  citations: {metrics['citations']}\n  h_index: {metrics['h_index']}\n"
        f"  source: {metrics['source']}\n  updated: \"{metrics['updated']}\"\n", encoding="utf-8")
    n_skills = sum(len(g["items"]) for g in groups)
    print(f"gen_content: {n_art} articles ({n_first} first-author), "
          f"{len(pubs) - n_art} preprint(s), {n_skills} skills in {len(groups)} groups")


if __name__ == "__main__":
    main()
