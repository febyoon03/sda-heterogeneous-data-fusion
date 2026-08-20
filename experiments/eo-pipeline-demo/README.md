# EO pipeline demonstration

Not TLE cross-validation. NDVI has no physical mechanism that would confirm
or deny an orbital anomaly.

The original Landsat Collection 2 path called `normalizedDifference` on raw
SR integers (scale 0.0000275, offset −0.2). The live path now scales first
and applies a QA_PIXEL cloud/shadow mask.

Default run is offline so the repo is executable without a GEE project:

```bash
python experiments/eo-pipeline-demo/run.py
python experiments/eo-pipeline-demo/run.py --live --project YOUR_PROJECT
```
