# Anomaly flagging (TLE layer)

Unsupervised outlier flagging on LEO TLE-derived elements. This is not
maneuver detection and has no ground-truth labels.

## What changed vs. the original notebook script

- No Colab `uploaded` global.
- Mean motion is no longer a feature alongside altitude (they are the same Keplerian degree of freedom).
- IsolationForest `contamination=0.05` is recorded as an **input assumption**, not as a measured 5% anomaly rate.
- Candidates are written to `anomaly_candidates.csv` so later stages can consume them.

## Run

```bash
python experiments/anomaly-detection/run.py --catalog data/fixtures/demo_catalog.tle
```

A full Celestrak active catalog can be used the same way. The demo catalog is
only for reproducible tests, not for repeating the 13,893-object poster number.
