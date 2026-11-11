# Portfolio (bczech.github.io)

Quarto source of the portfolio served at https://bczech.github.io/.
The teaching site in the parent directory is a separate Quarto project (/teaching/).

## Build

```bash
cd portfolio
quarto render          # HTML pages + cv.pdf -> _site/
```

`scripts/gen_content.py` runs first (pre-render hook) and builds the publication
lists from `data/publications.toml`, the skill cards from `data/skills.toml`, the
charts from `data/metrics.toml` and the co-author network (`scripts/coauthors.py`).
It needs only Python 3.11+. The CV PDF uses the Inter font bundled in `fonts/`
(SIL Open Font License, see `fonts/LICENSE.txt`), so it looks the same everywhere.

## Edit skills

Add or remove items in `data/skills.toml`. The cards on the About page and the
Skills section of the CV both come from this file.

## Add a publication

Copy one `[[pub]]` block in `data/publications.toml`, keep newest first, and
re-render. The count of articles on the About and Research pages updates itself.

Example:

```toml
[[pub]]
type = "article"
year = 2027
title = "Paper title"
authors = "Kowalski J, Czech B, Nowak A"
journal = "Scientific Reports"
cite = "17:1234"
doi = "10.1038/xxxx"
area = "genomics"
```

`area` places the co-authors in a circle of the network on the Research page:
`genomics`, `drug`, `virology` or `other`. Each co-author takes the circle of
most of the papers we share.

New works linked to my ORCID in OpenAlex are found automatically (see below):
`python3 scripts/check_new_works.py` prints a ready-to-paste `[[pub]]` entry for
each of them. Works that should not be shown (corrections, abstracts, software
records) go to `data/ignored_works.toml`.

## Update the citation numbers

`python3 scripts/update_metrics.py` downloads citations, h-index and citations per
year from OpenAlex into `data/metrics.toml` (needs internet). Then re-render: the
stat tiles on the About page and the charts on the Research page update.
If OpenAlex reports more than 20% fewer citations than before, the old numbers stay.

## Publish

The "Portfolio" workflow on the `master` branch (`.github/workflows/portfolio.yml`)
builds and publishes the site:

- every Monday, with fresh citation counts from OpenAlex;
- after a push to `quarto-site` that changes `portfolio/`
  (started by `.github/workflows/portfolio-trigger.yml` on `quarto-site`);
- by hand: GitHub > Actions > Portfolio > Run workflow.

It copies `_site/` to the root of `master` and never touches `teaching/`.
It also opens an issue for each new work in OpenAlex (label `new-publication`)
and one issue listing broken links (label `broken-links`).

The workflow commits to `master`, so before publishing the teaching site by hand
run `git fetch` and build on top of `origin/master`.
