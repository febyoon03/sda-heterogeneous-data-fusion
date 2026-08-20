# YAOGAN-9 ground track

Supporting figure. Sampling starts at the TLE epoch, not at an arbitrary
midnight. The Korea box reports both sample counts and distinct passes.

```bash
python experiments/yaogan9-ground-track/run.py
```

Eccentricity 0.053 is the published Yaogan-9 design (perigee ~700 km, apogee
~1490 km, i=63.4°). It is unusual in a LEO catalog, which is why a density
model flags it; it is not by itself evidence of a maneuver.
