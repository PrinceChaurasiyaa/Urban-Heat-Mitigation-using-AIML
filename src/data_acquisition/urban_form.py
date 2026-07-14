"""M1: OSM / GHSL / UT-GLOBUS urban morphology connectors (FR-1.6)."""

import ee


def fetch_ghsl_built_up(cfg, aoi):
    """GHSL built-up volume/height/density grid (JRC GHSL, via GEE catalog)."""
    return (
        ee.Image("JRC/GHSL/P2023A/GHS_BUILT_H/2018")
        .clip(aoi)
    )


def fetch_osm_buildings(cfg, aoi):
    """
    TODO: pull OSM building footprints / road network via Overpass API
    for the AOI, since OSM vector data is not natively hosted in GEE.
    """
    raise NotImplementedError


def fetch_ut_globus(cfg, aoi):
    """TODO: ingest UT-GLOBUS building-level morphology data, if available for this city."""
    raise NotImplementedError
