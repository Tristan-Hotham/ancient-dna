"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; points from data/individuals.csv."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
I = pd.read_csv(f"{DATA}/individuals.csv", keep_default_na=False, na_values=[""])
I = I[I.lat.notna() & (I.archaic == 0)]
HALO = [pe.withStroke(linewidth=3.2, foreground=BG)]
PN = [p[0] for p in PERIODS]


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def place_labels(ax, fig, items, pts, size=9, col=FG):
    """items: (x, y, text). Greedy: try offsets around the point, keep the first box that hits no earlier label or point."""
    fig.canvas.draw(); rr = fig.canvas.get_renderer(); boxes = []
    P = ax.transData.transform(np.column_stack(pts)) if len(pts[0]) else np.zeros((0, 2))
    for x, y, s in items:
        for dx, dy, ha, va in ((7, 0, "left", "center"), (-7, 0, "right", "center"), (0, 8, "center", "bottom"), (0, -8, "center", "top"),
                               (7, 7, "left", "bottom"), (-7, 7, "right", "bottom"), (7, -7, "left", "top"), (-7, -7, "right", "top"),
                               (12, 12, "left", "bottom"), (-12, -12, "right", "top"), (12, -12, "left", "top"), (-12, 12, "right", "bottom"),
                               (0, 22, "center", "bottom"), (0, -22, "center", "top"), (24, -18, "left", "top"), (-24, -18, "right", "top"),
                               (24, 18, "left", "bottom"), (-24, 18, "right", "bottom"), (0, 34, "center", "bottom"), (0, -34, "center", "top")):
            far = abs(dx) + abs(dy) > 25
            t = ax.annotate(s, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, fontsize=size, color=col, path_effects=HALO, zorder=8,
                            arrowprops=dict(arrowstyle="-", color=MUT, lw=.6, shrinkA=1, shrinkB=4) if far else None)
            bb = t.get_window_extent(rr).expanded(1.04, 1.1)
            hitp = ((P[:, 0] > bb.x0 - 3) & (P[:, 0] < bb.x1 + 3) & (P[:, 1] > bb.y0 - 3) & (P[:, 1] < bb.y1 + 3)).any()
            axb = ax.get_window_extent()
            if hitp or any(bb.overlaps(o) for o in boxes) or bb.x0 < axb.x0 or bb.x1 > axb.x1 or bb.y0 < axb.y0 or bb.y1 > axb.y1:
                t.remove(); continue
            boxes.append(bb); break
        else:
            raise RuntimeError("no room for label " + s)


# ---------- 1. world map of everyone, by period ----------
fig = plt.figure(figsize=(12, 6.7), facecolor=BG); ax = fig.add_axes([0, .06, 1, .86])
ax.add_patch(plt.Rectangle((WORLD_EXT[0], WORLD_EXT[2]), WORLD_EXT[1] - WORLD_EXT[0], WORLD_EXT[3] - WORLD_EXT[2], fc=SEA, ec="none", zorder=0)); basemap(ax, ec=BG)
J = I.sort_values("date_mean_bp")   # oldest on top
x, y = proj(J.lon.values, J.lat.values)
ax.scatter(x, y, s=5, c=[PCOL[p] for p in J.period], lw=0, alpha=.85, zorder=3)
fig.text(.02, .955, f"{R['source']['mapped_modern']:,} ancient people in the AADR {R['source']['version']}, placed where they were buried, coloured by when they lived", fontsize=11.5, color=FG)
fig.legend(handles=[Patch(color=PCOL[p], label=p) for p in PN], loc="lower center", ncol=4, frameon=False, fontsize=9.5, bbox_to_anchor=(.5, -.005))
both(fig, "map")

# ---------- 2. the archive: publication years and dates ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.9), facecolor=BG, gridspec_kw={"width_ratios": [1, 1.5]}); fig.subplots_adjust(left=.07, right=.98, wspace=.22, top=.85, bottom=.16)
Pp = pd.DataFrame(R["pubs"]["years"])
a1.bar(Pp.y, Pp.n, color=[HOT if v >= 2020 else INK for v in Pp.y], width=.8); a1.set_facecolor(BG); spines(a1)
a1.set_title("First published, by year", loc="left", fontsize=12, color=FG); a1.set_xticks(range(2010, 2027, 4)); a1.grid(axis="y", color=RULE); a1.set_axisbelow(True)
a1.text(2010.2, Pp.n.max() * .92, f"{R['pubs']['since2020_pct']:.0f}% since 2020", fontsize=10.5, color=HOT)
H = pd.DataFrame(R["half_millennia"])
a2.bar(H.a + 250, H.n, width=450, color=[INK if v < -2500 else GOLD if v < 0 else COOL for v in H.a]); a2.set_facecolor(BG); spines(a2)
a2.set_title("People per 500 years, 10,000 BCE to today", loc="left", fontsize=12, color=FG); a2.grid(axis="y", color=RULE); a2.set_axisbelow(True)
a2.set_xticks(range(-10000, 2001, 2000)); a2.set_xticklabels([ylab(v) if v else "1 CE" for v in range(-10000, 2001, 2000)], fontsize=9.5)
a2.text(-9800, H.n.max() * .92, f"half lived after {yr(R['time']['median_year'])}", fontsize=10.5, color=FG)
both(fig, "archive")

# ---------- 3. sampling bias ----------
B = R["bias_list"]; K3 = [("pct", "Ancient genomes", HOT), ("pop_pct", "People today", COOL), ("land_pct", "Land (without Antarctica)", GOLD)]
fig = plt.figure(figsize=(12, 5.4), facecolor=BG); ax = fig.add_axes([.15, .08, .82, .78]); ax.set_facecolor(BG)
for i, d in enumerate(B):
    for j, (k, n, c) in enumerate(K3):
        yy = i * 1.0 + j * .26
        ax.barh(yy, d[k], height=.24, color=c)
        ax.text(d[k] + .6, yy, f"{d[k]:.1f}%" if d[k] < 10 else f"{d[k]:.0f}%", va="center", fontsize=9.5)
ax.set_yticks([i + .26 for i in range(len(B))]); ax.set_yticklabels([d["cont"] for d in B], fontsize=11); ax.invert_yaxis()
ax.set_xlim(0, 75); ax.set_xticks([0, 25, 50, 75]); ax.set_xticklabels(["0%", "25%", "50%", "75%"]); spines(ax); ax.tick_params(axis="y", length=0)
fig.legend(handles=[Patch(color=c, label=n) for _, n, c in K3], loc="upper left", bbox_to_anchor=(.14, .99), ncol=3, frameon=False, fontsize=10.5)
both(fig, "bias")

# ---------- 4. the first farmers: map and distance ----------
NL = R["neolithic"]; A = pd.DataFrame(NL["countries"])
fig = plt.figure(figsize=(12, 6.4), facecolor=BG)
ax = fig.add_axes([0, .02, .5, .9]); ax.add_patch(plt.Rectangle((EU_EXT[0], EU_EXT[2]), EU_EXT[1] - EU_EXT[0], EU_EXT[3] - EU_EXT[2], fc=SEA, ec="none", zorder=0))
basemap(ax, t=EU, ext=EU_EXT, ec=BG)
cm = plt.get_cmap("YlOrBr_r"); nrm = plt.Normalize(-9000, -3000)
x, y = proj(A.lon.values, A.lat.values, EU)
ax.scatter(x, y, s=70, c=cm(nrm(A.year.values)), ec=FG, lw=.6, zorder=5)
cx, cy = proj([ANATOLIA[1]], [ANATOLIA[0]], EU); ax.scatter(cx, cy, marker="*", s=180, c=HOT, ec="#fff", lw=.8, zorder=6)
place_labels(ax, fig, [(xx, yy, f"{yr(v).replace(' BCE', '')}") for xx, yy, v in zip(x, y, A.year)] + [(cx[0], cy[0], "Çatalhöyük")], (np.r_[x, cx], np.r_[y, cy]), size=8.5)
ax.set_title("Earliest Neolithic burial per country (BCE)", loc="left", fontsize=11.5, color=FG, x=.03, y=.995)
a2 = fig.add_axes([.58, .12, .4, .76]); a2.set_facecolor(BG)
a2.scatter(A.km, A.year, s=40, c=cm(nrm(A.year.values)), ec=FG, lw=.6, zorder=4)
kk = np.array([500, 3800]); a2.plot(kk, NL["intercept"] + NL["slope_yr_per_km"] * kk, ls="--", color=HOT, lw=1.5)
place_labels(a2, fig, [(r.km, r.year, "Britain" if r.country == "United Kingdom" else "N. Macedonia" if r.country == "North Macedonia" else "Channel Is." if r.country == "Channel Islands" else r.country) for r in A.itertuples()], (A.km.values, A.year.values), size=8)
a2.set_xlim(0, 4000); a2.set_ylim(-9200, -2900); spines(a2); a2.grid(color=RULE); a2.set_axisbelow(True)
a2.set_yticks(range(-9000, -2999, 1000)); a2.set_yticklabels([ylab(v) for v in range(-9000, -2999, 1000)], fontsize=9.5)
a2.set_xlabel("km from Çatalhöyük", fontsize=10); a2.set_title(f"About {NL['km_per_year']:.1f} km a year (dashed fit, r = {NL['r']:.2f})", loc="left", fontsize=11.5, color=FG)
both(fig, "farmers")

# ---------- 5. Britain: Y lines by 500 years ----------
YC = [c for c, _ in Y_CLADES]


def stack(ax, reg, a0=-4500, sm=False):
    Bn = [b for b in R["steppe"][reg]["bins"] if b["a"] >= a0]
    for i, b in enumerate(Bn):
        acc = 0
        for c in YC:
            v = b["clades"][c] / b["n"] if b["n"] else 0
            if v:
                ax.bar(i, v * 100, bottom=acc, color=YCOL[c], width=.86, alpha=1 if b["n"] >= 5 else .35); acc += v * 100
        if b["n"]:
            ax.text(i, 102, str(b["n"]), ha="center", fontsize=8.5 if not sm else 7.5, color=MUT)
    ax.set_xticks(range(len(Bn))); ax.set_xticklabels([("1 CE" if b["a"] == 0 else ylab(b["a"])) if b["a"] % 1000 == 0 else "" for b in Bn], fontsize=9)
    ax.set_ylim(0, 108); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0", "25", "50", "75", "100%"]); spines(ax); ax.set_facecolor(BG)
    k = [b["a"] for b in Bn].index(-2500); ax.axvline(k - .5, color=FG, ls=(0, (3, 3)), lw=1.2)
    return Bn


fig = plt.figure(figsize=(12, 5.8), facecolor=BG); ax = fig.add_axes([.06, .17, .92, .64])
stack(ax, "Britain")
br = R["britain"]
fig.text(.06, .955, f"Britain: Y lines of men in each 500 years (number of men above each bar; pale: fewer than five).\nBefore 2500 BCE, 0 of {br['pre_n']} men carry R1b. From 2500 to 1500 BCE, {br['post_r1b_pct']:.0f}% do.", fontsize=11, color=FG, va="top", linespacing=1.5)
used = [c for c in YC if any(b["clades"][c] for b in R["steppe"]["Britain"]["bins"])]
fig.legend(handles=[Patch(color=YCOL[c], label=c) for c in used], loc="lower center", ncol=len(used), frameon=False, fontsize=10, bbox_to_anchor=(.52, -.005))
both(fig, "britain")

# ---------- 6. four regions: R1b + R1a ----------
fig = plt.figure(figsize=(12, 5.2), facecolor=BG); ax = fig.add_axes([.07, .16, .9, .72]); ax.set_facecolor(BG)
for reg, col, desc in REGIONS:
    Bn = [b for b in R["steppe"][reg]["bins"] if b["n"] >= 5 and -5000 <= b["a"] < 1500]
    ax.plot([(b["a"] + b["b"]) / 2 for b in Bn], [b["steppe_pct"] for b in Bn], "-o", color=col, lw=2.4, ms=5, label=f"{reg} ({desc})")
ax.axvline(-2500, color=FG, ls=(0, (3, 3)), lw=1.1); ax.text(-2450, 3, "2500 BCE", fontsize=9.5)
ax.set_xlim(-5000, 1500); ax.set_ylim(0, 102); spines(ax); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.set_xticks(range(-5000, 1501, 1000)); ax.set_xticklabels([ylab(v) if v else "1 CE" for v in range(-5000, 1501, 1000)], fontsize=9.5)
ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0", "25", "50", "75", "100%"]); ax.set_ylabel("men carrying R1b or R1a")
fig.legend(loc="upper left", bbox_to_anchor=(.06, 1.0), ncol=2, frameon=False, fontsize=9.5)
both(fig, "regions")

# ---------- 7. Europe before and after: men's Y lines on the map ----------
M = I[(I.sex == "M") & I.y_clade.notna() & ~I.y_clade.isin(["Too broad"]) & I.lon.between(-12, 45) & I.lat.between(34, 72)]
GRP = [("R1b", YCOL["R1b"]), ("R1a", YCOL["R1a"]), ("I2", YCOL["I2"]), ("G2", YCOL["G2"]), ("Other lines", "#8C8478")]
fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
for k, key in enumerate(("early", "late")):
    E = R["europe_y"][key]; a, b = E["a"], E["b"]
    ax = fig.add_axes([.005 + k * .5, .1, .49, .82]); ax.add_patch(plt.Rectangle((EU_EXT[0], EU_EXT[2]), EU_EXT[1] - EU_EXT[0], EU_EXT[3] - EU_EXT[2], fc=SEA, ec="none", zorder=0))
    basemap(ax, t=EU, ext=EU_EXT, ec=BG)
    d = M[(M.year_ce >= a) & (M.year_ce < b)]
    g = d.y_clade.where(d.y_clade.isin(["R1b", "R1a", "I2", "G2"]), "Other lines")
    order = np.argsort(g.isin(["R1b", "R1a"]).values)
    x, y = proj(d.lon.values[order], d.lat.values[order], EU)
    ax.scatter(x, y, s=14, c=[dict(GRP)[v] for v in g.values[order]], ec="#fff", lw=.3, zorder=4)
    assert len(d) == E["men"]
    ax.set_title(f"{ylab(a)} to {ylab(b)}: {E['men']:,} men, {E['r_pct']:.0f}% R1b or R1a", loc="left", fontsize=11.5, color=FG, x=.03)
fig.legend(handles=[Patch(color=c, label=n) for n, c in GRP], loc="lower center", ncol=5, frameon=False, fontsize=10.5, bbox_to_anchor=(.5, .01))
both(fig, "europe_y")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.42, .05, .57, .9]); ax.add_patch(plt.Rectangle((EU_EXT[0], EU_EXT[2]), EU_EXT[1] - EU_EXT[0], EU_EXT[3] - EU_EXT[2], fc=SEA, ec="none", zorder=0))
basemap(ax, t=EU, ext=EU_EXT, ec=BG, lw=.2)
J = I.sort_values("date_mean_bp"); x, y = proj(J.lon.values, J.lat.values, EU)
ax.scatter(x, y, s=4, c=[PCOL[p] for p in J.period], lw=0, alpha=.9, zorder=3)
fig.text(.04, .87, "Ancient", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.04, .72, "DNA", fontproperties=DISP, fontsize=54, color=HOT, va="top")
fig.text(.04, .57, "on the map", fontproperties=DISP, fontsize=40, color=COOL, va="top")
fig.text(.04, .40, f"{R['source']['kept']:,} ancient genomes, placed where\nand when they lived. Farmers out of\nAnatolia; the steppe after 2500 BCE.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.35)
fig.text(.04, .05, "maps.tristanhotham.com/ancient-dna", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
