# UHIMP — Urban Heat Island Mitigation Platform

A geospatial, physics-informed AI/ML pipeline that identifies urban heat
hotspots, quantifies their drivers, and recommends optimized cooling
interventions with estimated temperature reduction (°C).

This repository implements the architecture described in the project SRS
(`docs/SRS.docx`): five layers — Data, Processing, Modeling, Simulation &
Optimization, and Presentation — broken into seven modules (M1–M7).

## Project layout

```
uhimp_project/
├── data/                       # All data, never committed raw (see .gitignore)
│   ├── raw/                    # Untouched pulls from each source
│   │   ├── landsat8/
│   │   ├── ecostress/
│   │   ├── sentinel2/
│   │   ├── era5/
│   │   ├── cpcb/
│   │   ├── osm/
│   │   └── ghsl/
│   ├── interim/                # Cloud-masked, reprojected, not yet feature-engineered
│   ├── processed/               # Final harmonized raster stack (Module 1 output)
│   └── training_tables/        # Sampled point tables for ML (LST, NDVI, NDBI, ...)
│
├── notebooks/                  # Exploratory analysis, one notebook per phase
│
├── src/                        # All pipeline code, mirrors SRS modules M1–M7
│   ├── data_acquisition/       # M1: GEE/USGS/Copernicus/CDS/OSM connectors
│   ├── preprocessing/          # M1: cloud masking, reprojection, index computation
│   ├── hotspot_mapping/        # M2: LST retrieval, classification, clustering
│   ├── driver_analysis/        # M3: SHAP, GWR, driver attribution maps
│   ├── modeling/
│   │   └── physics_informed/   # M4: baseline + physics-informed model, energy balance loss
│   ├── scenario_simulation/    # M5: layer perturbation engine, SOLWEIG/InVEST hooks
│   ├── optimization/           # M6: genetic algorithm / simulated annealing search
│   ├── visualization/          # M7: map tiles, chart generation, report builder
│   └── api/                    # REST API exposing pipeline outputs
│
├── configs/                    # YAML configs: AOI, date ranges, resolution, model params
├── models/                     # Trained model artifacts (versioned, gitignored by default)
│   ├── baseline/
│   ├── physics_informed/
│   └── artifacts/
│
├── outputs/                    # Generated deliverables
│   ├── heat_maps/
│   ├── driver_maps/
│   ├── scenario_results/
│   ├── reports/
│   └── figures/
│
├── dashboard/                  # M7: interactive front end + API backend
│   ├── frontend/
│   └── backend/
│
├── docs/                       # SRS, plain-English guide, architecture diagram
├── tests/                      # Unit + integration tests, mirrors src/ structure
└── scripts/                    # One-off / orchestration scripts (run_pipeline.sh etc.)
```

## Quick start

```bash
# 1. Create environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Authenticate Earth Engine (one-time)
earthengine authenticate

# 3. Configure your area of interest
cp configs/aoi.example.yaml configs/aoi.yaml
# edit configs/aoi.yaml with your city/ward bounds, date range, resolution

# 4. Run the pipeline phase by phase
python scripts/run_pipeline.py --phase data_acquisition
python scripts/run_pipeline.py --phase hotspot_mapping
python scripts/run_pipeline.py --phase driver_analysis
python scripts/run_pipeline.py --phase modeling
python scripts/run_pipeline.py --phase scenario_simulation
python scripts/run_pipeline.py --phase optimization

# 5. Launch the dashboard
cd dashboard/backend && uvicorn main:app --reload
```

## Module → SRS requirement mapping

| Directory | SRS Module | Key Requirements |
|---|---|---|
| `src/data_acquisition/`, `src/preprocessing/` | M1 | FR-1.1 – FR-1.9 |
| `src/hotspot_mapping/` | M2 | FR-2.1 – FR-2.5 |
| `src/driver_analysis/` | M3 | FR-3.1 – FR-3.6 |
| `src/modeling/physics_informed/` | M4 | FR-4.1 – FR-4.6 |
| `src/scenario_simulation/` | M5 | FR-5.1 – FR-5.5 |
| `src/optimization/` | M6 | FR-5.6 – FR-5.8 |
| `src/visualization/`, `dashboard/` | M7 | FR-6.1 – FR-6.5 |

See `docs/SRS.docx` for the full specification and `docs/execution_roadmap.md`
for the phase-by-phase build plan.
