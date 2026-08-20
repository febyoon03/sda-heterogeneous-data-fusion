# SGP4 comparison and OWL-Net visibility

## Experiment A

Propagate the case-study t0 TLE and compare it to a second TLE at t0+24h.

The original script treated "whatever Celestrak returns today" as t24. That is
only valid if the downloaded TLE epoch is near the evaluation time. This rewrite
refuses to call the comparison a maneuver test when the epoch window fails.

The bundled reference TLE is from 2026-03-09, about a week before t0. The
pipeline will therefore report `comparable=false` unless you supply a true
near-t24 TLE.

## Experiment B

Optical visibility windows for real OWL-Net sites. Mt. Lemmon is in Arizona,
not near Busan. Sobaeksan is not an OWL-Net station.

Numbers are **observable-time ratios**, not detection probabilities. There is
no RF layer in this repository.

```bash
python experiments/sgp4-and-owlnet-visibility/run.py --stations korea
python experiments/sgp4-and-owlnet-visibility/run.py --stations all
```

Skyfield will download `de421.bsp` on the first visibility run.
