"""M1: Urban morphology feature extraction (building density, SVF proxy, canopy).
Implements FR-3.2.
"""


def compute_building_density(osm_buildings, aoi, grid_resolution_m):
    """TODO: rasterize OSM building footprints and compute per-cell density."""
    raise NotImplementedError


def compute_sky_view_factor_proxy(ghsl_height_raster):
    """
    TODO: compute an SVF proxy from GHSL building-height raster.
    Full SVF requires SOLWEIG/UMEP; this is a coarse raster-based approximation
    for use directly in the ML feature stack.
    """
    raise NotImplementedError
