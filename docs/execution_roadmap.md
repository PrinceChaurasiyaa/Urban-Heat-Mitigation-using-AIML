# UHIMP Execution Roadmap

Condensed from SRS Section 9. Use this as the working checklist.

| Phase | Focus | Primary Code Location | Output |
|---|---|---|---|
| 0 | AOI Selection & Setup | `configs/aoi.yaml` | Defined AOI, repo scaffolded |
| 1 | Data Acquisition & Preprocessing | `src/data_acquisition/`, `src/preprocessing/` | Harmonized raster stack in `data/processed/` |
| 2 | Heat Hotspot Mapping | `src/hotspot_mapping/` | Classified heat map + hotspot polygons in `outputs/heat_maps/` |
| 3 | Feature Engineering & Driver Analysis | `src/driver_analysis/` | Driver ranking + attribution maps in `outputs/driver_maps/` |
| 4 | Physics-Informed Model Development | `src/modeling/` | Trained model in `models/physics_informed/` |
| 5 | Scenario Simulation | `src/scenario_simulation/` | Pre/post LST comparisons in `outputs/scenario_results/` |
| 6 | Optimization | `src/optimization/` | Ranked intervention plan (GeoJSON) |
| 7 | Visualization, Reporting & Validation | `src/visualization/`, `dashboard/` | Dashboard + `outputs/reports/` |

## Checklist per phase

- [ ] **Phase 0**: `cp configs/aoi.example.yaml configs/aoi.yaml`, fill in GEE project ID and AOI bounds
- [ ] **Phase 1**: run `python scripts/run_pipeline.py --phase data_acquisition`; verify scene count > 0
- [ ] **Phase 2**: implement `classify_heat_stress` calibration for your AOI's LST distribution
- [ ] **Phase 3**: train baseline model, run SHAP, cross-check with GWR
- [ ] **Phase 4**: implement energy-balance loss term, train physics-informed model, compare vs. baseline
- [ ] **Phase 5**: define intervention parameters in `perturbation.py`, run scenarios
- [ ] **Phase 6**: define budget/feasibility constraints, run GA/SA optimizer
- [ ] **Phase 7**: build dashboard views, generate final report, package for submission/handoff

See `docs/SRS.docx` for full requirement definitions (FR-1.x through FR-6.x)
and `docs/plain_english_guide.md` for a non-technical walkthrough of the same
pipeline.
