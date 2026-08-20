# Validation review — original scripts vs. rewritten toolkit

Reviewed artifacts: the four standalone scripts in
`sda-heterogeneous-data-fusion.zip` (anomaly detection, SGP4/OWL-Net,
ground track, Landsat NDVI) plus their READMEs.

This is not a web app. There is no user auth, billing, or campaign module.
Those review questions are mapped onto the actual systems: data access,
experiment stages, and candidate state.

---

## 1. One-line summary

Four Colab-style notebooks that *narrate* a 3-layer SDA fusion pipeline
but *run* as disconnected scripts with hardcoded TLEs, a live Celestrak
pull used as if it were t24, incorrect OWL-Net geography, a guaranteed
5% IsolationForest rate, and an NDVI experiment whose figure title still
claims cross-validation.

---

## 2. Responsibility boundaries

### What each original file claimed to own

| Script | Claimed responsibility | Actual responsibility at runtime |
|---|---|---|
| `isolation_forest_detection.py` | Flag LEO TLE outliers; produce the candidate list the rest of the pipeline uses | Parse a Colab upload, print counts, save one PNG. Writes no candidate list. |
| `sgp4_owlnet_validation.py` | Physically check one flagged object; measure OWL-Net observability | Hardcodes YAOGAN-9 t0; fetches *current* TLE; mixes measured geometry with invented RF multipliers. |
| `ground_track.py` | Show why this satellite and Korea matter | Independent copy of the same TLE; counts samples, not passes. |
| `ndvi_landsat_pipeline.py` | Demonstrate a third modality after withdrawing the validation claim | Still titles the figure “Cross-validation of TLE Anomaly Detection”. |

One-sentence ownership after the rewrite:

- `sda_fusion.tle` — parse and checksum TLE text.
- `sda_fusion.orbit` — Keplerian elements from a TLE.
- `sda_fusion.anomaly` — unsupervised flagging policy.
- `sda_fusion.sgp4_validate` — epoch-gated position comparison.
- `sda_fusion.visibility` — optical window geometry.
- `sda_fusion.ground_track` — sub-satellite sampling and pass counting.
- `sda_fusion.eo` — NDVI demo orchestration.
- `sda_fusion.providers.celestrak` / `earthengine` — removable I/O.

Why those cuts: TLE checksum does not belong next to IsolationForest;
station coordinates do not belong next to SGP4 error bars; GEE types must
not leak into orbit math.

Blast radius in the original: changing the YAOGAN-9 TLE required editing
two files by hand. Changing OWL-Net sites required editing the SGP4
script. Changing the anomaly definition had no effect on the case study
because nothing consumed the anomaly output.

---

## 3. Actual execution flow

### Original success path (as written)

**Anomaly script**

1. Request: there is no request. A Colab global `uploaded` is assumed.
2. Validation: `if t1.startswith('1') and t2.startswith('2')`. Bare `except: continue`.
3. State read: every 3-line group; inclination `[8:16]`, ecc `'0.'+[26:33]`, mean motion `[52:63]`.
4. Side effects: IsolationForest fit; `plt.savefig('anomaly_detection_fusion.png')`; stdout tables.
5. Success residue: a DataFrame in memory and a PNG. No CSV, no NORAD list, no handoff.

**SGP4 / OWL-Net script**

1. Hardcoded t0 TLE → Skyfield `EarthSatellite` → epoch `t0`.
2. HTTP GET `gp.php?CATNR=36413`. On any parse failure, `tle1_t24` stays `None`.
3. If a TLE came back: `sat_t0.at(t24)` vs `sat_t24.at(t24)`, Euclidean error, 5 km policy.
4. Load DE421; 4320 one-minute samples; three stations; sunlit ∩ elev>10° ∩ sun<-10°.
5. Multiply station-average “probability” by 2.0 and 2.8, cap at 88% / 95%.
6. Save two PNGs in the current working directory.

**Failure path, original SGP4**

- Network exception: printed, Experiment A skipped, Experiment B still runs on t0.
- Short Celestrak body: printed “형식이 다릅니다”, Experiment A skipped.
- No checksum check, so a truncated line can become a wrong satellite.
- DE421 download failure: uncaught, process dies after A.
- `if tle1_t24:` is the only gate; `tle2_t24` is trusted implicitly.

### Rewritten success / failure path

1. `load_catalog` or bundled fixture → checksummed `TwoLineElement`s.
2. Optional `flag_anomalies` → `anomaly_candidates.csv` + summary JSON.
3. Case study always starts from the bundled t0 TLE (the presentation object).
4. `compare_propagation(t0, t_ref)` computes the error **and** the epoch gap.
   If the gap > 12 h, `comparable=False` and `within_normal=False` even if
   the number is small.
5. Visibility is skipped or run with a real station table. No RF multiplier.
6. EO default is offline; live GEE is behind `providers.earthengine`.

---

## 4. Auth / state / communication

### Auth

There are no users. The auth-shaped problems are credentials and trust of
external catalogs.

- Celestrak is unauthenticated. The original script spoofed
  `User-Agent: Mozilla/5.0`. That is not a reason Skyfield or Celestrak
  need a browser UA; it is a habit. The rewrite sends an explicit research UA.
- Earth Engine project `sda-tle-analysis` is hardcoded next to NDVI math.
  Auth is smeared into the science script. The rewrite isolates
  `ee.Initialize` in `providers.earthengine`.
- The anomaly script cannot run outside Colab (`filename = list(uploaded.keys())[0]`).
  That is session state used as a public interface.

Business logic (z-score, SGP4 difference, altaz) can now be tested without
Celestrak or GEE.

### State

There is no persistent campaign state. The only state that should have
existed is “this NORAD id was flagged, here is its t0 TLE.” It never
existed on disk.

YAOGAN-9 is *asserted* to be a fusion candidate. The anomaly script never
selects it. If a future catalog run does not flag 36413, the case-study
scripts still analyze it.

### Communication

Original: none. Shared knowledge is comments and duplicated TLE strings.

Rewrite: dataclasses in memory, JSON/CSV on disk, CLI as the only
cross-experiment surface. No circular imports. Removing Celestrak or GEE
is `providers/*` plus a fixture fallback.

---

## 5. Tight coupling and break points

- TLE string duplicated in SGP4 and ground-track scripts. Change one, the
  figures disagree.
- Altitude and mean motion both fed to IsolationForest. Dropping either
  changes scores; the original could not drop one without editing the
  plot labels by hand.
- `contamination=0.05` is bound to the headline “695 (5.0%)”. Changing
  the parameter silently changes the published rate.
- RF multipliers 2.0 / 2.8 live in the visibility function. Adding a real
  RF source would have been another `* factor` instead of a new module.
- Figure titles encode claims (“Multi-Source Fusion”, “Cross-validation”).

If Celestrak disappeared tomorrow, the original SGP4 experiment had no
fixture path. The rewrite runs Experiment A on bundled TLEs and refuses
the maneuver interpretation when epochs do not match.

---

## 6. Why this abstraction (and what was given up)

Original abstraction: “one script per figure.” Cheap to present, expensive
to change, impossible to test.

Rewrite: a small library + thin experiment wrappers.

Given up: single-file Colab paste. Gained: checksum tests, station
corrections, epoch guard, removable GEE.

Alternatives not taken:

- Full database + queue. Not earned by four experiments.
- Event bus between anomaly and SGP4. A CSV is enough.
- Keeping RF bars “for the poster look.” They are not measurements.

---

## 7. Explanation vs. runtime mismatches

| Claim | Runtime |
|---|---|
| Fusion flags 695 (5.0%) | `IsolationForest(contamination=0.05)` *sets* that fraction. |
| Fusion list is what SGP4 uses | SGP4 hardcodes 36413. |
| t24 TLE from Celestrak | Latest catalog TLE, any epoch. README even warns re-runs change the number, then still calls it t24. |
| 0.20 km result | Measured once in March 2026. Not recoverable from the script as written after the catalog moves. |
| Optical detection probability 4.1% | (sunlit ∩ night ∩ elev) / (elev) × 0.5. A weather-discounted visibility ratio. |
| +RF 8.1%, fusion 11.4% | `avg * 2.0`, `avg * 2.8`, caps 88/95. No RF data. |
| OWL-Net 레몬산 at 35.30°N, 129.10°E | Mt. Lemmon is ~32.44°N, 110.79°W. 소백산 is not an OWL-Net site. |
| Astronomical night | Sun < −10°, not −18°. |
| 한반도 통과 횟수 | Number of 5-minute samples in a box, not passes. |
| Ground-track date 2026-03-16 00:00 | TLE epoch is 2026-03-15 17:11 UTC. |
| NDVI “pipeline demo” | Figure title: “Cross-validation of TLE Anomaly Detection”. |
| Landsat C2 NDVI | `normalizedDifference` on unscaled SR integers (offset −0.2). |
| YAOGAN-9 ecc 0.053 is “ANOMALOUS” | Design of the 2010-009 ELINT trio (~700 × 1490 km, 63.4°). Unusual in a LEO cloud, not a surprise maneuver. |
| 3-layer fusion | TLE measured + EO demo + RF projection. README already admits “1.5-source.” The scripts still print 3-source percentages. |

Intended Experiment A: compare a TLE at t0 with a TLE whose epoch is ~t0+24h.

Actual Experiment A after March 2026: evaluate a current TLE at a date
months from its epoch. SGP4 is not valid there. A small number, if it
ever appeared later, would be an accident.

---

## 8. Blind spots

### Edge cases

- Empty catalog, all-GEO catalog, duplicate names, missing name lines
  (2LE vs 3LE). Original 3-step walk desynchronizes on a missing name.
- Zero / constant feature column: z-score divides by `std` with no guard.
- Negative altitude if mean motion is garbage; only a 200–2000 km gate
  after the fact.
- Celestrak “No GP data found” HTML/text: treated as a short TLE.
- GEE empty collection: `median()` then `reduceRegion` can yield `None`,
  then `stats['NDVI']` crashes.
- Permission-like: Jinju AOI includes ocean; mean NDVI is pulled down
  without a land mask.

### Race / time

- Live t24 pull is a time-of-run race against the catalog. Two runs a day
  apart are different experiments with the same name.
- No idempotency: re-running overwrites PNGs in cwd, not a dated output dir.

### Resources

- 4320-element Python datetime list × 3 stations × sun + sat. Fine at
  this size; no file/session leak except GEE client state.
- `plt.show()` in scripts that also `savefig` — hangs headless runs.

### Dead / unnecessary logic

- RF bars and caps.
- `normal_max = 5.0` presented as a physical LEO law. It is a policy.
- Altitude **and** mean motion as IF features.
- Colab `uploaded` left in a repo README that says `python script.py`.
- NDVI change-direction string “겨울→봄 식생 감소” for August→March
  (late summer → late winter). The season comment is right about the
  confound and wrong about the month names.

### Domain

YAOGAN-9 / 36413 is a known eccentric 63.4° triplet. IsolationForest
should flag it relative to SSO-dominated catalogs. Calling that a
candidate is fair; treating SGP4 residual 0.20 km as “the flag may be a
false positive” mixes two definitions of anomaly (unusual elements vs.
maneuver). Unusual elements can be stable for 16 years.

---

## 9. Must fix now / can defer

### Fixed in this rewrite

- Shared TLE parse + checksum.
- Remove Colab `uploaded`.
- Do not use latest TLE as t24 without an epoch window.
- Correct OWL-Net coordinates; drop Sobaeksan-as-OWL-Net.
- Stop emitting RF/fusion percentages.
- Count passes as runs, sample from the TLE epoch.
- Landsat C2 scale/offset + QA mask on the live path.
- Figure titles match the claim.
- contamination labeled as an assumption.
- Drop collinear mean-motion feature.
- GEE behind an adapter; offline EO path.
- Candidate CSV / JSON handoff.
- Tests for checksum, altitude, epoch window, pass counting, stations.

### Deferred, and when it becomes dangerous

| Item | Why it can wait | When it becomes dangerous |
|---|---|---|
| Real historical TLE archive for a true t24 | No public archive is bundled; the guard already refuses a fake t24 | Publishing a new 0.xx km “validation” number |
| Pixel-level land mask / seasonal NDVI model | EO is not used as evidence | Anyone cites ΔNDVI next to the TLE flag |
| Real weather model instead of 0.5 | Geometry is already separated | Citing weather-adjusted ratios as detections |
| SatSim / light curves / SDR | Stated future work; still no code | Slide language that implies they exist |
| contamination sensitivity sweep | Demo catalog is tiny | Treating 5% as a measured LEO-anomaly rate |
| Full 13,893-object reproduce | Needs a dated Celestrak snapshot | Comparing new counts to the poster table |

---

## 10. Explainability test

Original: you cannot explain the pipeline to another engineer in five
minutes without saying “ignore the RF bars, ignore the figure title,
ignore that t24 is not t24, and the anomaly script does not actually
feed the next script.”

Rewrite: TLE in → optional flags out → one case-study object → SGP4
only if epochs match → optical windows at real sites → optional NDVI
demo. That sentence is the architecture.

Fast-judgment answers for the original modules:

1. One-sentence responsibility? Only after reading the README footnotes.
2. Did “auth” seep in? GEE and Colab upload, yes.
3. Tightly coupled? Duplicated TLE, yes. Coupled as a pipeline? No —
   which is worse.
4. Can someone else follow it quickly? The honesty in the READMEs is
   good; the code still performs the withdrawn claims.
5. Remove a dependency tomorrow? Not Celestrak, not GEE, not `uploaded`.
6. Smart explanation, strange runtime? Yes. That was the main finding.

---

## Verification of the rewrite

See `tests/`. They check:

- YAOGAN-9 checksum and epoch (2026-03-15 17:11 UTC).
- Mean altitude ≈ 1095.3 km, perigee/apogee split from e=0.053.
- IsolationForest features exclude mean motion.
- SGP4 window rejects the week-old bundled reference.
- Same-TLE zero-horizon error is ~0.
- Korea stations are Bohyun + Daedeok; Lemmon is west longitude.
- Pass counter counts runs.
- Offline NDVI stays labeled synthetic and seasonal.

What the tests do not claim: reproduction of 695 / 0.20 km / 4.1%.
Those numbers belonged to a specific catalog pull and a specific
incorrect station table.
