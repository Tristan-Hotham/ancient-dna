"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; results and the palettes (site.json) are embedded; data/individuals.json and data/world.json are
loaded by the page. Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html)
is pasted before </body>. 10.5281/zenodo.23872993 and https://blog.tristanhotham.com/2026/10/31/ancient-dna/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
BR, ST, NL, FM = R["britain"], R["steppe"], R["neolithic"], {f["id"]: f for f in R["famous"]}

# facts stated in words (page, blog, paper, collage)
assert R["famous"][13]["id"] == "Inuk" and R["famous"][13]["pub_year"] == 2010 and R["pubs"]["first_year"] == 2010   # "In 2010 ... the first genome"
assert R["famous"][1]["id"] == "Ust_Ishim" and R["famous"][1]["ok"] == 1
assert R["time"]["oldest_k"] == 45000 and R["time"]["oldest_bp"] < 46000
assert [o["group"].split("_")[1] for o in R["oldest"][:10]].count("Ranis") >= 8 and any(o["id"] == "ZKU002" for o in R["oldest"][:10])   # Ranis and Zlatý kůň
assert R["oldest"][0]["bp"] == FM["ZKU002"]["bp"]                                                                                    # "given the same broad date"
assert R["archaic"][0]["id"] == "Denisova25"
assert {a["site"].split(" ")[0].split("-")[0] for a in R["archaic"]} == {"Denisova", "Chagyrskaya", "Mezmaiskaya", "Vindija", "Grotte"}, {a["site"] for a in R["archaic"]}
assert R["sex"]["M"] > R["sex"]["F"]
assert [c["country"] for c in R["top_countries"][:3]] == ["Russia", "Hungary", "United Kingdom"]
assert sum(p["eu_pct"] > 50 for p in R["bias_period"]) == 7 and R["bias_period"][1]["eu_pct"] < 50                                 # "almost every period"
assert R["bias_sum"]["eu_pct"] > 60 and R["bias_sum"]["eu_pop_pct"] < 10 and R["bias_sum"]["eu_land_pct"] < 10
assert R["bias"]["Africa"]["pct"] < 2 < R["bias"]["Africa"]["pop_pct"] / 5
# farmers
assert NL["first"]["country"] == "Turkey" and NL["by_country"]["Turkey"]["year"] == NL["first"]["year"]
order = [NL["by_country"][c]["year"] for c in ("Greece", "Hungary", "France", "Portugal", "United Kingdom", "Ireland")]
assert order == sorted(order), order                                                                                                # "get later, country by country"
assert [b["lat0"] for b in NL["lat_bands"][2:5]] == [45, 50, 55] and NL["lat_bands"][2]["year"] < NL["lat_bands"][3]["year"] < NL["lat_bands"][4]["year"]
assert 0.9 < NL["km_per_year"] < 1.3 and NL["r"] > .7                                                                                # "about a kilometre a year"
# steppe
assert BR["pre_r1b"] == 0 and BR["pre_r1a"] == 0 and BR["post_r1b_pct"] > 85 and BR["first_r1b_group"].startswith("England_BellBeaker")
assert BR["first_r1b_site"].startswith("Canada Farm (England, Dorset") and BR["first_r1b_year"] > -2500
assert BR["ia_r1b_pct"] > 85 and BR["em_i1_pct"] > 20
assert all(ST[r]["pre3000_pct"] < 10 and ST[r]["ba_pct"] >= 50 and ST[r]["first50"] == -2500 for r in ST)                           # "small minority ... at least half"
sc = {b["a"]: b for b in ST["Scandinavia"]["bins"]}
assert sum(sc[a]["clades"]["I1"] for a in range(-7000, -3000, 500)) == 0 and sc[-2500]["clades"]["I1"] + sc[-2000]["clades"]["I1"] > 10   # "where I1 also rises"
bb = {b["a"]: b for b in ST["Britain"]["bins"]}
assert sum(bb[a]["clades"]["I1"] for a in range(-7000, 400, 500) if a in bb) <= 2                                                   # I1 "almost absent from earlier Britain"
assert R["yamnaya"]["r1b_pct"] > 70 and R["corded"]["r1a_pct"] > R["corded"]["r1b_pct"] and R["beaker"]["r1b_pct"] > 90
assert R["neo_y"]["r_pct"] < 10 and R["anatolia_y"]["top"] == "G2" and R["iceman"]["y_clade"] == "G2"
assert ST["Central Europe"]["pre3000_r"] > 0
# faces
assert FM["kennewick"]["assessment"].startswith("Questionable") and FM["Anzick"]["assessment"].startswith("Questionable")
assert "Avar" in R["sites"][0]["group"] and "Avar" in R["sites"][1]["group"] and R["sites"][0]["country"] == "Austria" and R["sites"][1]["country"] == "Hungary"
assert R["sites"][5]["site"].startswith("Çatalhöyük")
assert any(s["site"].startswith("Cambridgeshire (England)") for s in R["sites"])                                                     # county-level "sites"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23872993", "https://blog.tristanhotham.com/2026/10/31/ancient-dna/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    Rp = {k: v for k, v in R.items() if k not in ("source",)}
    Rp["source"] = {k: v for k, v in R["source"].items() if k != "checks"}
    html = html.replace("/*RESULTS*/", J(Rp)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
