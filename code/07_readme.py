"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, bs, br, NL, t = R["source"], R["bias_sum"], R["britain"], R["neolithic"], R["time"]
N = lambda v: f"{round(v):,}"
ST = R["steppe"]
readme = f"""# Ancient DNA on the map: where and when the world's published ancient human genomes lived

A map and analysis of every ancient human individual in the Allen Ancient DNA Resource (AADR) {s['version']}: {N(s['kept'])} people whose genomes pass the archive's quality checks, placed where they were buried and when they lived, from {yr(t['oldest_year'])} to {yr(t['youngest_year'])}. The interactive page has a time slider with a play button, colours by period, culture label, Y line or mtDNA line, and charts of sampling bias, the spread of the first farmers and the arrival of steppe-associated Y lines in Europe.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- The archive: {N(s['ancient_rows'])} ancient rows describe {N(s['ancient_individuals'])} individuals; {N(s['kept'])} ({s['kept_pct']:.0f}%) have data graded Pass, PROVISIONAL_PASS or MERGE_PASS, from {N(s['n_sites'])} sites in {s['n_countries']} countries and territories. {s['archaic']} Neanderthal and Denisovan genomes are counted apart. Half the modern humans lived after {yr(t['median_year'])}; {t['n_before_10000bce']} before 10,000 BCE. {R['pubs']['since2020_pct']:.0f}% were first published in 2020 or later. Molecular sex: {N(R['sex']['M'])} male, {N(R['sex']['F'])} female, {N(R['sex']['U'])} unknown.
- Sampling bias: {bs['eu_pct']:.1f}% of located modern humans come from Europe (Russia split at 60°E), which has {bs['eu_pop_pct']:.1f}% of today's people and {bs['eu_land_pct']:.1f}% of the land; Africa {R['bias']['Africa']['pct']:.1f}% for {bs['africa_pop_pct']:.1f}% of people.
- First farmers: the earliest Neolithic-labelled burial in each of {NL['n_countries']} countries of Europe and Anatolia gets later with distance from Çatalhöyük by {NL['slope_yr_per_km']:.2f} years per km (r = {NL['r']:.2f}), about {NL['km_per_year']:.1f} km a year.
- Steppe-associated Y lines: in Britain none of {br['pre_n']} men before 2500 BCE carries R1b; {br['post_r1b']} of {br['post_n']} ({br['post_r1b_pct']:.0f}%) from 2500 to 1500 BCE do. R1b plus R1a before 3000 BCE and from 2500 to 1500 BCE: Iberia {ST['Iberia']['pre3000_pct']:.0f}% to {ST['Iberia']['ba_pct']:.0f}%, Scandinavia {ST['Scandinavia']['pre3000_pct']:.0f}% to {ST['Scandinavia']['ba_pct']:.0f}%, central Europe {ST['Central Europe']['pre3000_pct']:.0f}% to {ST['Central Europe']['ba_pct']:.0f}%. Haplogroups are a proxy for ancestry, not ancestry itself.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; results embedded, `data/individuals.json` and `data/world.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/individuals.csv` | The {N(s['kept'])} individuals that pass the quality checks: IDs, group, site, country, coordinates, date mean and standard deviation, calendar year, date text, molecular sex, Y call and major clade, mtDNA call and macro-haplogroup, period, culture label, region, continent, archaic flag, publication and assessment. |
| `data/failed_quality_individuals.csv` | The {N(s['failed'])} ancient individuals with no passing data, same fields. |
| `data/y_clades_by_region.csv` | Men with a resolved Y line by region, 500 year bin and major clade. |
| `data/neolithic_arrival.csv` | Earliest Neolithic-labelled individual per country, with distance from Çatalhöyük. |
| `data/continents.csv`, `data/countries.csv`, `data/sites.csv` | Counts by continent (with population and land shares), country and site. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/individuals.json`, `data/site.json`, `data/world.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Ancient: date mean above 0 BP. An individual is one Individual ID; it is kept if any of its rows has an ASSESSMENT starting Pass, PROVISIONAL_PASS or MERGE_PASS, represented by the passing row with most SNPs on the 1240k set (taking each individual's richest row and then filtering would keep {N(s['strict_kept'])}).
- Archaic: Group ID naming Neanderthals or Denisova and dated before 40,000 BP.
- Y lines: the archive's ISOGG call, or its hand call where given ({s['y_manual']} people), grouped by leading characters into R1b, R1a, I1, I2, G2, J1, J2, E1b, N, Q, C, O, H, T, L, D and other; calls too broad to separate R1a from R1b (CT, F, K, P, R, R1...) are excluded from shares. mtDNA by leading letter. Sex is molecular sex.
- Culture labels: keywords in the Group ID (rules in `code/common.py`), named cultures before broad periods. Periods: from the calendar year (1950 minus BP).
- Continents: Natural Earth polygons, Russia split at 60°E; population 2019 estimates, land without Antarctica.
- Neolithic arrival: Neolithic-labelled modern humans in Europe and Anatolia, leaving out Russia, Ukraine, Belarus, Moldova, the Baltic states and Finland, mixed hunter-gatherer labels, dates with sd over 300 years and dates outside their own stated range; earliest per country with at least three.
- Caveats: the archive reflects where research has been done; earliest sampled burials are lower bounds; haplogroups trace single lines, not ancestry.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw input: `raw/v66.p1_1240K.aadr.PUB.anno` (download from the AADR Dataverse, {AADR_URL}; not included in the repository); Natural Earth in `/home/claude/newdata/raw/geo/` (paths in `code/common.py`). Intermediate files go to `/dev/shm/ancientdna/work` (set `ADTMP` to change).

```
python3 code/01_clean.py        # read the AADR file, filter, one row per individual, derived fields
python3 code/02_geo.py          # outlines, continents, population and land
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Mallick, S., Micco, A., Mah, M., Ringbauer, H., Lazaridis, I., Olalde, I., Patterson, N. and Reich, D. The Allen Ancient DNA Resource (AADR), release {s['version']}. Harvard Dataverse, doi:{AADR_DOI}. CC0 1.0.
- Mallick, S. et al. (2024) The Allen Ancient DNA Resource (AADR) a curated compendium of ancient human genomes. Scientific Data 11, 182. doi:{PAPER_DOI}.
- Every genome comes from an original publication, named for each individual in the data files.
- Natural Earth countries, land and populated places (https://www.naturalearthdata.com/). Public domain.
- Page base map: labels and borders from OpenFreeMap (© OpenMapTiles, © OpenStreetMap contributors); relief, hillshade and satellite tiles © Esri.

## Citation

Hotham, T. (2026) Ancient DNA on the map: where and when the world's published ancient human genomes lived. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The underlying data are from the
Allen Ancient DNA Resource (AADR) v66.p1, Mallick et al., Harvard Dataverse,
doi:10.7910/DVN/FFIDCW, released under CC0 1.0: please cite the AADR (and
Mallick et al. 2024, Scientific Data, doi:10.1038/s41597-024-03031-7) and the
original publication of each genome. Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] I mapped all {N(s['kept'])} published ancient human genomes by where and when they lived. {bs['eu_pct']:.0f}% come from Europe, and in Britain not one of {br['pre_n']} men before 2500 BCE carried the Y line R1b; a thousand years later {br['post_r1b_pct']:.0f}% did

## Body

The Allen Ancient DNA Resource (Harvard) collects every published ancient human genome in one free file. I placed each of the {N(s['kept'])} people that pass its quality checks at their burial place and date. Two things stand out. First, the sampling: {bs['eu_pct']:.0f}% of the genomes come from Europe, home to {bs['eu_pop_pct']:.0f}% of people today, and Africa supplies {R['bias']['Africa']['pct']:.1f}%. Second, the movements: the earliest Neolithic burial in each country gets later the further it is from Anatolia, at about {NL['km_per_year']:.1f} km a year, and around 2500 BCE the male (Y chromosome) lines across western Europe turn over, from mostly I2 and G2 to mostly R1b and R1a. In Britain it is all or nothing: 0 of {br['pre_n']} men before 2500 BCE, {br['post_r1b']} of {br['post_n']} in the next thousand years. Caveats: a Y haplogroup is one line of descent, a proxy for ancestry, not ancestry itself; "Neolithic" is the archive's label; and the map shows where geneticists have looked as much as where people lived. Interactive map with a play button through 45,000 years: {PAGE}

## Source comment

Source: Allen Ancient DNA Resource (AADR) {s['version']}, Mallick et al., Harvard Dataverse, doi:{AADR_DOI} (CC0 1.0); paper: Mallick et al. 2024, Scientific Data, doi:{PAPER_DOI}. Kept: individuals with data graded Pass, PROVISIONAL_PASS or MERGE_PASS (one row per individual). Y shares: men whose Y call reaches a major branch. Population and outlines: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for tx in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in tx.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
