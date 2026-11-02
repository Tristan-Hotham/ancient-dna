"""r/dataisbeautiful collage for ancient-dna: 2400 x 3200 px, light background. Numbers from data/results.json.
Map labels sit on open sea or on the paper around the map, with a halo, and are checked against land and dots;
no leader lines."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from shapely.geometry import shape as _shape, box as _box, Polygon as _Poly, Point as _Pt
from shapely.ops import unary_union
from shapely.prepared import prep as _prep

R = jload(f"{DATA}/results.json")
BGc = "#F7F5F0"; SEAc = "#E6EDF0"; LANDc = "#E2DDD1"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
HALOP = [pe.withStroke(linewidth=4, foreground=BGc)]
s, bs, br, NL = R["source"], R["bias_sum"], R["britain"], R["neolithic"]
I = pd.read_csv(f"{DATA}/individuals.csv", keep_default_na=False, na_values=[""])
I = I[I.lat.notna() & (I.archaic == 0)]
PN = [p[0] for p in PERIODS]

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "Where the world's ancient DNA comes from", fontproperties=DISP, fontsize=38, color=FG, va="top")
fig.text(.045, .945, f"All {s['kept']:,} ancient human genomes in the Allen Ancient DNA Resource that pass its quality checks, placed\n"
         f"where they were buried. {bs['eu_pct']:.0f}% come from Europe, home to {bs['eu_pop_pct']:.0f}% of people today. And in Britain, none of\n"
         f"{br['pre_n']} men before 2500 BCE carried the Y line R1b; in the next thousand years, {br['post_r1b_pct']:.0f}% did.",
         fontproperties=SERP, fontsize=13.5, color=FG, va="top", linespacing=1.45)

# ---- world map
ax = fig.add_axes([0, .585, 1, .285])
ax.add_patch(plt.Rectangle((WORLD_EXT[0], WORLD_EXT[2]), WORLD_EXT[1] - WORLD_EXT[0], WORLD_EXT[3] - WORLD_EXT[2], fc=SEAc, ec="none", zorder=0))
basemap(ax, land=LANDc, ec=BGc)
J = I.sort_values("date_mean_bp"); x, y = proj(J.lon.values, J.lat.values)
ax.scatter(x, y, s=4.5, c=[PCOL[p] for p in J.period], lw=0, alpha=.9, zorder=3)
_land = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = _shape(f["geometry"]); gs = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for q in gs:
        xy = np.array(q.exterior.coords); xx, yy = EE.transform(np.clip(xy[:, 0], -179.99, 179.99), np.clip(xy[:, 1], -89.9, 89.9))
        _land.append(_Poly(np.column_stack([xx, yy])).buffer(0))
LANDP = _prep(unary_union(_land).buffer(60e3))
DOTS = _prep(unary_union([_Pt(a, b).buffer(9e4) for a, b in zip(x, y)]))
fig.canvas.draw(); REN = fig.canvas.get_renderer(); PLACED = []


def tbox(t):
    bb = t.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 4, bb.y0 - 3], [bb.x1 + 4, bb.y1 + 3]])
    return _box(x0, y0, x1, y1)


def place(name, txt, lon0, lat0, col=FG, size=10.5, ha="center", r=40):
    t = ax.text(0, 0, txt, ha=ha, va="center", fontsize=size, color=col, family=MONO, linespacing=1.2, zorder=10, path_effects=HALO, fontweight="medium")
    for lo, la in [(lon0, lat0)] + sorted([(lon0 + dx, lat0 + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)], key=lambda q: (q[0] - lon0) ** 2 + (q[1] - lat0) ** 2):
        if abs(la) > 80 or abs(lo) > 180: continue
        px, py = proj(lo, la); t.set_position((float(px), float(py))); b = tbox(t)
        if not _box(WORLD_EXT[0] + 1e5, WORLD_EXT[2] + 1e5, WORLD_EXT[1] - 1e5, WORLD_EXT[3] - 1e5).contains(b): continue
        if LANDP.intersects(b) or DOTS.intersects(b) or any(b.intersects(o) for _, o in PLACED): continue
        PLACED.append((name, b)); print(name, lo, la); return
    raise RuntimeError("no clean spot for " + name)


B = R["bias"]
place("eu", f"EUROPE\n{B['Europe']['pct']:.0f}% of genomes\n{B['Europe']['pop_pct']:.0f}% of people", -38, 30, col=HOT, size=9.5)
place("af", f"AFRICA\n{B['Africa']['pct']:.1f}% of genomes\n{B['Africa']['pop_pct']:.0f}% of people", -20, 0, size=10.5)
place("as", f"ASIA\n{B['Asia']['pct']:.0f}% of genomes\n{B['Asia']['pop_pct']:.0f}% of people", 80, -12, size=10.5)
place("na", f"NORTH AMERICA\n{B['North America']['pct']:.1f}% / {B['North America']['pop_pct']:.0f}%", -140, 22, size=10)
place("sa", f"SOUTH AMERICA\n{B['South America']['pct']:.1f}% / {B['South America']['pop_pct']:.1f}%", -105, -30, size=10)
place("oc", f"OCEANIA\n{B['Oceania']['pct']:.1f}% / {B['Oceania']['pop_pct']:.1f}%", 168, -45, size=10)
for nm, b in PLACED:
    assert not LANDP.intersects(b) and not DOTS.intersects(b) and not any(b.intersects(o) for n2, o in PLACED if n2 != nm), nm
fig.text(.045, .578, "Each dot is one person, coloured by when they lived. Continent figures: share of genomes / share of today's people.", fontsize=9.6, color=MUT, va="top")
fig.legend(handles=[Patch(color=PCOL[p], label=p) for p in PN], loc="upper left", bbox_to_anchor=(.035, .568), ncol=4, frameon=False, fontsize=10, handletextpad=.5, columnspacing=1.3)

# ---- numbers row
nums = [(f"{s['kept']:,}", INK, "ancient genomes passing\nthe archive's checks"),
        (f"{R['time']['oldest_k']:,}", COOL, "years: the oldest modern\nhumans in the archive"),
        (f"{R['pubs']['since2020_pct']:.0f}%", GOLD, "first published\nin 2020 or later"),
        (f"{NL['km_per_year']:.1f} km", HOT, "a year: how fast the\nfirst farmers spread")]
for i, (big, col, small) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, .505, big, fontproperties=DISP, fontsize=31, color=col, va="top")
    fig.text(xx, .468, small, family=MONO, fontsize=10.3, color=FG, va="top", linespacing=1.4)

# ---- Europe before and after
M = I[(I.sex == "M") & I.y_clade.notna() & ~I.y_clade.isin(["Too broad"]) & I.lon.between(-12, 45) & I.lat.between(34, 72)]
GRP = [("R1b", YCOL["R1b"]), ("R1a", YCOL["R1a"]), ("I2", YCOL["I2"]), ("G2", YCOL["G2"]), ("Other lines", "#8C8478")]
fig.text(.045, .425, "Europe's male lines turn over after 2500 BCE", fontproperties=DISPB, fontsize=17, color=FG, va="top")
for k, key in enumerate(("early", "late")):
    E = R["europe_y"][key]
    a2 = fig.add_axes([.04 + k * .48, .238, .45, .158])
    a2.add_patch(plt.Rectangle((EU_EXT[0], EU_EXT[2]), EU_EXT[1] - EU_EXT[0], EU_EXT[3] - EU_EXT[2], fc=SEAc, ec="none", zorder=0))
    basemap(a2, t=EU, ext=EU_EXT, land=LANDc, ec=BGc, lw=.2)
    d = M[(M.year_ce >= E["a"]) & (M.year_ce < E["b"])]; assert len(d) == E["men"]
    g = d.y_clade.where(d.y_clade.isin(["R1b", "R1a", "I2", "G2"]), "Other lines"); o = np.argsort(g.isin(["R1b", "R1a"]).values)
    xx, yy = proj(d.lon.values[o], d.lat.values[o], EU)
    a2.scatter(xx, yy, s=9, c=[dict(GRP)[v] for v in g.values[o]], ec="#fff", lw=.25, zorder=4)
    fig.text(.045 + k * .48, .399, f"{yr(E['a'])} to {yr(E['b'])}: {E['r_pct']:.0f}% of {E['men']} men carry R1b or R1a", fontsize=10.3, color=FG, va="bottom")
fig.legend(handles=[Patch(color=c, label=n) for n, c in GRP], loc="upper left", bbox_to_anchor=(.035, .236), ncol=5, frameon=False, fontsize=10.5)

# ---- Britain bars
a3 = fig.add_axes([.075, .088, .9, .068]); a3.set_facecolor(BGc)
YC = [c for c, _ in Y_CLADES]
Bn = [b for b in R["steppe"]["Britain"]["bins"] if -4000 <= b["a"] < 1500 and b["n"] >= 5]
for i, b in enumerate(Bn):
    acc = 0
    for c in YC:
        v = 100 * b["clades"][c] / b["n"]
        if v: a3.bar(i, v, bottom=acc, color=YCOL[c], width=.86); acc += v
    a3.text(i, 104, f"{b['n']} men", ha="center", fontsize=8.3, color=MUT)
a3.set_xticks(range(len(Bn))); a3.set_xticklabels([("1 CE" if b["a"] == 0 else f"{yr(b['a'])}").replace(" BCE", "\nBCE").replace(" CE", "\nCE") for b in Bn], fontsize=8.3)
a3.set_ylim(0, 112); a3.set_yticks([0, 50, 100]); a3.set_yticklabels(["0", "50", "100%"], fontsize=9); spines(a3)
k = [b["a"] for b in Bn].index(-2500); a3.axvline(k - .5, color=FG, ls=(0, (3, 3)), lw=1.1)
fig.text(.045, .192, f"Britain, Y lines of men per 500 years: I2 until 2500 BCE, then R1b", fontproperties=DISPB, fontsize=15, color=FG, va="top")
used = [c for c in YC if any(b["clades"][c] for b in Bn)]
fig.legend(handles=[Patch(color=YCOL[c], label=c) for c in used], loc="upper left", bbox_to_anchor=(.035, .178), ncol=len(used), frameon=False, fontsize=9.5, handletextpad=.4, columnspacing=1.0)

fig.text(.045, .006, f"Source: Allen Ancient DNA Resource (AADR) {s['version']}, Mallick et al., Harvard Dataverse, doi:10.7910/DVN/FFIDCW (CC0). People today: Natural Earth (2019).\n"
         "Kept: individuals with data graded Pass, PROVISIONAL_PASS or MERGE_PASS; Neanderthals and Denisovans left out. Y shares: men whose Y call reaches a major branch.\n"
         "Bars start at the date shown. A haplogroup traces one male line: a proxy for ancestry, not ancestry itself.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/ancient-dna", family=MONO, fontsize=8.2, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ancient_dna_map.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out, [n for n, _ in PLACED])
