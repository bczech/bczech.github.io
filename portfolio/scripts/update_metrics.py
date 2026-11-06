"""Fetch citation metrics from OpenAlex and save them to data/metrics.toml.

Run by hand when you want fresh numbers (it needs internet, so it is NOT part
of the render):  python3 scripts/update_metrics.py

The render then uses data/metrics.toml for the stat tiles on the About page and
the "citations per year" chart on the Research page.
"""

import datetime
import json
import urllib.request
from pathlib import Path

ORCID = "0000-0002-9908-3007"
URL = f"https://api.openalex.org/authors/orcid:{ORCID}"


def main():
    with urllib.request.urlopen(URL, timeout=30) as r:
        a = json.load(r)
    years = sorted(a["counts_by_year"], key=lambda d: d["year"])
    lines = [
        "# Written by scripts/update_metrics.py from OpenAlex. Do not edit by hand.",
        f'source = "OpenAlex"',
        f'updated = "{datetime.date.today().isoformat()}"',
        f'citations = {a["cited_by_count"]}',
        f'h_index = {a["summary_stats"]["h_index"]}',
        "",
        "# citations received in each calendar year",
        "[citations_by_year]",
    ]
    lines += [f'{d["year"]} = {d["cited_by_count"]}' for d in years]
    out = Path(__file__).resolve().parent.parent / "data" / "metrics.toml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}: {a['cited_by_count']} citations, h-index {a['summary_stats']['h_index']}")


if __name__ == "__main__":
    main()
