"""Look for my works in OpenAlex that are not yet on the site.

Compares the DOIs that OpenAlex links to my ORCID with the DOIs in
data/publications.toml and data/ignored_works.toml. For every work found in
neither file it prints a ready-to-paste [[pub]] entry (authors, journal and
volume from Crossref).

    python3 scripts/check_new_works.py            # print what is missing
    python3 scripts/check_new_works.py --issue    # also open a GitHub issue per work

With --issue (used by the weekly GitHub Actions workflow) each new work gets one
issue labelled "new-publication". The DOI is in the issue body, so a work that
already has an issue, open or closed, is not reported again. To stop seeing a
work, add its DOI to data/ignored_works.toml or add the paper to
data/publications.toml (summary, methods, tags and area are written by hand).
"""

import json
import subprocess
import sys
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

ORCID = "0000-0002-9908-3007"
MAILTO = "bartosz.w.czech@gmail.com"  # OpenAlex and Crossref ask for a contact address
ROOT = Path(__file__).resolve().parent.parent
LABEL = "new-publication"


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"bczech.github.io (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def known_dois():
    dois = set()
    for name, key in (("publications.toml", "pub"), ("ignored_works.toml", "work")):
        path = ROOT / "data" / name
        if path.exists():
            with open(path, "rb") as f:
                dois |= {w["doi"].lower() for w in tomllib.load(f).get(key, [])}
    return dois


def openalex_works():
    url = ("https://api.openalex.org/works?per-page=200&select=doi,title,publication_year,type"
           f"&filter=author.orcid:{ORCID}&mailto={MAILTO}")
    works = []
    for w in get_json(url)["results"]:
        if w["doi"]:
            works.append({"doi": w["doi"].replace("https://doi.org/", "").lower(),
                          "title": w["title"] or "", "year": w["publication_year"], "type": w["type"]})
    return works


def initials(given):
    parts = given.replace("-", " ").replace(".", " ").split()
    return "".join(p[0].upper() for p in parts if p)


def toml_stub(w):
    """Draft [[pub]] entry from Crossref; falls back to OpenAlex data if Crossref fails."""
    title, journal, cite, authors = w["title"], "", "", ""
    try:
        m = get_json(f"https://api.crossref.org/works/{urllib.parse.quote(w['doi'])}?mailto={MAILTO}")["message"]
        title = (m.get("title") or [title])[0]
        journal = (m.get("container-title") or [""])[0]
        authors = ", ".join(f"{a.get('family', '')} {initials(a.get('given', ''))}".strip()
                            for a in m.get("author", []))
        vol, iss = m.get("volume", ""), m.get("issue", "")
        page = m.get("article-number") or m.get("page", "")
        cite = vol + (f"({iss})" if iss else "") + (f":{page}" if page else "")
    except Exception as e:  # noqa: BLE001 - a draft without Crossref data is still useful
        print(f"  (Crossref lookup failed: {e})", file=sys.stderr)
    kind = "preprint" if w["type"] == "preprint" else "article"
    q = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
    return "\n".join([
        "[[pub]]",
        f'type = "{kind}"',
        f"year = {w['year']}",
        f'title = "{q(title)}"',
        f'authors = "{q(authors)}"',
        f'journal = "{q(journal)}"',
        f'cite = "{q(cite)}"',
        f'doi = "{w["doi"]}"',
        'area = "genomics"   # genomics, drug, virology or other',
        'summary = ""',
        "methods = []",
        "tags = []",
    ])


def reported_dois():
    out = subprocess.run(["gh", "issue", "list", "--state", "all", "--label", LABEL, "--limit", "500",
                          "--json", "body"], capture_output=True, text=True, check=True).stdout
    return {line.strip().lower() for issue in json.loads(out) for line in issue["body"].splitlines()
            if line.strip().lower().startswith("10.")}


def open_issue(w, stub):
    body = "\n".join([
        f"OpenAlex lists a work linked to my ORCID that is not on the site yet (type: **{w['type']}**).",
        "",
        w["doi"],
        "",
        f"https://doi.org/{w['doi']}",
        "",
        "If it belongs on the Research page, add this entry to `portfolio/data/publications.toml`",
        "(newest first) and fill in `summary`, `methods`, `tags` and `area`:",
        "",
        "```toml",
        stub,
        "```",
        "",
        "If it should not be shown (correction, abstract, software record, wrong attribution),",
        "add its DOI to `portfolio/data/ignored_works.toml` and close this issue.",
        "",
        "_Opened by the weekly portfolio workflow._",
    ])
    title = f"New publication: {w['title'][:90]}"
    subprocess.run(["gh", "issue", "create", "--title", title, "--label", LABEL, "--body", body], check=True)


def main():
    known = known_dois()
    new = [w for w in openalex_works() if w["doi"] not in known]
    if not new:
        print("check_new_works: nothing new in OpenAlex")
        return
    issue = "--issue" in sys.argv
    already = reported_dois() if issue else set()
    for w in new:
        print(f"NEW: {w['year']} {w['type']} {w['doi']} {w['title'][:80]}")
        if w["doi"] in already:
            print("  already reported in an issue, skipping")
            continue
        stub = toml_stub(w)
        if issue:
            open_issue(w, stub)
        else:
            print(stub + "\n")


if __name__ == "__main__":
    main()
