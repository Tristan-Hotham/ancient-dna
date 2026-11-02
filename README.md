# Ancient DNA on the map: where and when the world's published ancient human genomes lived

A map and analysis of every ancient human individual in the Allen Ancient DNA Resource (AADR) v66.p1: 16,496 people whose genomes pass the archive's quality checks, placed where they were buried and when they lived, from 43,925 BCE to 1890 CE. The interactive page has a time slider with a play button, colours by period, culture label, Y line or mtDNA line, and charts of sampling bias, the spread of the first farmers and the arrival of steppe-associated Y lines in Europe.

Interactive page: https://maps.tristanhotham.com/ancient-dna/
Paper: https://doi.org/10.5281/zenodo.23872993
Blog post: https://blog.tristanhotham.com/2026/10/31/ancient-dna/

## Headline results

- The archive: 19,118 ancient rows describe 17,629 individuals; 16,496 (94%) have data graded Pass, PROVISIONAL_PASS or MERGE_PASS, from 3,664 sites in 127 countries and territories. 8 Neanderthal and Denisovan genomes are counted apart. Half the modern humans lived after 450 BCE; 102 before 10,000 BCE. 80% were first published in 2020 or later. Molecular sex: 8,601 male, 6,835 female, 1,060 unknown.
- Sampling bias: 68.4% of located modern humans come from Europe (Russia split at 60°E), which has 9.2% of today's people and 7.5% of the land; Africa 1.9% for 17.1% of people.
- First farmers: the earliest Neolithic-labelled burial in each of 24 countries of Europe and Anatolia gets later with distance from Çatalhöyük by 0.88 years per km (r = 0.75), about 1.1 km a year.
- Steppe-associated Y lines: in Britain none of 76 men before 2500 BCE carries R1b; 50 of 56 (89%) from 2500 to 1500 BCE do. R1b plus R1a before 3000 BCE and from 2500 to 1500 BCE: Iberia 2% to 80%, Scandinavia 3% to 51%, central Europe 5% to 82%. Haplogroups are a proxy for ancestry, not ancestry itself.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; results embedded, `data/individuals.json` and `data/world.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/individuals.csv` | The 16,496 individuals that pass the quality checks: IDs, group, site, country, coordinates, date mean and standard deviation, calendar year, date text, molecular sex, Y call and major clade, mtDNA call and macro-haplogroup, period, culture label, region, continent, archaic flag, publication and assessment. |
| `data/failed_quality_individuals.csv` | The 1,133 ancient individuals with no passing data, same fields. |
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

- Ancient: date mean above 0 BP. An individual is one Individual ID; it is kept if any of its rows has an ASSESSMENT starting Pass, PROVISIONAL_PASS or MERGE_PASS, represented by the passing row with most SNPs on the 1240k set (taking each individual's richest row and then filtering would keep 16,267).
- Archaic: Group ID naming Neanderthals or Denisova and dated before 40,000 BP.
- Y lines: the archive's ISOGG call, or its hand call where given (224 people), grouped by leading characters into R1b, R1a, I1, I2, G2, J1, J2, E1b, N, Q, C, O, H, T, L, D and other; calls too broad to separate R1a from R1b (CT, F, K, P, R, R1...) are excluded from shares. mtDNA by leading letter. Sex is molecular sex.
- Culture labels: keywords in the Group ID (rules in `code/common.py`), named cultures before broad periods. Periods: from the calendar year (1950 minus BP).
- Continents: Natural Earth polygons, Russia split at 60°E; population 2019 estimates, land without Antarctica.
- Neolithic arrival: Neolithic-labelled modern humans in Europe and Anatolia, leaving out Russia, Ukraine, Belarus, Moldova, the Baltic states and Finland, mixed hunter-gatherer labels, dates with sd over 300 years and dates outside their own stated range; earliest per country with at least three.
- Caveats: the archive reflects where research has been done; earliest sampled burials are lower bounds; haplogroups trace single lines, not ancestry.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw input: `raw/v66.p1_1240K.aadr.PUB.anno` (download from the AADR Dataverse, https://doi.org/10.7910/DVN/FFIDCW; not included in the repository); Natural Earth in `/home/claude/newdata/raw/geo/` (paths in `code/common.py`). Intermediate files go to `/dev/shm/ancientdna/work` (set `ADTMP` to change).

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

- Mallick, S., Micco, A., Mah, M., Ringbauer, H., Lazaridis, I., Olalde, I., Patterson, N. and Reich, D. The Allen Ancient DNA Resource (AADR), release v66.p1. Harvard Dataverse, doi:10.7910/DVN/FFIDCW. CC0 1.0.
- Mallick, S. et al. (2024) The Allen Ancient DNA Resource (AADR) a curated compendium of ancient human genomes. Scientific Data 11, 182. doi:10.1038/s41597-024-03031-7.
- Every genome comes from an original publication, named for each individual in the data files.
- Natural Earth countries, land and populated places (https://www.naturalearthdata.com/). Public domain.
- Page base map: labels and borders from OpenFreeMap (© OpenMapTiles, © OpenStreetMap contributors); relief, hillshade and satellite tiles © Esri.

## Citation

Hotham, T. (2026) Ancient DNA on the map: where and when the world's published ancient human genomes lived. Zenodo. https://doi.org/10.5281/zenodo.23872993

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
