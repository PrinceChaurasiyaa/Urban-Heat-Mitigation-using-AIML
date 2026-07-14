"""
M7: REST API exposing pipeline outputs (hotspot maps, driver rankings,
scenario results) for the dashboard front end and external GIS integration.
Implements the API interface described in SRS Section 7.3.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="UHIMP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/hotspots")
def get_hotspots():
    """TODO: return hotspot polygons (GeoJSON) from outputs/heat_maps/."""
    raise NotImplementedError


@app.get("/drivers/{cell_id}")
def get_drivers(cell_id: str):
    """TODO: return SHAP-based driver ranking for a given grid cell."""
    raise NotImplementedError


@app.get("/scenarios")
def list_scenarios():
    """TODO: return available scenario results from outputs/scenario_results/."""
    raise NotImplementedError


@app.get("/intervention-plan")
def get_intervention_plan():
    """TODO: return the optimized intervention plan (GeoJSON + metadata)."""
    raise NotImplementedError
