"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, and Natural Earth outlines in the Equal Earth projection (world) or a Lambert azimuthal
equal-area projection centred on Europe (Europe maps)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1D2128", "#636A72", "#E2DDD1", "#DDD8CC", "#E6ECEF"
HOT, COOL, GOLD, INK = "#B5402A", "#2F5FA7", "#C9A227", "#3B2A1A"
YCOL = dict(Y_CLADES); MTCOL = dict(MT_CLADES); PCOL = {p[0]: p[3] for p in PERIODS}; RCOL = {r[0]: r[1] for r in REGIONS}

EE = Transformer.from_crs(4326, 8857, always_xy=True)
EU = Transformer.from_crs(4326, "+proj=laea +lat_0=52 +lon_0=15 +ellps=WGS84", always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    for ring in rings(f["geometry"]):
        SHAPES.append((f["properties"]["iso"], ring))
WORLD_EXT = (-17.0e6, 17.0e6, -6.6e6, 8.7e6)
EU_EXT = (-2.75e6, 2.65e6, -2.35e6, 2.05e6)


def proj(lon, lat, t=EE):
    return t.transform(np.asarray(lon, float), np.asarray(lat, float))


def basemap(ax, t=EE, ext=WORLD_EXT, lw=.3, ec="#FFFFFF", land=LAND, z=1, skip_ata=True):
    for iso, ring in SHAPES:
        if skip_ata and iso == "ATA":
            continue
        lo, la = np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5)
        if t is EU and (lo.max() < -40 or lo.min() > 75 or la.max() < 20):
            continue
        x, y = t.transform(lo, la)
        ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0, latmin=-60):
    """Equal Earth outline (cut at latmin, since Antarctica is not drawn)."""
    lat = np.linspace(latmin, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, -180), lat); xr, yr_ = EE.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr_]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def ylab(y):
    return yr(y)
