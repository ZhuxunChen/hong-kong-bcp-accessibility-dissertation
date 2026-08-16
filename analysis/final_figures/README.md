# Final explanatory figures

This package reproduces the six explanatory figures added to the final dissertation:

- Figure 4.1: analytical workflow;
- Figure 4.2: stable-routing sample retention;
- Figure 5.3: cumulative access;
- Figure 5.4: BCP accessibility profile;
- Figure 5.6: global Moran scatterplots; and
- Figure 5.8: model transition and residual spatial dependence.

The generator reads only the frozen Stage 9A inputs and results. It writes new
exports to `analysis/final_figures/results/` and does not overwrite the frozen
copies in `reference_outputs/final_figures/`.

From the repository root, after installing the locked Python environment, run:

```bash
.venv/bin/python analysis/final_figures/generate_final_figures.py
.venv/bin/python analysis/final_figures/verify_final_figures.py
```

Verify the frozen dissertation exports directly with:

```bash
.venv/bin/python analysis/final_figures/verify_final_figures.py \
  --directory reference_outputs/final_figures
```

The generator also emits a study-area candidate used during figure development.
The final Figure 3.1 is reproduced separately by
`analysis/meeting3_checks/scripts/05_enhance_study_area_map.R`.
