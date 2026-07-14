"""M1: Sentinel-2 connector for LULC classification and spectral indices (FR-1.3)."""

import ee


def fetch_sentinel2_sr(cfg, aoi):
    src = cfg["data_sources"]["sentinel2"]
    return (
        ee.ImageCollection(src["collection"])
        .filterBounds(aoi)
        .filterDate(cfg["time"]["start_date"], cfg["time"]["end_date"])
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", src["max_cloud_cover_pct"]))
    )
