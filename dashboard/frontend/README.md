# UHIMP Dashboard Frontend

Placeholder for the interactive map + driver-attribution + scenario
comparison dashboard (SRS FR-6.1 – FR-6.3).

Suggested stack: React + Leaflet/Mapbox GL for maps, Plotly/D3 for charts.

## Getting started (once scaffolded)
```bash
npm install
npm run dev
```

Connects to the backend API at `dashboard/backend/main.py`
(endpoints: `/hotspots`, `/drivers/{cell_id}`, `/scenarios`, `/intervention-plan`).
