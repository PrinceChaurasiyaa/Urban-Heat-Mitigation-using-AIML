"""
UHIMP - Module 1: Data Acquisition & Preprocessing
Pull, cloud-mask, and export Landsat 8 Collection 2 Level-2 Land Surface
Temperature (LST) for a Delhi AOI using the Google Earth Engine Python API.

Prereqs:
    pip install earthengine-api geemap
    earthengine authenticate      # one-time browser login
    # or: ee.Authenticate() the first time you run this script

Docs referenced:
    QA_PIXEL bit layout & ST/SR scale factors:
    https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands
    LANDSAT/LC08/C02/T1_L2 dataset:
    https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2
"""

import ee

# ---------------------------------------------------------------------------
# 1. Initialize
# ---------------------------------------------------------------------------
# Replace with your own GEE-registered Cloud project.
PROJECT_ID = "uhmaiml"

try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# ---------------------------------------------------------------------------
# 2. Define AOI (Delhi) and date range
# ---------------------------------------------------------------------------
# Option A: simple bounding box around Delhi NCR (quick start)
delhi_aoi = ee.Geometry.Rectangle([76.84, 28.40, 77.35, 28.88])

# Option B (preferred for real work): use an admin boundary instead of a box
# delhi_aoi = (
#     ee.FeatureCollection("FAO/GAUL/2015/level2")
#     .filter(ee.Filter.eq("ADM2_NAME", "Delhi"))
#     .geometry()
# )

START_DATE = "2024-05-01"   # peak pre-monsoon heat season is ideal for UHI work
END_DATE = "2024-06-15"
CLOUD_COVER_MAX = 30        # % scene-level cloud cover filter, tune as needed

# ---------------------------------------------------------------------------
# 3. Cloud / shadow / saturation mask + scale factors
# ---------------------------------------------------------------------------
def mask_and_scale_l8(image):
    """
    Applies the QA_PIXEL cloud/shadow/cirrus/dilated-cloud mask, the
    QA_RADSAT saturation mask, and the official USGS scale/offset factors
    for both optical (SR) and thermal (ST) bands.

    QA_PIXEL bits used (Collection 2, Landsat 8/9):
        Bit 1 - Dilated Cloud
        Bit 2 - Cirrus
        Bit 3 - Cloud
        Bit 4 - Cloud Shadow
    """
    qa = image.select("QA_PIXEL")

    dilated_cloud = 1 << 1
    cirrus = 1 << 2
    cloud = 1 << 3
    cloud_shadow = 1 << 4

    mask_bits = dilated_cloud | cirrus | cloud | cloud_shadow
    qa_mask = qa.bitwiseAnd(mask_bits).eq(0)

    sat_mask = image.select("QA_RADSAT").eq(0)

    # Official Collection 2 Level-2 scale/offset (USGS product guide)
    optical_bands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
    thermal_band = image.select("ST_B10").multiply(0.00341802).add(149.0)

    return (
        image.addBands(optical_bands, overwrite=True)
        .addBands(thermal_band, overwrite=True)
        .updateMask(qa_mask)
        .updateMask(sat_mask)
        .copyProperties(image, ["system:time_start", "system:index"])
    )


def kelvin_to_celsius(image):
    """Adds an LST_C band (Celsius) alongside the scaled ST_B10 (Kelvin)."""
    lst_c = image.select("ST_B10").subtract(273.15).rename("LST_C")
    return image.addBands(lst_c)


# ---------------------------------------------------------------------------
# 4. Build the filtered, masked collection
# ---------------------------------------------------------------------------
collection = (
    ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .filterBounds(delhi_aoi)
    .filterDate(START_DATE, END_DATE)
    .filter(ee.Filter.lt("CLOUD_COVER", CLOUD_COVER_MAX))
    .map(mask_and_scale_l8)
    .map(kelvin_to_celsius)
)

print("Scenes matching filter:", collection.size().getInfo())

# ---------------------------------------------------------------------------
# 5. Composite (median) LST over the date range and clip to AOI
# ---------------------------------------------------------------------------
lst_composite = collection.select("LST_C").median().clip(delhi_aoi)

# Optional: also keep the surface reflectance bands for NDVI/NDBI/NDWI
sr_composite = (
    collection.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"])
    .median()
    .clip(delhi_aoi)
)

# ---------------------------------------------------------------------------
# 6. Derived spectral indices (feeds Module 3: Driver Analysis)
# ---------------------------------------------------------------------------
ndvi = sr_composite.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
ndbi = sr_composite.normalizedDifference(["SR_B6", "SR_B5"]).rename("NDBI")
ndwi = sr_composite.normalizedDifference(["SR_B3", "SR_B5"]).rename("NDWI")

feature_stack = lst_composite.addBands([ndvi, ndbi, ndwi])

# ---------------------------------------------------------------------------
# 7. Export
# ---------------------------------------------------------------------------
# 7a. Export the full raster stack to Google Drive as a GeoTIFF
export_task = ee.batch.Export.image.toDrive(
    image=feature_stack,
    description="UHIMP_Delhi_LST_NDVI_NDBI_NDWI",
    folder="UHIMP_exports",
    fileNamePrefix="delhi_lst_stack_2024",
    region=delhi_aoi,
    scale=30,
    crs="EPSG:4326",
    maxPixels=1e13,
)
export_task.start()
print("Started export task:", export_task.id)

# 7b. Optional: sample the stack at random points to build a tabular
#     training set (same format as the LST/LULC/NDBI/NDVI/NDWI CSV you
#     already pulled from GEE)
sample_points = feature_stack.sample(
    region=delhi_aoi,
    scale=30,
    numPixels=2000,
    seed=42,
    geometries=True,
)

table_export_task = ee.batch.Export.table.toDrive(
    collection=sample_points,
    description="UHIMP_Delhi_training_points",
    folder="UHIMP_exports",
    fileNamePrefix="delhi_lst_training_points_2024",
    fileFormat="CSV",
)
table_export_task.start()
print("Started table export task:", table_export_task.id)

# ---------------------------------------------------------------------------
# 8. (Optional) Quick local preview with geemap, if running in a notebook
# ---------------------------------------------------------------------------
# import geemap
# m = geemap.Map(center=[28.6, 77.2], zoom=10)
# m.addLayer(
#     lst_composite,
#     {"min": 25, "max": 48, "palette": ["blue", "yellow", "red"]},
#     "Delhi LST (Celsius)",
# )
# m.addLayer(delhi_aoi, {}, "AOI", False)
# m
