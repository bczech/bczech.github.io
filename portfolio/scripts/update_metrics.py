"""Fetch citation metrics from OpenAlex and save them to data/metrics.toml.

The GitHub Actions workflow on the master branch (.github/workflows/portfolio.yml)
runs it every week before building the site. To refresh by hand:
    python3 scripts/update_metrics.py

If OpenAlex suddenly reports far fewer citations than before (it happens when
OpenAlex re-groups authors), the old numbers are kept and a warning is printed.

The render then uses data/metrics.toml for the stat tiles on the About page and
the "citations per year" chart on the Research page.
"""

import datetime
import json
import sys
import tomllib
import urllib.request
from pathlib import Path

ORCID = "0000-0002-9908-3007"
URL = f"https://api.openalex.org/authors/orcid:{ORCID}?mailto=bartosz.w.czech@gmail.com"
MAX_DROP = 0.8  # keep the old numbers if citations fall below 80% of the last value


def main():
    with urllib.request.urlopen(URL, timeout=30) as r:
        a = json.load(r)
    out = Path(__file__).resolve().parent.parent / "data" / "metrics.toml"
    if out.exists():
        with open(out, "rb") as f:
            old = tomllib.load(f)
        if a["cited_by_count"] < MAX_DROP * old["citations"]:
            print(f"::warning::OpenAlex reports {a['cited_by_count']} citations, "
                  f"down from {old['citations']}; keeping the old numbers")
            sys.exit(0)
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
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}: {a['cited_by_count']} citations, h-index {a['summary_stats']['h_index']}")


if __name__ == "__main__":
    main()
