"""Read the AADR v66.p1 annotation file and make one clean row per ancient individual.

Steps (counts are written to WORK/checks.json and reported in results.json):
  1. Read all rows (one per data representation: capture, shotgun, merged...). Strip quotes and spaces.
  2. Ancient: date mean in BP (column 11) greater than 0. Present-day people have 0.
  3. Individuals: rows are grouped by Individual ID (column 3).
  4. Quality: a row passes if its ASSESSMENT (column 48) starts with Pass, PROVISIONAL_PASS or MERGE_PASS.
     An individual is kept if at least one of its rows passes; the passing row with the most SNPs hit on the 1240k set
     (column 27) represents it. (For comparison I also count the stricter reading: take each individual's row with the
     most SNPs first, then apply the filter.) Individuals with no passing row are kept aside in a separate file, with
     their best row, so the page can show them on request; they are not in any count or share.
  5. Archaic humans: Group ID containing Neanderthal or Denisova, dated before 40,000 BP. Flagged; kept out of the modern human analyses.
  6. Derived fields: calendar year (1950 - BP), broad period, culture tag (common.culture), Y major clade
     (common.yclade, using the hand call in column 37 when there is one), mtDNA macro-haplogroup (common.mtclade),
     region for the steppe story (common.region_of).
Coordinates: latitude and longitude as given; 89 ancient rows have none and are left off the map (counted)."""
import numpy as np, pandas as pd
from common import *

raw = pd.read_csv(ANNO, sep="\t", dtype=str, keep_default_na=False, quoting=3)
hdr = list(raw.columns)
assert len(hdr) == 49 and hdr[2] == "Individual ID" and hdr[14] == "Group ID" and hdr[47] == "ASSESSMENT", hdr[:3]
raw.columns = [f"c{i}" for i in range(1, 50)]
raw = raw.apply(lambda s: s.str.strip().str.strip('"').str.strip())
chk = {"rows": len(raw), "cols": len(hdr)}
raw["bp"] = pd.to_numeric(raw.c11, errors="coerce")
raw["sd"] = pd.to_numeric(raw.c12, errors="coerce")
raw["snp"] = pd.to_numeric(raw.c27, errors="coerce").fillna(0)
assert raw.bp.notna().all()
chk["present_day_rows"] = int((raw.bp == 0).sum())
A = raw[raw.bp > 0].copy()
chk["ancient_rows"] = len(A)
chk["ancient_individuals"] = int(A.c3.nunique())
A["pass"] = A.c48.map(lambda s: s.startswith(PASS_PREFIX)).astype(int)
chk["assessment_rows"] = A.c48.value_counts().to_dict()
chk["pass_rows"] = int(A["pass"].sum())

# stricter reading: best row first, then the filter
best_any = A.sort_values(["c3", "snp"], ascending=[True, False]).drop_duplicates("c3")
chk["strict_kept"] = int(best_any["pass"].sum())
chk["assessment_best_row"] = best_any.c48.value_counts().to_dict()

# main reading: an individual passes if any of its rows passes; take the passing row with most SNPs
P = A[A["pass"] == 1].sort_values(["c3", "snp"], ascending=[True, False]).drop_duplicates("c3")
chk["kept"] = len(P)
F = best_any[~best_any.c3.isin(P.c3)].copy()
chk["failed"] = len(F)
assert chk["kept"] + chk["failed"] == chk["ancient_individuals"]
chk["rescued_by_other_row"] = int(len(set(P.c3) - set(best_any[best_any["pass"] == 1].c3)))
# sanity: same individual, same dates and group across its rows?
g = A.groupby("c3").agg(nb=("bp", "nunique"), ng=("c15", "nunique"))
chk["ind_multi_date"] = int((g.nb > 1).sum()); chk["ind_multi_group"] = int((g.ng > 1).sum())
chk["rows_per_individual_max"] = int(A.groupby("c3").size().max())


def tidy(D, ok):
    D = D.copy()
    D["lat"] = pd.to_numeric(D.c18, errors="coerce"); D["lon"] = pd.to_numeric(D.c19, errors="coerce")
    D.loc[(D.lat.abs() > 90) | (D.lon.abs() > 180), ["lat", "lon"]] = np.nan
    D["year"] = 1950 - D.bp
    D["archaic"] = (D.c15.str.contains(ARCHAIC_RE) & (D.bp > ARCHAIC_MIN_BP)).astype(int)
    D["sex"] = D.c31.str[0].map({"M": "M", "F": "F"}).fillna("U")
    yh = D.c37.map(yclean)
    D["y_call"] = np.where(yh != "", yh, D.c36.map(yclean))
    D["y_manual"] = (yh != "").astype(int)
    D.loc[D.sex != "M", "y_call"] = ""            # Y calls only for molecular males
    D["y_clade"] = D.y_call.map(yclade)
    D["mt_call"] = D.c39.where(~D.c39.str.startswith((".", "n/a")) & ~D.c39.isin(["NA", "na"]), "")
    D["mt_clade"] = D.mt_call.map(mtclade)
    D["period"] = D.year.map(period)
    D["culture"] = [culture(g if a else re.sub(ARCHAIC_RE, "", g)) for g, a in zip(D.c15, D.archaic)]   # archaic tag only for archaic humans
    D["region"] = [region_of(e, g, la) for e, g, la in zip(D.c17, D.c15, D.lat)]
    D["ok"] = ok
    D["first_pub"] = D.c6
    D["pub_year"] = pd.to_numeric(D.c6.str.extract(r"((?:19|20)\d\d)(?!.*(?:19|20)\d\d)")[0], errors="coerce")
    D["datestr"] = D.c13.str.replace(r"\s*\[.*$", "", regex=True).str.strip()
    D = D.rename(columns={"c1": "genetic_id", "c3": "individual", "c7": "publication", "c15": "group", "c16": "locality", "c17": "country",
                          "c36": "y_isogg_auto", "c37": "y_manual_raw", "c39": "mt_raw", "c48": "assessment", "c13": "date_full", "c31": "sex_raw"})
    return D[["individual", "genetic_id", "group", "locality", "country", "lat", "lon", "bp", "sd", "year", "date_full", "datestr", "sex", "sex_raw",
              "y_call", "y_manual", "y_clade", "mt_call", "mt_clade", "period", "culture", "region", "archaic", "publication", "first_pub", "pub_year", "snp", "assessment", "ok"]]


DPAT = re.compile(r"^(\d+)\s*(?:cal)?\s*(BCE|CE)?\s*[-–]\s*(\d+)\s*(?:cal)?\s*(BCE|CE)")


def date_ok(s, y):
    """0 if the full date string is a range and the date mean falls more than 100 years outside it, else 1."""
    m = DPAT.match(s or "")
    if not m:
        return 1
    a, b = int(m.group(1)), int(m.group(3)); e2 = m.group(4); e1 = m.group(2) or e2
    a, b = (-a if e1 == "BCE" else a), (-b if e2 == "BCE" else b)
    return int(min(a, b) - 100 <= y <= max(a, b) + 100)


K = tidy(P, 1); X = tidy(F, 0)
for D in (K, X):
    D["date_ok"] = [date_ok(s, y) for s, y in zip(D.datestr, D.year)]
chk["date_mismatch"] = int((K.date_ok == 0).sum())
chk["kept_no_coords"] = int(K.lat.isna().sum()); chk["failed_no_coords"] = int(X.lat.isna().sum())
chk["kept_archaic"] = int(K.archaic.sum()); chk["failed_archaic"] = int(X.archaic.sum())
chk["y_manual_used"] = int(K.y_manual.sum())
chk["culture_counts"] = K.culture.value_counts().to_dict()
chk["y_counts"] = K[K.sex == "M"].y_clade.replace("", "No call").value_counts().to_dict()
chk["mt_counts"] = K.mt_clade.replace("", "No call").value_counts().to_dict()
chk["other_y_examples"] = K[K.y_clade == "Other"].y_call.str[:3].value_counts().head(25).to_dict()
K.to_pickle(f"{WORK}/kept.pkl"); X.to_pickle(f"{WORK}/failed.pkl")
jsave(chk, f"{WORK}/checks.json", indent=1)
print({k: v for k, v in chk.items() if not isinstance(v, dict)})
print("culture", chk["culture_counts"]); print("y", chk["y_counts"]); print("mt", chk["mt_counts"]); print("other y", chk["other_y_examples"])
