# Validation review: original scripts vs. rewritten toolkit

This review looked at the four standalone scripts in `sda-heterogeneous-data-fusion.zip` (anomaly detection, SGP4/OWL‑Net, ground track, Landsat NDVI) and their READMEs.

This is not a web app, so it has no user accounts, billing, or marketing campaigns. The usual review questions are simply asked about the real parts of this project instead: how data is accessed, how each experiment runs, and how a candidate object's state is tracked.

---

## 1. One‑line summary

These are four Colab‑style notebooks. In writing, they describe a 3‑layer SDA fusion pipeline. In practice, they run as four disconnected scripts with hardcoded satellite data, a live Celestrak download used as if it were a fixed 24‑hour‑later snapshot, wrong OWL‑Net station locations, an anomaly model that is forced to always flag exactly 5% of the data, and an NDVI chart whose title still claims something the project had already withdrawn.

---

## 2. What each file was supposed to do

| Script | What it claimed to do | What it actually did |
|---|---|---|
| `isolation_forest_detection.py` | Flag unusual LEO orbits and produce the candidate list the rest of the pipeline uses | Reads a file uploaded through Colab, prints some counts, saves one image. Never writes out a candidate list. |
| `sgp4_owlnet_validation.py` | Physically check one flagged object; measure whether OWL‑Net can actually see it | Hardcodes one satellite's starting orbit; downloads whatever the *current* TLE happens to be; mixes real geometry with invented RF multipliers. |
| `ground_track.py` | Show why this satellite and Korea matter | Keeps its own separate copy of the same TLE; counts data samples, not actual passes. |
| `ndvi_landsat_pipeline.py` | Demonstrate a third, independent data source after the validation claim had already been withdrawn | Chart is still titled "Cross‑validation of TLE Anomaly Detection." |

After the rewrite, each part has one clear job:

- `sda_fusion.tle` parses and checks TLE text.
- `sda_fusion.orbit` turns a TLE into orbital elements.
- `sda_fusion.anomaly` decides which objects to flag.
- `sda_fusion.sgp4_validate` compares positions only when the time gap is valid.
- `sda_fusion.visibility` handles the geometry of what can be seen and when.
- `sda_fusion.ground_track` counts real passes.
- `sda_fusion.eo` runs the NDVI demo.
- `sda_fusion.providers.celestrak` / `earthengine` handle all outside data access, and can be removed or swapped without touching the science code.

These boundaries matter for a simple reason: TLE checksums have nothing to do with IsolationForest, station coordinates have nothing to do with SGP4 error numbers, and Earth Engine's data types should never leak into orbit math.

In the original code, changing one satellite's TLE meant editing two files by hand. Changing the OWL‑Net station list meant editing the SGP4 script directly. And changing how anomalies were defined had no effect on the case study at all, because the case study never actually used the anomaly output.

---

## 3. How the code actually ran

### The original scripts, step by step

**Anomaly script.** There was no real input step: it simply assumed a Colab variable called `uploaded` already existed. Each TLE line was only checked with `if t1.startswith('1') and t2.startswith('2')`, and any error was silently ignored with a bare `except: continue`. Values were read directly from fixed character positions in each line. The script fit an IsolationForest model, saved one chart, and printed some tables. All of this lived only in memory. Nothing was saved as a candidate list that another script could use.

**SGP4 / OWL‑Net script.** It started from one hardcoded satellite's TLE, loaded it into Skyfield, and set that as time t0. It then downloaded a satellite record from Celestrak for the same object. If that download failed to parse, the "t24" TLE was simply left empty. When a TLE was returned, the script compared position at t0 versus at t24 and reported the distance between them using a fixed 5 km threshold. It also loaded a planetary ephemeris file, ran 4,320 one‑minute time steps across three ground stations, and checked whether the satellite was sunlit, above 10° elevation, and the sky was dark enough. Finally, it multiplied the resulting visibility number by 2.0 and 2.8 to produce "RF" and "fusion" numbers, capped at 88% and 95%, and saved two images to whatever folder the script happened to be run from.

When something went wrong, the behavior was inconsistent. A network error was printed, and only the first experiment was skipped, while the second one kept running on outdated data. A malformed Celestrak response was also just printed and skipped, with no real error handling. There was no checksum check, so a corrupted line of text could silently be read as a different satellite entirely. If the ephemeris file failed to download, the whole program crashed partway through. And the only real safety check in the whole script was whether a TLE object existed at all, not whether it was actually valid.

**Rewritten version.** A catalog is loaded, either from a real source or from a bundled sample file, and every TLE is checksum‑validated before use. Anomaly flagging is optional, and when it runs, it writes out both a CSV of candidates and a JSON summary. The case study always starts from the same bundled, known‑good TLE. When comparing two time points, the code checks not just the distance between them, but also the actual time gap. If that gap is more than 12 hours, the comparison is explicitly marked as invalid, even if the resulting number happens to look small and convincing. Visibility calculations either use a real, verified station table or are skipped entirely, with no invented RF multiplier anywhere. The NDVI step defaults to a clearly offline mode, with any live Earth Engine access isolated in its own separate module.

---

## 4. Access, state, and how the pieces talk to each other

**Access.** There are no user accounts in this project, so the closest thing to an authentication problem is how the code trusts outside data sources. Celestrak needs no login at all, yet the original script still faked a browser identity string out of habit; the rewrite instead sends an honest, clearly labeled research identifier. A specific Earth Engine project ID was hardcoded directly inside the NDVI math itself, mixing an access detail into the science code; the rewrite moves that into its own separate access module. The anomaly script also could not run outside of Google Colab, since it depended on a Colab‑only variable to get its input file. With these problems fixed, all of the core calculations (anomaly scoring, SGP4 comparison, visibility geometry) can now be tested completely on their own, with no outside service needed.

**State.** There was no lasting memory of anything between runs. The only thing genuinely worth remembering, "this satellite was flagged, and here is its starting TLE," was never actually saved anywhere. The specific satellite used in the case study (YAOGAN‑9) was simply assumed to be a good example from the start; the anomaly script never actually selected it. If a future anomaly run didn't flag that satellite at all, the case‑study scripts would still go ahead and analyze it anyway.

**Communication.** The original scripts had no real way of sharing information with each other; everything that connected them was just a comment or a copy‑pasted TLE string. The rewrite fixes this with structured data passed between steps, saved to disk as JSON or CSV files, and one shared command‑line interface tying all the experiments together.

---

## 5. Where the original code was too tightly tangled together

The same satellite TLE was copy‑pasted into both the SGP4 script and the ground‑track script, so changing one without the other would make the resulting charts disagree with each other. Both altitude and mean motion were fed into the anomaly model even though they measure closely related things, so removing either one would silently change every score, and there was no way to do that without also editing chart labels by hand. The "695 candidates (5.0%)" headline number was directly tied to one hardcoded setting in the anomaly model, so changing that one number would have silently changed the published result. The fake RF multipliers of 2.0 and 2.8 lived inside the same function that calculated real visibility geometry, so adding an actual RF sensor later would have just meant multiplying by yet another made‑up number instead of building a real module. And the chart titles themselves made specific claims ("Multi‑Source Fusion," "Cross‑validation") that were no longer true by the time anyone read them.

If Celestrak had gone offline entirely, the original SGP4 experiment would have had no way to run at all. The rewritten version can still run its case study on bundled sample data, and correctly refuses to interpret two mismatched time points as a real maneuver.

---

## 6. Why this design, and what it gives up

The original design was essentially "one script per chart." Cheap to put together for a presentation, expensive to change later, and effectively impossible to test.

The rewrite instead uses a small, shared code library with thin wrapper scripts around it for each experiment. What was given up is the convenience of a single file you can paste directly into Colab. What was gained is checksum testing, corrected station data, a real time‑gap safety check, and the ability to remove Earth Engine entirely without breaking anything else.

A few heavier alternatives were considered and deliberately not used: a full database with a task queue was not worth building for just four experiments; a full event‑driven system connecting the anomaly detector to the SGP4 script wasn't necessary either, since a CSV file does the same job; and keeping the fake RF bars purely "because they looked good on the poster" was rejected outright, since they were never real measurements to begin with.

---

## 7. Where the explanation and the actual numbers didn't match

| Claim | What actually happened |
|---|---|
| Fusion flags 695 candidates (5.0%) | `IsolationForest(contamination=0.05)` **sets** that fraction in advance. It was never really discovered. |
| The fusion list is what SGP4 uses | SGP4 hardcodes one satellite (NORAD ID 36413), regardless of what the anomaly detector found. |
| "t24" TLE came from Celestrak, 24 hours later | It was just whatever the latest catalog entry happened to be, at any epoch. The README even warns re‑runs change the number, but still calls it "t24." |
| 0.20 km result | Measured once, in March 2026. Can't be reliably reproduced from the script since the catalog keeps moving. |
| Optical detection probability 4.1% | (sunlit ∩ night ∩ elevation) ÷ (elevation), then × an arbitrary 0.5 weather discount. |
| +RF 8.1%, fusion 11.4% | Just `optical average × 2.0` and `× 2.8`, capped at 88% / 95%. No real RF data. |
| "Mt. Lemmon" station is in Korea at 35.30°N, 129.10°E | Mt. Lemmon is actually in Arizona, at about 32.44°N, 110.79°W. A second listed station, Sobaeksan, is not an OWL‑Net site at all. |
| Astronomical night | Used sun altitude below −10°, when the correct threshold is below −18°. |
| Number of passes over Korea | Actually a count of 5‑minute samples inside a map box, not real passes. |
| Ground‑track date 2026‑03‑16 00:00 | The TLE's real epoch is 2026‑03‑15 17:11 UTC. |
| NDVI is a simple pipeline demo | Chart title still reads "Cross‑validation of TLE Anomaly Detection." |
| Landsat Collection‑2 NDVI, correctly calculated | `normalizedDifference` was applied to unscaled raw integers, without the required −0.2 offset. |
| YAOGAN‑9's 0.053 eccentricity is "anomalous" | It reflects the known, deliberate design of the 2010‑009 ELINT satellite trio (~700 × 1490 km, 63.4° inclination). Unusual next to a sun‑synchronous catalog, not evidence of a maneuver. |
| 3‑layer, 3‑source fusion | Really one real measured layer (TLE), one offline demo layer (EO), and one entirely invented projection (RF). The README already admits it's closer to "1.5 sources." |

In short, "Experiment A" was meant to compare a satellite's position at t0 against roughly t0 + 24 hours. Any real run after March 2026 actually compared a live, current‑day TLE against a satellite state months away from that TLE's real epoch, something SGP4 isn't designed to handle accurately. Any small number that came out of that comparison later would have been pure coincidence.

---

## 8. What the original code didn't account for

**Edge cases.** No real handling for an empty catalog, an all‑geostationary catalog, duplicate names, or missing name lines mixing 2‑line and 3‑line TLE formats (a single missing line would desync the whole reading loop). A column of data that never changes would cause a divide‑by‑zero in the z‑score step. A garbled mean‑motion value could produce a negative altitude, with only a broad 200–2000 km range checked afterward. A "no data found" response from Celestrak was treated as if it were just an unusually short, valid TLE. An empty Earth Engine result could silently produce `None`, which would later crash the script. And the Jinju NDVI example area includes ocean, pulling the average down with no land‑only filter.

**Timing.** Downloading "t24" live meant every run was racing against whatever Celestrak's catalog looked like at that exact moment, so two runs a day apart were really two different experiments sharing the same name. There was also no protection against overwriting results: re‑running just overwrote the same image files in the current folder instead of a dated output folder.

**Resources.** The actual computational load (about 4,320 time steps across three stations) is small and not a real concern. The one practical issue is `plt.show()` called right after `savefig()`, which hangs indefinitely when run without a display, like on a server.

**Leftover or unnecessary logic.** The invented RF bars and their percentage caps. A hardcoded `normal_max = 5.0` presented as if it were a physical law, when it's really just a policy choice. Feeding both altitude and mean motion into the same anomaly model when they measure closely related things. A leftover Colab‑only `uploaded` reference sitting in a README that otherwise says to just run `python script.py`. And an NDVI description that says "winter to spring vegetation decrease" for a comparison that was actually August to March (late summer to late winter): the point about seasonal confounding is fair, but the season names are wrong.

**Domain understanding.** YAOGAN‑9 (36413) is a known, deliberately eccentric satellite from a 63.4°‑inclination trio. It's reasonable for an anomaly detector to flag it as unusual against a mostly sun‑synchronous catalog. But treating a small 0.20 km SGP4 residual as evidence the flag "might be a false positive" mixes up two different meanings of anomaly: unusual orbital elements versus an actual maneuver. A satellite can have genuinely unusual elements and still fly a stable orbit for sixteen years.

---

## 9. Must fix now / can defer

### Fixed in this rewrite

- Shared TLE parsing and checksum validation.
- Removed the Colab‑only `uploaded` dependency entirely.
- No longer treats the latest available TLE as a valid "24 hours later" snapshot without checking the time gap.
- Corrected OWL‑Net station coordinates; dropped the non‑OWL‑Net "Sobaeksan" site.
- Removed the invented RF and fusion percentages completely.
- Ground‑track passes are now counted as actual passes, sampled from each satellite's real epoch.
- The live Landsat path now applies the correct scale, offset, and quality mask.
- Chart titles now match what the chart actually shows.
- `contamination` is now explicitly labeled as an assumption, not a measured value.
- Dropped the redundant, closely correlated mean‑motion feature from the anomaly model.
- Earth Engine access now sits behind its own adapter, with offline as the default.
- Flagged candidates are now saved and handed off as CSV/JSON.
- Added real tests for checksum validation, altitude, the epoch time‑gap check, pass counting, and station data.

### Deferred, and when it becomes dangerous

| Item | Why it can wait | When it becomes dangerous |
|---|---|---|
| Real historical TLE archive for a true t24 | No public archive is bundled; the guard already refuses a fake t24 | Publishing a new specific "0.xx km" validation number |
| Pixel‑level land mask / seasonal NDVI model | EO isn't currently used as evidence | Anyone cites a specific ΔNDVI next to the TLE flag as if they're connected |
| Real weather model instead of the 0.5 discount | Geometry is already cleanly separated from it | Citing the weather‑adjusted ratio as an actual detection rate |
| SatSim / light curves / passive RF | Stated as future work; still no code | Slide language that implies they already exist |
| `contamination` sensitivity sweep | Demo catalog is too small to matter | Treating 5% as a real, measured LEO anomaly rate |
| Full 13,893‑object reproduction | Needs a properly dated Celestrak snapshot | Comparing new counts directly to the old poster table |

---

## 10. Could you explain this to another engineer in five minutes?

With the original code, you couldn't explain the pipeline in five minutes without a long list of caveats: ignore the RF bars, ignore the chart title, remember that "t24" isn't really t24, and remember that the anomaly script doesn't actually feed into anything else.

With the rewrite, the whole pipeline fits in one sentence: TLE data comes in, optional anomaly flags come out, one case‑study object gets a closer look, SGP4 only runs when the time gap is valid, optical visibility is checked at real station locations, and NDVI is available as an optional demo. That sentence *is* the architecture.

Quick answers for the original code: could each module's job be described in one sentence? Only after digging through README footnotes. Did access concerns leak into the science code? Yes, through Earth Engine and the Colab upload. Was it too tightly coupled? The duplicated TLE, yes, but coupled together as an actual working pipeline? No, and that was the bigger problem. Could someone follow it quickly? The honesty in the READMEs helps, but the code was still quietly performing claims already withdrawn in writing. Could a dependency be removed tomorrow? Not Celestrak, not Earth Engine, not the Colab upload. Smart explanation, strange runtime? Yes, and that mismatch was the main finding.

---

## Verifying the rewrite

The tests in `tests/` confirm: YAOGAN‑9's checksum and epoch (2026‑03‑15 17:11 UTC) are correct. Mean altitude comes out to about 1,095.3 km, correctly split into perigee/apogee from its 0.053 eccentricity. The anomaly model's features exclude mean motion. The SGP4 time‑gap check correctly rejects the bundled week‑old reference TLE. Comparing a TLE against itself at zero time difference gives an error of about zero. The Korea station list contains only Bohyun and Daedeok, and Mt. Lemmon is correctly recognized as a western longitude. The pass counter counts actual passes, not raw samples. And the offline NDVI demo is always labeled synthetic and seasonal, never as a real measurement.

What these tests do **not** do is reproduce the original 695 / 0.20 km / 4.1% figures. Those numbers came from one specific catalog snapshot and one incorrect station table, and were never meant to be reproducible as originally presented.
