// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8871; set PORT to change).
const { chromium } = require("playwright");
// MapLibre from a local npm copy (the CDN is not reachable from the build container); tiles, labels and fonts are blocked here.
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
(async () => {
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic|openfreemap/, r => r.abort());
    await p.route(/maplibre-gl\.js$/, r => r.fulfill({ path: ML + "/maplibre-gl.js" }));
    await p.route(/maplibre-gl\.css$/, r => r.fulfill({ path: ML + "/maplibre-gl.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to fetch|AJAXError/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8871) + "/index.html", { waitUntil: "load" });
    for (let k = 0; k < 60 && !(await p.evaluate(() => !!window.map && document.getElementById("loading") === null)); k++) await p.waitForTimeout(500);
    console.log(nm, "map ready:", await p.evaluate(() => !!window.map && document.getElementById("loading") === null));
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    const drawn = async () => p.evaluate(() => map.queryRenderedFeatures({ layers: ["dots"] }).length);
    await shot("#atlas", "map");
    console.log(nm, "dots drawn (all):", await drawn());
    // a time window: 2400 BCE, Y lines, Europe
    await p.click('#colRow [data-c="yc"]');
    await p.evaluate(() => setTimeBP(4350, 2));
    await p.click('#focusRow .btn:nth-child(3)'); await p.waitForTimeout(1500);
    console.log(nm, "dots drawn (c. 2400 BCE, Europe):", await drawn(), "label:", await p.textContent("#yv"));
    await shot("#atlas", "map_2400bce_y");
    // slider drag and play
    await p.evaluate(() => { const r = document.getElementById("tt"); r.value = 500; r.dispatchEvent(new Event("input")); }); await p.waitForTimeout(500);
    console.log(nm, "slider 500 label:", await p.textContent("#yv"));
    await p.click("#play"); await p.waitForTimeout(2500); await p.click("#play");
    console.log(nm, "after play label:", await p.textContent("#yv"), "v=", await p.evaluate(() => S.v.toFixed(1)));
    // Britain before and after
    await p.click('#focusRow .btn:nth-child(4)'); await p.evaluate(() => setTimeBP(5200, 3)); await p.waitForTimeout(1200); await shot("#atlas", "britain_3250bce");
    await p.evaluate(() => setTimeBP(3900, 3)); await p.waitForTimeout(1200); await shot("#atlas", "britain_1950bce");
    // colour modes
    await p.click('#colRow [data-c="cu"]'); await p.click('#focusRow .btn:nth-child(3)'); await p.evaluate(() => setTimeBP(0, 0)); await p.waitForTimeout(1500); await shot("#atlas", "culture_all");
    await p.click('#colRow [data-c="mc"]'); await p.waitForTimeout(800); await shot("#atlas", "mt_all");
    // search and popup
    await p.fill("#q", "Iceman"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_iceman");
    console.log(nm, "popup:", (await p.textContent(".maplibregl-popup-content").catch(() => "none")).slice(0, 120));
    // layers panel
    await p.click(".lyrBtn"); await p.waitForTimeout(300);
    await p.evaluate(() => { const c = document.querySelector('.lyrPanel [data-k="failed"]'); c.checked = true; c.dispatchEvent(new Event("change")); });
    await p.evaluate(() => { const c = document.querySelector('.lyrPanel [data-k="base"]'); c.value = "relief"; c.dispatchEvent(new Event("change")); });
    await p.waitForTimeout(800); await shot("#map", "layers_panel");
    console.log(nm, "layers state:", await p.evaluate(() => JSON.stringify({ base: LY.base, failed: LY.failed, relief: map.getLayoutProperty("relief", "visibility"), land: map.getLayoutProperty("land", "visibility") })));
    await p.click(".lyrPanel .reset"); await p.click(".lyrBtn");
    await p.click('#focusRow .btn:nth-child(2)'); await p.waitForTimeout(800);
    for (const c of ["pubChart", "timeChart", "biasChart", "countryTable", "neoChart", "steppeChart", "steppeLines", "famousTable", "siteTable"]) await shot("#" + c, c);
    await p.click("#regRow .btn:nth-child(3)"); await p.waitForTimeout(400); await shot("#steppeChart", "steppeChart_iberia");
    await p.click("#regRow .btn:nth-child(4)"); await p.waitForTimeout(400); await shot("#steppeChart", "steppeChart_scand");
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#steppeChart", "dark_steppe");
    }
    await p.locator("#mapbox").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500);
    console.log(nm, "fullscreen:", await p.evaluate(() => !!(document.fullscreenElement || document.querySelector(".mfs-fake"))), "map h:", await p.evaluate(() => document.getElementById("map").clientHeight));
    await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    await p.click(".mfs-btn"); await p.waitForTimeout(500);
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
