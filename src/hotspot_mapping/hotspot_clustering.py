"""M2: Spatial clustering of high/severe heat cells into hotspot polygons.
Implements FR-2.4 (DBSCAN / Getis-Ord Gi*).
"""


def cluster_hotspots_dbscan(points_gdf, eps_m=100, min_samples=5):
    """
    TODO: run DBSCAN on high/severe-classified grid-cell centroids
    (geopandas GeoDataFrame) and dissolve resulting clusters into hotspot polygons.
    """
    raise NotImplementedError


def getis_ord_gi_star(points_gdf, value_col="LST_C", k_neighbors=8):
    """TODO: compute Getis-Ord Gi* hot spot statistic as a cross-check clustering method."""
    raise NotImplementedError
