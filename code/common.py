"""Shared paths, groupings and helpers for the ancient-dna project.

Raw inputs (read in place, never modified):
  raw/v66.p1_1240K.aadr.PUB.anno   Allen Ancient DNA Resource (AADR), version 66.p1, 1240K public annotation file:
                                    one row per published data representation of an individual (ancient or present-day),
                                    49 tab-separated columns with long descriptive headers.
      Mallick, S. et al. The Allen Ancient DNA Resource (AADR), Harvard Dataverse, doi:10.7910/DVN/FFIDCW. CC0 1.0.
      Paper: Mallick, S. et al. (2024) The Allen Ancient DNA Resource (AADR) a curated compendium of ancient human
      genomes. Scientific Data 11, 182. doi:10.1038/s41597-024-03031-7.
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_50m_land.geojson,
      ne_10m_populated_places_simple.geojson (Natural Earth, public domain)

Columns used (1-based, as in the AADR header): 3 Individual ID; 7 publication; 11 date mean in BP (years before 1950);
12 date standard deviation; 13 full date string; 15 Group ID; 16 locality; 17 political entity; 18 latitude;
19 longitude; 27 SNPs hit on the 1240k set; 31 molecular sex; 36 Y haplogroup (ISOGG); 37 Y haplogroup called by hand;
39 mtDNA haplogroup; 48 ASSESSMENT.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("AD_RAW", os.path.join(ROOT, "raw"))
ANNO = os.path.join(RAW, "v66.p1_1240K.aadr.PUB.anno")
GEO = os.environ.get("AD_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("AD_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("ADTMP", "/dev/shm/ancientdna"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "ancient-dna"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23872993"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/ancient-dna/"          # filled in by the publisher
AADR_VER = "v66.p1"
AADR_DOI = "10.7910/DVN/FFIDCW"
AADR_URL = "https://doi.org/10.7910/DVN/FFIDCW"
PAPER_DOI = "10.1038/s41597-024-03031-7"
AADR_CREDIT = "Allen Ancient DNA Resource (AADR) v66.p1, Mallick et al., Harvard Dataverse, doi:10.7910/DVN/FFIDCW (CC0 1.0)"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# ---------- quality ----------
PASS_PREFIX = ("Pass", "PROVISIONAL_PASS", "MERGE_PASS")   # AADR ASSESSMENT values kept

# ---------- archaic humans (flagged, kept apart from the modern human story) ----------
# Group ID naming Neanderthals or Denisova Cave, and dated before 40,000 BP: Denisova Cave also holds a modern human
# (DCP1, about 24,000 BP), which stays with the modern humans.
ARCHAIC_RE = re.compile(r"Neanderthal|Denisova", re.I)
ARCHAIC_MIN_BP = 40000

# ---------- Y chromosome: major clade from the ISOGG call ----------
# Order matters: the first prefix that matches wins. Calls above these levels (CT, F, K, P, R, R1...) cannot say whether
# a man carried R1a or R1b, so they are "too broad" and left out of every share.
Y_CLADES = [  # name, colour
    ("R1b", "#C8322B"), ("R1a", "#E8833A"), ("I1", "#2F5FA7"), ("I2", "#6C9BD2"), ("G2", "#2E9A8C"), ("J1", "#8C6BB1"),
    ("J2", "#B48FD8"), ("E1b", "#C9A227"), ("N", "#5B8C3A"), ("Q", "#D46A8C"), ("C", "#7A4E2D"), ("O", "#3B3B3B"),
    ("H", "#9DB84A"), ("T", "#E6B8A2"), ("L", "#8FB7B0"), ("D", "#A0522D"), ("Other", "#B9B2A6")]
Y_BROAD = re.compile(r"^(A0-T|A1b?|BT|CT|CF|DE|F\d?|GHIJK|HIJK|IJK|IJ|K.*|LT|NO.*|P\d?|R|R1|R1\?)$")
Y_RULES = [("R1b", "R1b"), ("R1a", "R1a"), ("I1", "I1"), ("I2", "I2"), ("G2", "G2"), ("J1", "J1"), ("J2", "J2"),
           ("E1b", "E1b"), ("N", "N"), ("Q", "Q"), ("C", "C"), ("O", "O"), ("H", "H"), ("T", "T"), ("L", "L"), ("D", "D")]
Y_OK = re.compile(r"^[A-T][A-Za-z0-9*]*$")


def yclean(s):
    """Tidy a Y call: drop '~', trailing '*', mutation suffixes ('I2a1a2-M423') and anything that is not a haplogroup."""
    s = (s or "").strip().replace("~", "").split()[0] if (s or "").strip() else ""
    s = re.sub(r"-[A-Z]+\d+.*$", "", s).rstrip("*?") if not s.startswith("A0-T") else s
    if s in ("", "..", "n/a", "NA") or s.startswith("n/a") or len(s) > 30:
        return ""
    return s if (Y_OK.match(s) or s == "A0-T") else ""


def yclade(s):
    """Major clade for colouring and shares: one of Y_CLADES names, 'Too broad', or '' (no call)."""
    s = yclean(s)
    if not s:
        return ""
    if Y_BROAD.match(s):
        return "Too broad"
    for pre, name in Y_RULES:
        if s.startswith(pre):
            return name
    return "Other"


# ---------- mtDNA: macro-haplogroup ----------
MT_CLADES = [
    ("H", "#C8322B"), ("HV and V", "#E8833A"), ("U", "#2F5FA7"), ("K", "#6C9BD2"), ("J", "#2E9A8C"), ("T", "#8FCFC0"),
    ("W, X, I and other N", "#8C6BB1"), ("A", "#C9A227"), ("B", "#D46A8C"), ("C", "#7A4E2D"), ("D", "#5B8C3A"),
    ("Other M", "#3B3B3B"), ("F and other R", "#B48FD8"), ("L (African)", "#A0522D")]


def mtclade(s):
    s = (s or "").strip()
    if not s or s.startswith("..") or s.lower().startswith("n/a") or s in ("NA", "na", "rCRS", "Neanderthal", "Hindet"):
        return ""
    m = re.match(r"^(L\d|HV|JT|[A-Z])", s)
    if not m:
        return ""
    k = m.group(1)
    if k.startswith("L"): return "L (African)"
    if k in ("HV", "V"): return "HV and V"
    if k in ("H", "U", "K", "J", "T", "A", "B", "C", "D"): return k
    if k in ("W", "X", "I", "N", "Y", "S", "O"): return "W, X, I and other N"
    if k in ("M", "G", "Z", "E", "Q"): return "Other M"
    if k in ("R", "F", "P", "JT"): return "F and other R"
    return ""


# ---------- broad period (calendar date of the date mean) ----------
# Years are CE; negative = BCE. date mean BP is years before 1950, so year = 1950 - BP.
PERIODS = [("Before 10,000 BCE", -1e9, -10000, "#3B2A1A"), ("10,000 to 6000 BCE", -10000, -6000, "#6E4A2E"),
           ("6000 to 4000 BCE", -6000, -4000, "#A2643A"), ("4000 to 2500 BCE", -4000, -2500, "#D08A3C"),
           ("2500 to 1000 BCE", -2500, -1000, "#E0B13E"), ("1000 BCE to 1 CE", -1000, 1, "#8DB06A"),
           ("1 to 1000 CE", 1, 1000, "#3F8F8A"), ("After 1000 CE", 1000, 1e9, "#2F5FA7")]


def period(year):
    for n, a, b, _ in PERIODS:
        if a <= year < b:
            return n
    return PERIODS[-1][0]


# ---------- culture tag from Group ID keywords ----------
# The Group ID is split on '_', '.', '-' and '+' into words; the first rule (top to bottom) with a matching word wins.
# A word matches a rule if it is one of the rule's exact words, or if it contains one of the rule's fragments (case
# sensitive) and is not listed for that fragment in CULTURE_NOT (words that contain it but mean something else, such as
# Eneolithic for Neolithic). Roman has no fragment at all, so that Romania stays out.
CULTURES = [  # name, colour, exact words, contains
    ("Archaic (Neanderthal, Denisovan)", "#111111", set(), ("Neanderthal", "Denisova")),
    ("Upper Palaeolithic", "#5A3A22", {"UP", "IUP", "EUP", "LUP", "Paleolithic", "Palaeolithic", "UpperPaleolithic", "Gravettian", "Aurignacian",
                                      "Magdalenian", "Epigravettian", "Solutrean", "Epipaleolithic", "Natufian", "Azilian", "Villabruna", "LGM", "Iberomaurusian", "EarlyUP"},
     ("Magdalenian", "Gravettian", "Aurignacian", "Federmesser", "Paleolithic")),
    ("Mesolithic and hunter-gatherers", "#8C6B3E", {"Mesolithic", "LateMesolithic", "EarlyMesolithic", "HG", "EHG", "WHG", "SHG", "CHG", "IronGates", "Meso", "Kongemose", "Ertebolle", "Maglemose"}, ("Mesolithic",)),
    ("Neolithic", "#5B8C3A", {"N", "EN", "MN", "LN", "EMN", "MLN", "PPN", "PPNA", "PPNB", "PPNC", "PN", "LBK", "Neolithic", "EarlyNeolithic", "MiddleNeolithic",
                              "LateNeolithic", "Megalithic", "PastoralN", "Cardial", "Impressa", "Starcevo", "Koros", "TRB", "FunnelBeaker", "GlobularAmphora", "Vinca",
                              "Lengyel", "Trypillia", "Cucuteni", "Wartberg", "Rossen", "PWC", "Pitted", "Michelsberg", "Baalberge", "Salzmunde", "PittedWare", "BKG", "Dawenkou", "Yangshao"}, ("Neolithic",)),
    ("Copper Age", "#A2643A", {"C", "EC", "LC", "LateC", "CA", "Eneolithic", "Chalcolithic", "Copper", "Bodrogkeresztur", "Tisza", "Gumelnita", "Lasinja",
                               "Varna", "Baden", "Maykop", "Botai", "Khvalynsk"}, ("Chalcolithic", "Eneolithic", "Maikop", "Tiszapolgar")),
    ("Yamnaya", "#C8322B", {"Yamnaya", "Yamna", "Afanasievo"}, ("Yamnaya",)),
    ("Corded Ware", "#E8833A", {"CordedWare", "Corded", "CWC", "CW", "Fatyanovo", "SingleGrave"}, ("CordedWare",)),
    ("Bell Beaker", "#E0B13E", {"BellBeaker", "Beaker", "BB"}, ("BellBeaker",)),
    ("Bronze Age", "#C9A227", {"BA", "EBA", "MBA", "LBA", "MLBA", "EMBA", "BA1", "BA2", "FBA", "BronzeAge", "Bronze", "Unetice", "Sintashta", "Andronovo",
                               "Srubnaya", "Catacomb", "Trzciniec", "Tumulus", "Urnfield", "Nuragic", "Minoan", "Mycenaean", "Argaric", "ElArgar",
                               "Hittite", "Fedorovo", "Alakul", "Okunevo", "Poltavka", "Potapovka", "Abashevo", "Wessex", "Petrovka", "Shang", "LShang"}, ("BronzeAge", "Hittite")),
    ("Iron Age", "#8C6BB1", {"IA", "EIA", "MIA", "LIA", "IA1", "IA2", "IronAge", "Iron", "LaTene", "Hallstatt", "Scythian", "Sarmatian", "Saka", "Etruscan",
                             "Punic", "Phoenician", "Hellenistic", "Classical", "Archaic", "Celtic", "Xiongnu", "XiongnuPeriod", "Urartian", "Piceni",
                             "Novilara", "Iberian", "Celtiberian", "PreRoman", "PreImperialRoman", "Republican", "Tasmola", "Pazyryk", "Tagar", "Levanluhta", "Parthian"},
     ("IronAge", "Punic", "Sarmatian", "Scythian")),
    ("Roman", "#B03A64", {"Roman", "ImperialRoman", "LateRoman", "EarlyRoman", "RomanBritain", "Romano", "RomanoBritish", "RomanPeriod", "Rome",
                         "EarlyRomanBogWar", "RomanRepublic", "GalloRoman"}, ()),
    ("Late Antiquity and Medieval", "#2F5FA7", {"Medieval", "EarlyMedieval", "HighMedieval", "LateMedieval", "EMA", "MA", "Med", "Medieval1", "LateAntiquity",
                                                "MigrationPeriod", "Avar", "EarlyAvar", "MiddleAvar", "LateAvar", "MiddleLateAvar", "Saxon", "AngloSaxon",
                                                "Lombards", "Langobard", "Longobard", "Merovingian", "Carolingian", "Byzantine", "Slav", "Slavic",
                                                "Conqueror", "Hunnic", "Hun", "Gepid", "Visigoth", "Ostrogoth", "Frankish", "Alamanni", "Bavarian",
                                                "Pictish", "Wielbark", "Chernyakhov", "Crusader", "Islamic", "Andalusi", "Golden", "GoldenHorde", "Mongol",
                                                "EarlySlav", "Gepids", "Alan", "Anglian", "EHun", "Reconquista", "NazariPeriod", "KingdomOfPortugal"}, ("Medieval", "Avar", "Arpadian", "Khazar")),
    ("Viking", "#1F2F4D", {"Viking", "EarlyViking", "LateViking", "VikingAge", "Norse"}, ("Viking",)),
    ("Early modern and historic", "#7A8A99", {"EarlyModern", "Modern", "Historic", "Historical", "PostMedieval", "Colonial", "PostColonial"}, ("EarlyModern", "Ottoman", "Napoleonic")),
]
CULTURE_OTHER = ("Other or regional label", "#C9C2B6")
# priority: specific named cultures beat broad periods (a Bell Beaker burial labelled EBA is Bell Beaker)
CULTURE_NOT = {"Viking": {"PreViking"}, "Medieval": {"PostMedieval"}, "Neolithic": {"Eneolithic", "EarlyEneolithic", "LateEneolithic"},
               "Scythian": {"Prescythian"}, "Yamnaya": {"oYamnaya"}}
CULTURE_ORDER = ["Archaic (Neanderthal, Denisovan)", "Yamnaya", "Corded Ware", "Bell Beaker", "Viking", "Roman", "Early modern and historic",
                 "Late Antiquity and Medieval", "Iron Age", "Bronze Age", "Copper Age", "Neolithic", "Mesolithic and hunter-gatherers", "Upper Palaeolithic"]
_CR = {c[0]: c for c in CULTURES}


def culture(group):
    words = [w for w in re.split(r"[_.\-+ ]", group or "") if w]
    for name in CULTURE_ORDER:
        _, _, exact, cont = _CR[name]
        if any(w in exact or any(c in w and w not in CULTURE_NOT.get(c, ()) for c in cont) for w in words):
            return name
    return CULTURE_OTHER[0]


# ---------- regions for the steppe story ----------
def region_of(entity, group, lat):
    first = (group or "").split("_")[0]
    if entity == "United Kingdom" and first in ("England", "Scotland", "Wales"):
        return "Britain"
    if entity in ("Spain", "Portugal", "Gibraltar"):
        return "Iberia"
    if entity in ("Denmark", "Sweden", "Norway"):
        return "Scandinavia"
    if entity in ("Germany", "Czechia", "Austria", "Switzerland", "Poland", "Slovakia"):
        return "Central Europe"
    return ""


REGIONS = [("Britain", "#C8322B", "England, Scotland and Wales"), ("Iberia", "#E0A11B", "Spain, Portugal and Gibraltar"),
           ("Scandinavia", "#2F5FA7", "Denmark, Sweden and Norway"),
           ("Central Europe", "#2E9A8C", "Germany, Czechia, Austria, Switzerland, Poland and Slovakia")]

# central Anatolia, for distances in the Neolithic spread (Çatalhöyük, 37.67 N 32.83 E)
ANATOLIA = (37.667, 32.828)


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    if f == "yr": return yr(v)
    raise ValueError(f)


def yr(y):
    """Calendar year as text: 2450 BCE, 43 CE."""
    y = int(round(float(y)))
    if y < 1:
        b = max(1, -y)
        return (f"{b:,}" if b >= 10000 else str(b)) + " BCE"
    return f"{y} CE"


def year_of(bp):
    return 1950 - bp
