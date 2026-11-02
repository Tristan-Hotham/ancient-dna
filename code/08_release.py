"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23872993, https://doi.org/10.5281/zenodo.23872993 and https://blog.tristanhotham.com/2026/10/31/ancient-dna/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Ancient_DNA_on_the_Map"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
B, EY = R["bias"], R["europe_y"]
assert R["source"]["mapped_modern"] == 16400                                                                        # alt text "16,400 ancient people"
assert [round(B["Europe"][k], 1) for k in ("pct", "pop_pct", "land_pct")] == [68.4, 9.2, 7.5]
assert [round(B["Asia"][k]) for k in ("pct", "pop_pct", "land_pct")] == [22, 60, 33] and [round(B["Africa"][k], 1) for k in ("pct",)] == [1.9]
assert round(B["Africa"]["pop_pct"]) == 17 and round(B["Africa"]["land_pct"]) == 22
P = {y["y"]: y["n"] for y in R["pubs"]["years"]}
assert P[2025] == 3757 and all(1250 < P[y] < 1350 for y in (2018, 2019)) and sum(P[y] for y in range(2010, 2015)) < 50
H = {h["a"]: h["n"] for h in R["half_millennia"]}
assert max(H, key=H.get) == 500 and 2900 < H[500] < 3100
A = R["neolithic"]["by_country"]
assert A["Turkey"]["yr"] == "8750 BCE" and 3700 <= -A["Ireland"]["year"] <= 3800 and 5300 < -A["France"]["year"] < 5500
assert EY["early"]["i2g2_pct"] > 50 and EY["late"]["r_pct"] > 50                                                   # "mostly I2 and G2 ... mostly R1b or R1a"
bb = {b["a"]: b for b in R["steppe"]["Britain"]["bins"]}
assert all(bb[a]["clades"]["I2"] / bb[a]["n"] > .9 for a in (-4000, -3500, -3000))                                   # "almost entirely I2"
assert all(73 <= bb[a]["r1b_pct"] <= 100 for a in range(-2500, 500, 500)) and 30 < 100 * bb[500]["clades"]["I1"] / bb[500]["n"] < 36
first = [next(b for b in R["steppe"][r]["bins"] if b["a"] == -2500)["steppe_pct"] for r in R["steppe"]]
assert min(first) >= 50 and max(first) > 90                                                                          # "between half and more than nine tenths"
later = [b["steppe_pct"] for r in R["steppe"] for b in R["steppe"][r]["bins"] if b["n"] >= 5 and -2500 <= b["a"] < 1500]
assert min(later) >= 28                                                                                              # "about 30% and 100%"
assert R["sites"][0]["site"].startswith("Mödling")
assert 3800 < R["famous"][13]["bp"] < 4100                                                                          # "about four thousand years ago"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23872993", "https://blog.tristanhotham.com/2026/10/31/ancient-dna/", "10.5281/zenodo.23872993"}
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s, bs, br = R["source"], R["bias_sum"], R["britain"]
meta = {"title": "Ancient DNA on the map: 16,496 ancient genomes, placed where and when they lived",
        "slug": "ancient-dna",
        "excerpt": f"I mapped every ancient human genome in the Allen Ancient DNA Resource, {s['kept']:,} people, by where and when they lived. {bs['eu_pct']:.0f}% come from Europe; the first farmers spread out of Anatolia at about a kilometre a year; and in Britain, none of {br['pre_n']} men before 2500 BCE carried the Y line R1b.",
        "seo_description": f"A map of {s['kept']:,} ancient human genomes: sampling bias, the spread of farming and the Y chromosome turnover in Europe after 2500 BCE.",
        "tags": ["ancient DNA", "archaeology", "genetics", "maps", "data visualisation", "Neolithic", "Bronze Age", "AADR"],
        "header_alt": "Title card reading 'Ancient DNA on the map' in black, red and blue on pale paper, beside a map of Europe and the Near East covered in small dots coloured from dark brown for the oldest to blue for the most recent, densest in Britain, Denmark, Hungary and Austria. Text: 16,496 ancient genomes, placed where and when they lived."}
assert meta["title"].startswith(f"Ancient DNA on the map: {s['kept']:,}")
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/ancient-dna_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"ancient-dna/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"ancient-dna/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "ancient-dna/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Ancient DNA on the Map: Where and When the World's Published Ancient Human Genomes Lived",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Data: Allen Ancient DNA Resource (AADR) v66.p1, Mallick et al., Harvard Dataverse, doi:10.7910/DVN/FFIDCW (CC0 1.0).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["ancient DNA", "archaeogenetics", "Y chromosome", "mitochondrial DNA", "Neolithic", "Bell Beaker", "Yamnaya", "sampling bias", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.7910/DVN/FFIDCW", "relation": "isDerivedFrom", "resource_type": "dataset", "scheme": "doi"},
                                 {"identifier": "10.1038/s41597-024-03031-7", "relation": "references", "resource_type": "publication-article", "scheme": "doi"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
