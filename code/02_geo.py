"""Geography: a light world outline file for the page and figures (Natural Earth 1:50m), and for every individual with
coordinates the Natural Earth country and continent it falls in (nearest country within 150 km for coastal sites and
small islands). Continents follow Natural Earth's CONTINENT field, except that Russia is split at 60 degrees East, the
line of the Urals: west of it counts as Europe, east of it as Asia. Present-day population (Natural Earth POP_EST,
2019 estimates) and land area (Equal Earth projection, Antarctica left out) are summed by the same continents, with
Russia's area clipped at 60 E and its population split in proportion to the population of its cities and towns
(Natural Earth populated places) on each side of the line."""
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping, Point, box
from shapely.strtree import STRtree
import shapely
from pyproj import Transformer
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
CONT = {"North America": "North America", "South America": "South America", "Europe": "Europe", "Asia": "Asia", "Africa": "Africa",
        "Oceania": "Oceania", "Antarctica": "Antarctica", "Seven seas (open ocean)": "Africa"}   # NE puts a few small islands in 'Seven seas'


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, shp, meta = [], [], []
EET = Transformer.from_crs(4326, 8857, always_xy=True)
EE = lambda c: np.column_stack(EET.transform(c[:, 0], c[:, 1]))
for f in W50["features"]:
    p = f["properties"]; iso = iso_of(p); g = shape(f["geometry"])
    cont = CONT[p["CONTINENT"]]
    shp.append(g); meta.append({"iso": iso, "name": p.get("NAME_EN") or p["NAME"], "cont": cont, "pop": float(p.get("POP_EST") or 0)})
    gs = g.simplify(0.05, preserve_topology=True)
    if not gs.is_empty:
        gm = mapping(gs)
        feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")

# ---- individuals -> country and continent
tree = STRtree(shp)


def locate(lat, lon):
    pt = Point(lon, lat)
    hit = [i for i in tree.query(pt) if shp[i].contains(pt)]
    if hit:
        return hit[0], 0.0
    i = int(tree.nearest(pt)); d = shp[i].distance(pt) * 111.0   # rough km
    return (i, d) if d <= 150 else (None, d)


rows = []
for fn in ("kept", "failed"):
    D = pd.read_pickle(f"{WORK}/{fn}.pkl")
    for r in D[D.lat.notna()].itertuples():
        i, d = locate(r.lat, r.lon)
        if i is None:
            rows.append((fn, r.individual, "", "", d)); continue
        c = meta[i]["cont"]
        if meta[i]["iso"] == "RUS":
            c = "Europe" if r.lon < 60 else "Asia"
        rows.append((fn, r.individual, meta[i]["iso"], c, d))
G = pd.DataFrame(rows, columns=["set", "individual", "ne_iso", "continent", "km_off"])
G.to_pickle(f"{WORK}/geo.pkl")

# ---- population and land by continent
P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
rus = [(f["properties"]["longitude"], f["properties"].get("pop_max") or 0) for f in P["features"] if f["properties"].get("adm0_a3") == "RUS"]
rus_w = sum(p for lo, p in rus if lo < 60) / sum(p for lo, p in rus)
area = {}; pop = {}
for g, m in zip(shp, meta):
    if m["cont"] == "Antarctica":
        continue
    parts = [(m["cont"], g, m["pop"])]
    if m["iso"] == "RUS":
        parts = [("Europe", g.intersection(box(-180, -90, 60, 90)), m["pop"] * rus_w), ("Asia", g.intersection(box(60, -90, 180, 90)), m["pop"] * (1 - rus_w))]
    for c, gg, pp in parts:
        a = shapely.transform(gg, EE).area / 1e6
        area[c] = area.get(c, 0) + a; pop[c] = pop.get(c, 0) + pp
jsave({"area_km2": area, "pop": pop, "rus_west_pop_share": rus_w, "pop_year": 2019}, f"{WORK}/continents.json", indent=1)
k = G[G.set == "kept"]
print("world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB; located", (k.continent != "").sum(), "of", len(k), "unlocated", (k.continent == "").sum(), "max off", round(k.km_off.max()))
print(k.continent.value_counts().to_dict()); print({c: round(100 * v / sum(pop.values()), 1) for c, v in pop.items()}, {c: round(100 * v / sum(area.values()), 1) for c, v in area.items()}, round(rus_w, 3))
print(k[k.continent == ""].head(10))
