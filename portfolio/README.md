# Portfolio (bczech.github.io)

Quarto source of the portfolio served at https://bczech.github.io/.
The teaching site in the parent directory is a separate Quarto project (/teaching/).

## Build

```bash
cd portfolio
quarto render          # HTML pages + cv.pdf -> _site/
```

`scripts/gen_content.py` runs first (pre-render hook) and builds the publication
lists from `data/publications.toml` and the skill cards from `data/skills.toml`.
It needs only Python 3.11+.

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
```

## Update the citation numbers

`python3 scripts/update_metrics.py` downloads citations, h-index and citations per
year from OpenAlex into `data/metrics.toml` (needs internet). Then re-render: the
stat tiles on the About page and the charts on the Research page update.

## Publish

Copy the contents of `_site/` to the root of the `master` branch
(next to `teaching/`), commit and push.
