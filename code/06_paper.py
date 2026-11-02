"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23872993 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Ancient_DNA_on_the_Map"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert all(R["steppe"][r]["pre3000_pct"] < 5 for r in ("Iberia", "Scandinavia", "Central Europe"))     # "from under 5%"
assert R["britain"]["pre_r1a"] == 0 and R["source"]["kept"] > 16000                                    # "more than sixteen thousand"
assert R["bias_period"][1]["name"] == "10,000 to 6000 BCE"
assert R["time"]["pct_after_3000bce"] > 50                                                              # "most of them from the last five thousand years"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return yr(v)
    return tex(str(v))


rows = "".join(f"{tex(c['country'])} & {c['n']:,} & {c['pct']:.1f}\\%\\\\\n" for c in R["countries"][:20])
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{The twenty present-day countries and territories with the most ancient individuals passing the quality assessment.}\\label{tab:countries}"
      "\\begin{tabular}{lrr}\\toprule Country or territory & Individuals & Share\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(b['cont'])} & {b['n']:,} & {b['pct']:.1f}\\% & {b['pop_pct']:.1f}\\% & {b['land_pct']:.1f}\\% & {b['per_10m_people']:.1f}\\\\\n" for b in R["bias_list"])
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{Located modern humans by continent, against present-day population and land.}\\label{tab:bias}"
      "\\begin{tabular}{lrrrrr}\\toprule Continent & Individuals & Share & Population & Land & Per 10 million people\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(c['country'])} & {c['n']} & {tex(c['yr'])} & {tex(c['group'])} & {c['km']:,}\\\\\n" for c in R["neolithic"]["countries"])
TN = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Earliest individual labelled Neolithic per country (countries with at least three), with distance of its site from Çatalhöyük.}\\label{tab:neo}"
      "\\begin{tabular}{lrrlr}\\toprule Country & Neolithic individuals & Earliest & Group & km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("COUNTRIES", TC), ("BIAS", TB), ("NEO", TN)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
for bad in ("DSIT", "DCMS"):
    assert bad not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
