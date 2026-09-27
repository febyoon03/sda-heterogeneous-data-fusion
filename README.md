# SDA Heterogeneous Data Fusion Toolkit

*Presented at Yonsei Aerospace Week 2026 (May 2026), Excellence Award. Rewritten and checked again in August 2026 before publishing to GitHub. Please read this whole README before quoting any number from this project.*

This is a data fusion toolkit for Space Domain Awareness (SDA). It combines three types of data (TLE, EO, RF) to find unusual satellite orbits, take a closer look at one flagged case, check whether it can be seen with a telescope, and show how a third, independent data source (EO) can be added on top.

## Please read this first: the numbers shown at the symposium are not verified

The numbers shown at the symposium (**695 candidates (5.0%), 0.20 km SGP4 deviation, 4.1% / 8.1% / 11.4% OWL‑Net visibility**) came from an earlier version of this code. That version was checked carefully after the symposium. The full write‑up is here: [`VALIDATION_REVIEW.md`](VALIDATION_REVIEW.md).

The check found several real problems:

**Wrong station locations.** One of three stations labeled "OWL‑Net Korea" was actually **Mt. Lemmon, Arizona, USA**, but it was plotted with made‑up coordinates near Busan. A second station used ("Sobaeksan") is not an OWL‑Net site at all. The real OWL‑Net network in Korea only has two sites (Bohyun and Daedeok).

**Wrong definition of night.** "Astronomical night" was defined as sun altitude below −10°, when the correct value is below −18°.

**No real time gap.** The "t24" TLE was simply whatever Celestrak's current catalog happened to return when the script ran. It was never checked to actually be 24 hours after t0. Running the same script today could compare t0 to a TLE from days or weeks later and still call it a "24‑hour" comparison.

**Made‑up visibility numbers.** The "+RF" and "Multi‑Source Fusion" visibility numbers were just the optical number multiplied by 2.0 and 2.8. These multipliers were invented, not measured. This problem was already known from an earlier version of this project. What changed here is that the fake multipliers are now removed completely, not just labeled as fake.

**Wrong satellite image data.** The Landsat NDVI value was calculated using raw Collection‑2 numbers, without applying the scale (0.0000275) and offset (−0.2) that the formula needs to work correctly.

**A number that can't really surprise anyone.** `IsolationForest(contamination=0.05)` is told in advance to flag exactly 5% of the data. So "695 candidates (5.0%)" is mostly just the model doing what it was told, not really a discovery.

**Counting samples instead of real passes.** The number of "passes over Korea" was actually a count of 5‑minute snapshots that happened to fall inside a map box. One real 15‑minute pass could get counted as three.

**Leftover label.** A chart about NDVI still had the old title "Cross‑validation of TLE Anomaly Detection," even though that framing had already been dropped everywhere else.

None of this means the core idea is wrong. Flagging outliers from TLE data, comparing them with SGP4, and checking optical visibility are all valid methods. The problem is that **the specific numbers above came from one bad station list and one uncontrolled catalog pull, so they can't be reproduced or trusted as they were presented.** The fix here was not to patch the old numbers. It was to rebuild the toolkit so these mistakes can't happen again, and to add tests that check for exactly that.

## What is in this repo now

**`sda_fusion/`** — a proper, tested Python package (not loose scripts). It includes TLE parsing with checksum validation, orbital element calculations, anomaly flagging, a time‑gap check for SGP4 comparisons, real OWL‑Net station data, correct pass counting, and an EO/NDVI module with the right Landsat scaling.

**`experiments/`** — simple one‑command scripts, one for each figure from the original project.

**`tests/`** — 15 tests that all pass. They check exactly the things that went wrong before: TLE checksums, a known satellite's real epoch and altitude, that the anomaly model doesn't use a redundant column, that a week‑old reference TLE is correctly rejected, that Korea's station list doesn't include Arizona, that passes (not samples) are counted, and that offline NDVI is always labeled as fake data.

**`data/fixtures/`** — sample TLE data (including a real satellite's actual starting orbit) so the toolkit can run without any internet connection.

**`outputs/`** — a real, saved run of the full pipeline on a small 58‑object sample catalog (not the original 13,893‑object Celestrak data, see below). This is kept as proof that the pipeline runs correctly from start to finish, not as a replacement for the old symposium numbers.

## What the sample run in `outputs/` actually shows

This run used `data/fixtures/demo_catalog.tle`, a small, made‑up sample catalog of 58 objects used for testing (not the real 13,893‑satellite Celestrak data).

**Anomaly flagging:** 3 of the 58 objects were flagged by the combined model, and 2 of 58 by a simpler method. One real satellite (YAOGAN‑9 01A) was flagged, along with two test objects that were deliberately made to look unusual.

**SGP4 case study:** the sample reference TLE is actually about 174 hours (7.2 days) after t0, not 24 hours. The pipeline correctly detects this and reports `comparable: false`, instead of wrongly treating the resulting 0.65 km difference as a sign of a maneuver. This shows the fix working as intended, not a new finding.

**Ground track:** 4 snapshots landed inside the Korea map box, and the pipeline correctly counts this as **1** real pass (before, this difference was not tracked).

**EO demo:** the offline version uses a fixed, made‑up placeholder value (NDVI 0.42 → 0.18, a change of −0.24) so the repo can run without a live Earth Engine connection. **This is not a real measurement from Jinju.** A real, corrected NDVI run needs `--live --project YOUR_PROJECT` with Earth Engine credentials, which has not been done yet with the corrected scale and offset.

The figures for all of this are saved in `outputs/` and shown below.

![Anomaly flagging, demo catalog](outputs/anomaly_detection_fusion.png)
![SGP4 comparison, correctly flagged as not comparable](outputs/fig3_experiment_A_sgp4.png)
![Ground track with correct pass counting](outputs/yaogan9_ground_track.png)

## Tech stack

Python, Skyfield, scikit‑learn, pandas, NumPy, Matplotlib, Google Earth Engine (only needed for the live/optional path), pytest.

## How to run it

```bash
pip install -r requirements.txt
python -m pytest tests -q
python -m sda_fusion.cli pipeline --catalog data/fixtures/demo_catalog.tle --out outputs --skip-visibility
```

The visibility step (OWL‑Net viewing windows) needs Skyfield's DE421 ephemeris file, which downloads automatically the first time you run it. Leave out `--skip-visibility` to include this step. To check for anomalies using a real, current Celestrak catalog instead of the sample one, run: `python -m sda_fusion.cli anomaly --catalog <path-to-downloaded-catalog>`.

## What is not in this repo

**A verified reproduction of the symposium numbers** (13,893 objects, 695 candidates, 0.20 km, 4.1–11.4%). As explained above, these numbers are not currently defensible, and this rewrite does not try to create new versions of them.

**The SQLite storage pipeline and a direct NASA EarthData download attempt.** These were exploratory pieces from the original project that were never part of the actual presented method, so they are not included here either.

**SatSim synthetic imagery with light‑curve photometry, and SDR‑based passive RF integration.** These were only planned as future work in the original research plan. No code exists for either one.

## Limitations and what's next

A full‑scale validation run has not been done yet: this means running on the real ~13,893‑object Celestrak catalog, using a genuinely 24‑hour‑apart TLE pair, and doing a live Earth Engine NDVI run with the corrected scale and offset. That is the real next step before this project can publish new headline numbers.

The `contamination=0.05` setting is still just an assumption, not something fitted or tested against real labeled data. The rewrite is honest about this in every output, rather than trying to fix it artificially, since fixing it properly would require labeled anomaly data that doesn't currently exist.

See section 9 of [`VALIDATION_REVIEW.md`](VALIDATION_REVIEW.md), "Deferred, and when it becomes dangerous," for the full list of what has intentionally not been fixed yet, and why.

## Credits

Built independently. Presented at the 2026 Yonsei Aerospace Week Symposium and received an Excellence Award. The August 2026 audit and rewrite ([`VALIDATION_REVIEW.md`](VALIDATION_REVIEW.md), `sda_fusion/`, `tests/`) were done in collaboration with Claude (Anthropic). The audit process is as much a part of this portfolio piece as the code itself.
