"""
Module 1: Data Acquisition & Preprocessing — Landsat 8 connector.
Implements SRS requirements FR-1.1, FR-1.7, FR-1.8, FR-1.9.

This is the productionized version of the standalone script
`gee_landsat8_lst_delhi.py` — wrapped as an importable function that reads
its parameters from configs/aoi.yaml instead of hardcoded constants.
"""

import ee
import yaml


def load_config(path="configs/aoi.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def get_aoi_geometry(cfg):
    aoi_cfg = cfg["aoi"]
    if aoi_cfg.get("bbox"):
        return ee.Geometry.Rectangle(aoi_cfg["bbox"])
    admin = aoi_cfg["admin_boundary"]
    return (
        ee.FeatureCollection(admin["source"])
        .filter(ee.Filter.eq(admin["field"], admin["value"]))
        .geometry()
    )


def mask_and_scale_l8(image):
    """QA_PIXEL cloud/shadow mask + QA_RADSAT saturation mask + USGS scale factors."""
    qa = image.select("QA_PIXEL")
    mask_bits = (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4)  # dilated cloud, cirrus, cloud, shadow
    qa_mask = qa.bitwiseAnd(mask_bits).eq(0)
    sat_mask = image.select("QA_RADSAT").eq(0)

    optical = image.select("SR_B.").multiply(0.0000275).add(-0.2)
    thermal = image.select("ST_B10").multiply(0.00341802).add(149.0)

    return (
        image.addBands(optical, overwrite=True)
        .addBands(thermal, overwrite=True)
        .updateMask(qa_mask)
        .updateMask(sat_mask)
        .copyProperties(image, ["system:time_start", "system:index"])
    )


def add_lst_celsius(image):
    return image.addBands(image.select("ST_B10").subtract(273.15).rename("LST_C"))


def fetch_landsat8_lst(cfg):
    """Returns a cloud-masked, scaled ee.ImageCollection for the configured AOI/date range."""
    aoi = get_aoi_geometry(cfg)
    src = cfg["data_sources"]["landsat8"]

    collection = (
        ee.ImageCollection(src["collection"])
        .filterBounds(aoi)
        .filterDate(cfg["time"]["start_date"], cfg["time"]["end_date"])
        .filter(ee.Filter.lt("CLOUD_COVER", src["max_cloud_cover_pct"]))
        .map(mask_and_scale_l8)
        .map(add_lst_celsius)
    )
    return collection, aoi


if __name__ == "__main__":
    cfg = load_config()
    ee.Initialize(project=cfg["project"]["gee_project_id"])
    coll, aoi = fetch_landsat8_lst(cfg)
    print("Scenes matched:", coll.size().getInfo())
