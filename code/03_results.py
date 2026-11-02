"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/individuals.json, data/site.json).

Definitions (see 01_clean.py and common.py):
  * individual: one Individual ID with at least one data representation that passes the AADR assessment;
  * modern humans: everyone except the archaic (Neanderthal and Denisovan) individuals, which are counted apart;
  * year: 1950 minus the date mean in BP; BCE years are negative inside the code;
  * Y shares: men (molecular sex M) whose Y call reaches a major clade (R1b, R1a, I2...); calls too broad to tell R1a
    or R1b apart (CT, F, K, P, R, R1...) are left out of the denominator. Haplogroups are a proxy for ancestry, not
    ancestry itself: one paternal line out of thousands of ancestors;
  * Neolithic arrival: individuals whose Group ID carries a Neolithic word (common.CULTURES), in Europe and Anatolia
    (latitude 30 to 72, longitude -12 to 45), leaving out Russia, Ukraine, Belarus, Moldova, the Baltic states and
    Finland, where 'Neolithic' in the archive's labels mostly means pottery-making hunter-gatherers rather than farmers,
    and leaving out groups whose label also carries a hunter-gatherer word (Mesolithic, HG, Swifterbant, Ertebolle, Pitted
    Ware), dates with a standard deviation over 300 years, and dates whose mean falls outside their own date range
    (common date_ok check in 01_clean.py); for each country with at least three left the earliest such individual (by date mean), its distance from Catalhoyuk in central Anatolia."""
import numpy as np, pandas as pd
from common import *

K = pd.read_pickle(f"{WORK}/kept.pkl")
X = pd.read_pickle(f"{WORK}/failed.pkl")
G = pd.read_pickle(f"{WORK}/geo.pkl")
CHK = jload(f"{WORK}/checks.json")
CN = jload(f"{WORK}/continents.json")
geo_k = G[G.set == "kept"].set_index("individual")
K["continent"] = K.individual.map(geo_k.continent).fillna("")
K["ne_iso"] = K.individual.map(geo_k.ne_iso).fillna("")
H = K[K.archaic == 0]                       # modern humans
pc = lambda a, b: round(100 * a / b, 2) if b else None
R = {}

# ---------- source and filter ----------
s = {"rows": CHK["rows"], "present_day_rows": CHK["present_day_rows"], "ancient_rows": CHK["ancient_rows"],
     "ancient_individuals": CHK["ancient_individuals"], "kept": CHK["kept"], "failed": CHK["failed"], "strict_kept": CHK["strict_kept"],
     "rescued": CHK["rescued_by_other_row"], "archaic": int(K.archaic.sum()), "modern": len(H),
     "no_coords": CHK["kept_no_coords"], "mapped": int(K.lat.notna().sum()), "mapped_modern": int(H.lat.notna().sum()),
     "failed_mapped": int(X.lat.notna().sum()), "kept_pct": pc(CHK["kept"], CHK["ancient_individuals"]),
     "n_groups": int(K.group.nunique()), "n_sites": int(K.locality.nunique()), "n_countries": int(K.country[K.country != ".."].nunique()),
     "n_pubs": int(K.publication.nunique()), "version": AADR_VER, "doi": AADR_DOI, "paper_doi": PAPER_DOI,
     "assess": {k: int(v) for k, v in K.assessment.str.extract(r"^(MERGE_PASS|PROVISIONAL_PASS|Pass)")[0].value_counts().items()},
     "multi_rows": int(CHK["ancient_rows"] - CHK["ancient_individuals"]), "y_manual": CHK["y_manual_used"], "checks": CHK}
R["source"] = s
assert s["ancient_rows"] == 19118 and s["ancient_individuals"] == 17629 and s["kept"] + s["failed"] == s["ancient_individuals"]
assert sum(s["assess"].values()) == s["kept"]

# ---------- sex ----------
sx = K.sex.value_counts()
R["sex"] = {"M": int(sx.get("M", 0)), "F": int(sx.get("F", 0)), "U": int(sx.get("U", 0))}
R["sex"].update({k + "_pct": pc(v, len(K)) for k, v in list(R["sex"].items())})
R["sex"]["m_per_f"] = round(R["sex"]["M"] / R["sex"]["F"], 2)

# ---------- time ----------
Hs = H.sort_values("bp", ascending=False)
fam_ids = {"Ust_Ishim": "Ust'-Ishim man", "ZKU002": "Zlatý kůň woman", "Oase1": "Oase 1", "Kostenki14": "Kostenki 14", "Tianyuan": "Tianyuan man", "Sunghir1": "Sunghir 1"}


def ind_row(r):
    return {"id": r.individual, "group": r.group, "site": r.locality, "country": r.country, "bp": int(r.bp), "year": int(r.year), "yr": yr(r.year),
            "date": r.datestr, "sex": r.sex, "y": r.y_call, "mt": r.mt_call, "pub": r.publication, "first_pub": r.first_pub,
            "pub_year": None if pd.isna(r.pub_year) else int(r.pub_year), "lat": None if np.isnan(r.lat) else round(float(r.lat), 3),
            "lon": None if np.isnan(r.lon) else round(float(r.lon), 3), "culture": r.culture}


R["oldest"] = [ind_row(r) for r in Hs.head(12).itertuples()]
A_ = K[K.archaic == 1].sort_values("bp", ascending=False)
R["archaic"] = [ind_row(r) for r in A_.itertuples()]
R["archaic_failed"] = [ind_row(r) for r in X[X.archaic == 1].sort_values("bp", ascending=False).itertuples()]
yrs = H.year
R["time"] = {"oldest_bp": int(H.bp.max()), "oldest_year": int(1950 - H.bp.max()), "oldest_id": Hs.iloc[0].individual, "oldest_group": Hs.iloc[0].group,
             "youngest_bp": int(H.bp.min()), "youngest_year": int(1950 - H.bp.min()), "archaic_oldest_bp": int(A_.bp.max()),
             "median_year": int(round(yrs.median())), "n_before_10000bce": int((yrs < -10000).sum()), "n_before_5000bce": int((yrs < -5000).sum()),
             "pct_after_3000bce": pc((yrs >= -3000).sum(), len(H)), "pct_after_1bce": pc((yrs >= 0).sum(), len(H)),
             "pct_last_10000": pc((H.bp <= 10000).sum(), len(H)), "n_over_40000bp": int((H.bp > 40000).sum()), "n_over_20000bp": int((H.bp > 20000).sum())}
R["time"]["oldest_k"] = int(H.bp.max() // 1000) * 1000
assert R["time"]["oldest_bp"] > 44000
# counts by millennium (BCE negative) for the histogram, and by 500 years for the last 10,000
mil = []
for a in range(-45000, 2000, 1000):
    n = int(((yrs >= a) & (yrs < a + 1000)).sum())
    mil.append({"a": a, "b": a + 1000, "n": n})
R["millennia"] = mil
half = []
for a in range(-10000, 2000, 500):
    half.append({"a": a, "b": a + 500, "n": int(((yrs >= a) & (yrs < a + 500)).sum())})
R["half_millennia"] = half
R["periods"] = [{"name": n, "n": int((H.period == n).sum())} for n, *_ in PERIODS]
R["cultures"] = [{"name": n, "n": int((K.culture == n).sum())} for n, *_ in CULTURES] + [{"name": CULTURE_OTHER[0], "n": int((K.culture == CULTURE_OTHER[0]).sum())}]

# ---------- publication years ----------
py = K.pub_year.dropna().astype(int).value_counts().sort_index()
R["pubs"] = {"years": [{"y": int(y), "n": int(py.get(y, 0))} for y in range(int(py.index.min()), int(py.index.max()) + 1)], "since2020": int(K.pub_year.ge(2020).sum()),
             "since2020_pct": pc(K.pub_year.ge(2020).sum(), K.pub_year.notna().sum()), "before2015": int(K.pub_year.lt(2015).sum()),
             "y2025": int((K.pub_year == 2025).sum()), "no_year": int(K.pub_year.isna().sum()), "first_year": int(py.index.min()),
             "top": [{"pub": p, "n": int(n)} for p, n in K.publication.value_counts().head(10).items()]}

# ---------- countries and sites ----------
cc = K[K.country != ".."].country.value_counts()
R["countries"] = [{"country": c, "n": int(n), "pct": pc(n, len(K))} for c, n in cc.items()]
R["top_countries"] = R["countries"][:20]
R["n_countries_100"] = int((cc >= 100).sum())
st = []
for loc, d in K[K.lat.notna()].groupby("locality"):
    st.append({"site": loc, "n": len(d), "country": d.country.iloc[0], "lat": round(float(d.lat.median()), 3), "lon": round(float(d.lon.median()), 3),
               "y0": int(d.year.min()), "y1": int(d.year.max()), "group": d.group.value_counts().index[0], "culture": d.culture.value_counts().index[0]})
ST = pd.DataFrame(st).sort_values("n", ascending=False)
R["sites"] = ST.head(15).to_dict("records")
R["avar_sites"] = {"y0": int(min(r["y0"] for r in R["sites"][:2])), "y1": int(max(r["y1"] for r in R["sites"][:2]))}
R["sites_one"] = int((ST.n == 1).sum()); R["sites_n"] = len(ST); R["sites_one_pct"] = pc((ST.n == 1).sum(), len(ST))
ST.to_csv(f"{DATA}/sites.csv", index=False)

# ---------- sampling bias ----------
CONTS = ["Europe", "Asia", "Africa", "North America", "South America", "Oceania"]
loc = H[H.continent != ""]
tp, ta = sum(CN["pop"].values()), sum(CN["area_km2"].values())
bias = []
for c in CONTS:
    n = int((loc.continent == c).sum())
    bias.append({"cont": c, "n": n, "pct": pc(n, len(loc)), "pop_pct": round(100 * CN["pop"][c] / tp, 2), "land_pct": round(100 * CN["area_km2"][c] / ta, 2),
                 "per_10m_people": round(n / (CN["pop"][c] / 1e7), 1), "per_100k_km2": round(n / (CN["area_km2"][c] / 1e5), 1)})
R["bias"] = {r["cont"]: r for r in bias}; R["bias_list"] = bias
eu = R["bias"]["Europe"]
R["bias_sum"] = {"n_located": len(loc), "eu_pct": eu["pct"], "eu_pop_pct": eu["pop_pct"], "eu_land_pct": eu["land_pct"],
                 "eu_x_pop": round(eu["pct"] / eu["pop_pct"], 1), "eu_x_land": round(eu["pct"] / eu["land_pct"], 1),
                 "africa_pct": R["bias"]["Africa"]["pct"], "africa_pop_pct": R["bias"]["Africa"]["pop_pct"],
                 "asia_pct": R["bias"]["Asia"]["pct"], "asia_pop_pct": R["bias"]["Asia"]["pop_pct"],
                 "eu_vs_africa_per_person": round(eu["per_10m_people"] / R["bias"]["Africa"]["per_10m_people"]),
                 "rus_west_pop_share": round(CN["rus_west_pop_share"] * 100, 1), "pop_year": CN["pop_year"]}
# European share through time (by period) to show the bias is everywhere
R["bias_period"] = [{"name": n, "n": int(((loc.period == n)).sum()), "eu_pct": pc(((loc.period == n) & (loc.continent == "Europe")).sum(), (loc.period == n).sum())} for n, *_ in PERIODS]
pd.DataFrame(bias).to_csv(f"{DATA}/continents.csv", index=False)
assert eu["pct"] > 60 and eu["pop_pct"] < 12

# ---------- Y clades ----------
M = H[(H.sex == "M")]
My = M[(M.y_clade != "") & (M.y_clade != "Too broad")]
R["y"] = {"men": len(M), "resolved": len(My), "too_broad": int((M.y_clade == "Too broad").sum()), "no_call": int((M.y_clade == "").sum()),
          "clades": {c: int((My.y_clade == c).sum()) for c, _ in Y_CLADES}}
R["y"]["resolved_pct"] = pc(len(My), len(M))
mt = H[H.mt_clade != ""]
R["mt"] = {"n": len(mt), "pct": pc(len(mt), len(H)), "clades": {c: int((mt.mt_clade == c).sum()) for c, _ in MT_CLADES}}

# ---------- the steppe: R1b and R1a by region and half millennium ----------
EDGES = list(range(-7000, 2001, 500))
steppe = {}
rows = []
for reg, col, desc in REGIONS:
    d = My[My.region == reg]; bins = []
    for a, b in zip(EDGES[:-1], EDGES[1:]):
        x = d[(d.year >= a) & (d.year < b)]
        cnt = {c: int((x.y_clade == c).sum()) for c, _ in Y_CLADES}
        bins.append({"a": a, "b": b, "n": len(x), "r1b": cnt["R1b"], "r1a": cnt["R1a"], "r1b_pct": pc(cnt["R1b"], len(x)), "r1a_pct": pc(cnt["R1a"], len(x)),
                     "steppe_pct": pc(cnt["R1b"] + cnt["R1a"], len(x)), "clades": cnt})
        rows.append({"region": reg, "from_year": a, "to_year": b, "men": len(x), **{c: cnt[c] for c, _ in Y_CLADES}})
    early = d[d.year < -3000]; mid = d[(d.year >= -2500) & (d.year < -1500)]
    steppe[reg] = {"desc": desc, "men": len(d), "bins": bins, "pre3000_n": len(early), "pre3000_r": int(early.y_clade.isin(["R1b", "R1a"]).sum()),
                   "pre3000_pct": pc(early.y_clade.isin(["R1b", "R1a"]).sum(), len(early)),
                   "ba_n": len(mid), "ba_r": int(mid.y_clade.isin(["R1b", "R1a"]).sum()), "ba_pct": pc(mid.y_clade.isin(["R1b", "R1a"]).sum(), len(mid)),
                   "ba_r1b_pct": pc((mid.y_clade == "R1b").sum(), len(mid)), "ba_r1a_pct": pc((mid.y_clade == "R1a").sum(), len(mid))}
R["steppe"] = steppe
pd.DataFrame(rows).to_csv(f"{DATA}/y_clades_by_region.csv", index=False)
B = My[My.region == "Britain"]
pre, post = B[B.year < -2500], B[(B.year >= -2500) & (B.year < -1500)]
r1b_b = B[B.y_clade == "R1b"].sort_values("year")
first = r1b_b.iloc[0]
R["britain"] = {"pre_n": len(pre), "pre_r1b": int((pre.y_clade == "R1b").sum()), "pre_r1a": int((pre.y_clade == "R1a").sum()),
                "pre_i2": int((pre.y_clade == "I2").sum()), "pre_i2_pct": pc((pre.y_clade == "I2").sum(), len(pre)),
                "post_n": len(post), "post_r1b": int((post.y_clade == "R1b").sum()), "post_r1b_pct": pc((post.y_clade == "R1b").sum(), len(post)),
                "first_r1b_id": first.individual, "first_r1b_group": first.group, "first_r1b_year": int(first.year), "first_r1b_date": first.datestr,
                "first_r1b_site": first.locality, "men": len(B),
                "neo_n": int(((B.year >= -4000) & (B.year < -2500)).sum()),
                "ia_n": int(((B.year >= -800) & (B.year < 43)).sum()), "ia_r1b_pct": pc(((B.year >= -800) & (B.year < 43) & (B.y_clade == "R1b")).sum(), ((B.year >= -800) & (B.year < 43)).sum()),
                "em_n": int(((B.year >= 400) & (B.year < 1066)).sum()), "em_r1b_pct": pc(((B.year >= 400) & (B.year < 1066) & (B.y_clade == "R1b")).sum(), ((B.year >= 400) & (B.year < 1066)).sum()),
                "em_i1_pct": pc(((B.year >= 400) & (B.year < 1066) & (B.y_clade == "I1")).sum(), ((B.year >= 400) & (B.year < 1066)).sum())}
br = R["britain"]
assert br["pre_r1b"] == 0 and br["post_r1b_pct"] > 80 and br["pre_n"] >= 50
# Beaker-tagged men in Britain
bb = B[B.culture == "Bell Beaker"]
br["beaker_n"] = len(bb); br["beaker_r1b"] = int((bb.y_clade == "R1b").sum())
# men in a Europe box (lon -12 to 45, lat 34 to 72) before and after, for the before and after maps
EB = My[My.lon.between(-12, 45) & My.lat.between(34, 72)]
R["europe_y"] = {}
for k, (a, b) in {"early": (-5000, -3000), "late": (-2500, -1500)}.items():
    d = EB[(EB.year >= a) & (EB.year < b)]
    R["europe_y"][k] = {"a": a, "b": b, "men": len(d), "r_pct": pc(d.y_clade.isin(["R1b", "R1a"]).sum(), len(d)),
                        "r1b": int((d.y_clade == "R1b").sum()), "r1a": int((d.y_clade == "R1a").sum()),
                        "i2g2_pct": pc(d.y_clade.isin(["I2", "G2"]).sum(), len(d))}
Sc = My[(My.region == "Scandinavia") & (My.year >= 1) & (My.year < 1000)]
R["scand_i1"] = {"men": len(Sc), "i1_pct": pc((Sc.y_clade == "I1").sum(), len(Sc))}
# whole of Europe-wide summary of first R1b or R1a after the steppe arrival per region (first bin where steppe share >= 50%)
for reg in steppe:
    b50 = next((b for b in steppe[reg]["bins"] if b["n"] >= 5 and b["steppe_pct"] >= 50), None)
    steppe[reg]["first50"] = b50["a"] if b50 else None
# Yamnaya and Corded Ware men anywhere
for cname, key in (("Yamnaya", "yamnaya"), ("Corded Ware", "corded"), ("Bell Beaker", "beaker")):
    d = My[My.culture == cname]
    R[key] = {"men": len(d), "r1b": int((d.y_clade == "R1b").sum()), "r1a": int((d.y_clade == "R1a").sum()),
              "r1b_pct": pc((d.y_clade == "R1b").sum(), len(d)), "r1a_pct": pc((d.y_clade == "R1a").sum(), len(d)), "all": int((H.culture == cname).sum()),
              "q10": int(H[H.culture == cname].year.quantile(.1)), "q90": int(H[H.culture == cname].year.quantile(.9))}
# farmers' G2 in the Neolithic of Europe
NE_ = My[(My.culture == "Neolithic") & (My.continent == "Europe")]
R["neo_y"] = {"men": len(NE_), "g2_pct": pc((NE_.y_clade == "G2").sum(), len(NE_)), "i2_pct": pc((NE_.y_clade == "I2").sum(), len(NE_)),
              "r_pct": pc(NE_.y_clade.isin(["R1b", "R1a"]).sum(), len(NE_))}

TN = My[(My.culture == "Neolithic") & (My.country == "Turkey")]
R["anatolia_y"] = {"men": len(TN), "top": TN.y_clade.value_counts().index[0], "top_pct": pc(TN.y_clade.value_counts().iloc[0], len(TN)),
                   "g2_pct": pc((TN.y_clade == "G2").sum(), len(TN))}

# ---------- Neolithic arrival ----------
EXCL = {"Russia", "Ukraine", "Belarus", "Moldova", "Latvia", "Lithuania", "Estonia", "Finland"}


def gc_km(lat1, lon1, lat2, lon2):
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


N0 = H[(H.culture == "Neolithic") & H.lat.notna() & H.lat.between(30, 72) & H.lon.between(-12, 45) & ~H.country.isin(EXCL)].copy()
N0 = N0[N0.continent.isin(["Europe", "Asia"]) & ((N0.continent == "Europe") | N0.country.isin(["Turkey", "Cyprus"]))]
N_all = len(N0)
mixed = N0.group.str.contains(r"Mesolithic|HG|Swifterbant|Ertebolle|PittedWare", case=False)
N0 = N0[~mixed & (N0.sd <= 300) & (N0.date_ok == 1)].copy()
N_drop = {"mixed_label": int(mixed.sum()), "after": len(N0), "before": N_all}
N0["km"] = gc_km(N0.lat.values, N0.lon.values, *ANATOLIA)
arr = []
for c, d in N0.groupby("country"):
    if len(d) < 3:
        continue
    e = d.sort_values(["year", "individual"]).iloc[0]
    arr.append({"country": c, "n": len(d), "year": int(e.year), "yr": yr(e.year), "id": e.individual, "group": e.group, "site": e.locality,
                "lat": round(float(e.lat), 3), "lon": round(float(e.lon), 3), "km": round(float(e.km)), "date": e.datestr,
                "median_year": int(round(d.year.median()))})
ARR = pd.DataFrame(arr).sort_values("year")
ARR.to_csv(f"{DATA}/neolithic_arrival.csv", index=False)
fit = ARR[ARR.country != "Turkey"]
sl, ic = np.polyfit(fit.km.values, fit.year.values, 1)
r = float(np.corrcoef(fit.km.values, fit.year.values)[0, 1])
R["neolithic"] = {"countries": ARR.to_dict("records"), "n_countries": len(ARR), "n_ind": len(N0), "slope_yr_per_km": round(float(sl), 3),
                  "km_per_year": round(float(1 / sl), 2), "drop": N_drop, "r": round(r, 2), "r2": round(r * r, 2), "intercept": round(float(ic)),
                  "first": ARR.iloc[0].to_dict(), "last": ARR.iloc[-1].to_dict(), "excluded": sorted(EXCL),
                  "turkey_year": int(ARR[ARR.country == "Turkey"].year.iloc[0]),
                  "span_years": int(ARR.year.max() - ARR.year.min()),
                  "ireland_gap": int(ARR[ARR.country == "Ireland"].year.iloc[0] - ARR[ARR.country == "Turkey"].year.iloc[0])}
AR = {a["country"]: a for a in arr}
R["neolithic"]["by_country"] = AR
nb = []
for la in range(35, 65, 5):
    d = N0[(N0.lat >= la) & (N0.lat < la + 5)]
    if len(d) >= 3:
        e = d.sort_values("year").iloc[0]
        nb.append({"lat0": la, "lat1": la + 5, "n": len(d), "year": int(e.year), "yr": yr(e.year), "country": e.country, "site": e.locality, "group": e.group})
R["neolithic"]["lat_bands"] = nb
lb = []
for lo in range(-10, 45, 10):
    d = N0[(N0.lon >= lo) & (N0.lon < lo + 10)]
    if len(d) >= 3:
        e = d.sort_values("year").iloc[0]
        lb.append({"lon0": lo, "lon1": lo + 10, "n": len(d), "year": int(e.year), "yr": yr(e.year), "country": e.country, "site": e.locality})
R["neolithic"]["lon_bands"] = lb
assert R["neolithic"]["r"] > 0.7 and AR["Turkey"]["year"] < -8000

# ---------- famous and striking individuals ----------
FAM = [("Iceman", "Ötzi the Iceman", "Found in 1991 melting out of a glacier in the Ötztal Alps"),
       ("Ust_Ishim", "Ust'-Ishim man", "A thigh bone found on the bank of the Irtysh river in Siberia in 2008"),
       ("ZKU002", "The woman from Zlatý kůň", "A skull from a cave in Bohemia"),
       ("Oase1", "Oase 1", "A jawbone from a cave in Romania"),
       ("Kostenki14", "Kostenki 14", "A man buried on the Don river"),
       ("Tianyuan", "Tianyuan man", "From a cave near Beijing"),
       ("Sunghir1", "Sunghir 1", "One of the richly beaded burials at Sunghir, east of Moscow"),
       ("MA1", "The Mal'ta boy", "A child buried near Lake Baikal"),
       ("Loschbour", "Loschbour man", "A hunter from Luxembourg"),
       ("LaBrana1", "La Braña 1", "A hunter from the mountains of León"),
       ("Stuttgart", "Stuttgart woman", "An early farmer from Baden-Württemberg"),
       ("I3016", "The man from Gough's Cave, Cheddar", "Gough's Cave in Cheddar Gorge, Somerset, is where Cheddar Man was found in 1903"),
       ("mota", "Mota man", "From Mota Cave in the Ethiopian highlands"),
       ("Inuk", "Inuk, the Saqqaq man", "Known from a tuft of hair preserved in Greenland's permafrost"),
       ("Anzick", "The Anzick child", "The only known Clovis burial, in Montana"),
       ("kennewick", "Kennewick Man", "Found on the bank of the Columbia River in 1996")]
fam = []
allr = pd.concat([K, X])
for i, nm, note in FAM:
    d = allr[allr.individual == i]
    if not len(d):
        continue
    r0 = d.iloc[0]; row = ind_row(r0); row.update({"name": nm, "note": note, "ok": int(r0.ok), "assessment": r0.assessment.split(" ")[0][:40]})
    fam.append(row)
R["famous"] = fam
FM = {f["id"]: f for f in fam}
assert FM["Iceman"]["ok"] == 1 and FM["Iceman"]["group"].startswith("Italy") and FM["kennewick"]["ok"] == 0 and FM["Anzick"]["ok"] == 0
assert FM["Ust_Ishim"]["ok"] == 1 and FM["I3016"]["site"].startswith("Gough")
R["iceman"] = {k: FM["Iceman"][k] for k in ("year", "yr", "date", "y", "group", "site")}
R["iceman"]["y_clade"] = yclade(FM["Iceman"]["y"])
R["iceman"]["bp"] = FM["Iceman"]["bp"]

# ---------- page data ----------
YC = [c for c, _ in Y_CLADES] + ["Too broad"]; YI = {c: i for i, c in enumerate(YC)}
MC = [c for c, _ in MT_CLADES]; MI = {c: i for i, c in enumerate(MC)}
CU = [c[0] for c in CULTURES] + [CULTURE_OTHER[0]]; CI = {c: i for i, c in enumerate(CU)}
PE = [p[0] for p in PERIODS]; PI = {p: i for i, p in enumerate(PE)}
ALL = pd.concat([K.assign(ok=1), X.assign(ok=0)])
ALL = ALL[ALL.lat.notna()].sort_values("bp", ascending=False).reset_index(drop=True)
grp = sorted(ALL.group.unique()); GI = {g: i for i, g in enumerate(grp)}
sit = sorted(ALL.locality.unique()); SI = {g: i for i, g in enumerate(sit)}
cty = sorted(ALL.country.unique()); TI = {g: i for i, g in enumerate(cty)}
pub = sorted(ALL.publication.unique()); BI = {g: i for i, g in enumerate(pub)}
rows = []
for r in ALL.itertuples():
    rows.append([r.individual, GI[r.group], SI[r.locality], TI[r.country], round(float(r.lat), 3), round(float(r.lon), 3), int(r.bp), r.datestr,
                 r.sex, r.y_call, YI.get(r.y_clade, -1) if r.y_clade else -1, r.mt_call, MI.get(r.mt_clade, -1) if r.mt_clade else -1,
                 CI[r.culture], PI[r.period], BI[r.publication], int(r.ok), int(r.archaic)])
jsave({"cols": ["id", "group", "site", "country", "lat", "lon", "bp", "date", "sex", "y", "yc", "mt", "mc", "cu", "pe", "pub", "ok", "arch"],
       "groups": grp, "sites": sit, "countries": cty, "pubs": pub, "rows": rows}, f"{DATA}/individuals.json")
site = {"y": [[c, col] for c, col in Y_CLADES] + [["Too broad", "#E4E0D8"]], "mt": [[c, col] for c, col in MT_CLADES],
        "cu": [[c[0], c[1]] for c in CULTURES] + [list(CULTURE_OTHER)], "pe": [[p[0], p[3]] for p in PERIODS],
        "regions": [[n, c, d] for n, c, d in REGIONS], "anatolia": list(ANATOLIA)}
jsave(site, f"{DATA}/site.json")

# ---------- clean data out ----------
cols = ["individual", "genetic_id", "group", "locality", "country", "lat", "lon", "bp", "sd", "year", "datestr", "sex", "y_call", "y_manual", "y_clade",
        "mt_call", "mt_clade", "period", "culture", "region", "continent", "archaic", "publication", "first_pub", "pub_year", "snp", "assessment"]
K.sort_values("bp", ascending=False)[cols].rename(columns={"locality": "site", "country": "political_entity", "bp": "date_mean_bp", "sd": "date_sd",
                                                          "year": "year_ce", "datestr": "date", "snp": "snps_1240k"}).to_csv(f"{DATA}/individuals.csv", index=False)
X.sort_values("bp", ascending=False)[[c for c in cols if c != "continent"]].rename(columns={"locality": "site", "country": "political_entity", "bp": "date_mean_bp",
                                                                                         "sd": "date_sd", "year": "year_ce", "datestr": "date", "snp": "snps_1240k"}).to_csv(f"{DATA}/failed_quality_individuals.csv", index=False)
pd.DataFrame(R["countries"]).to_csv(f"{DATA}/countries.csv", index=False)
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "aadr_url": AADR_URL}
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("individuals.json", "site.json", "results.json", "individuals.csv")})
print(R["source"]["kept"], R["source"]["archaic"], R["time"]); print(R["sex"]); print(R["bias_sum"]); print([(b["cont"], b["pct"], b["pop_pct"], b["land_pct"]) for b in bias])
print({k: (v["pre3000_n"], v["pre3000_pct"], v["ba_n"], v["ba_pct"], v["first50"]) for k, v in steppe.items()}); print(R["britain"])
print({k: R[k] for k in ("yamnaya", "corded", "beaker", "neo_y")})
print(ARR[["country", "n", "year", "km", "group"]].to_string()); print(R["neolithic"]["km_per_year"], R["neolithic"]["r"]); print(nb); print(lb)
print(R["top_countries"][:10]); print([(x["site"][:40], x["n"]) for x in R["sites"]]); print(R["pubs"]["since2020_pct"]); print([(f["name"], f["ok"], f["yr"]) for f in fam])
print(R["oldest"][:5]); print(R["y"]); print(R["iceman"])
