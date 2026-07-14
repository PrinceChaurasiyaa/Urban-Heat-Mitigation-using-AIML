"""M1: ERA5 atmospheric variables connector (FR-1.4)."""

import ee


def fetch_era5(cfg, aoi):
    src = cfg["data_sources"]["era5"]
    return (
        ee.ImageCollection(src["collection"])
        .filterBounds(aoi)
        .filterDate(cfg["time"]["start_date"], cfg["time"]["end_date"])
        .select(["temperature_2m", "dewpoint_temperature_2m", "u_component_of_wind_10m", "v_component_of_wind_10m"])
    )
