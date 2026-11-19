# ITA0312 Mobile Computing – Assignment 5 (CO5)

**Student:** N. Arun Kumar  
**Register No.:** 192424184

This folder contains the executable simulation code and generated evidence for Part B. These are model-based simulations, not measurements from a physical Android phone.

## Files

- `bgsim.py` – B1/B2 background scheduler and adversarial workloads
- `feedsim.py` – B3 exact vs adaptive feed renderer search
- `videosim.py` – B4 video encode/upload strategy
- `run_all.py` – runs all three programs
- `make_figures.py` – creates report-ready charts under `figure/` (requires Matplotlib)
- `requirements.txt` – standard-library-only simulation dependencies
- `*_results.json` – generated numerical results

## Run

```bash
python run_all.py
```

Run one task individually using `python bgsim.py`, `python feedsim.py`, or `python videosim.py`.

To regenerate charts, install Matplotlib (`pip install matplotlib`) and run `python make_figures.py`.

The default B3 scaling run covers up to 400 feed items; 800/1,500 item exhaustive searches are computationally expensive and can be added to the `scale` list in `feedsim.py` for an extended run.

All battery, radio, CPU, frame-time and energy values are assumptions in the simulation model. They demonstrate relative algorithm behaviour, not real-device benchmarks. Validate production decisions with Android Studio Profiler, Perfetto and Battery Historian on representative devices.
