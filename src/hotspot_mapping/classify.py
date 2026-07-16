"""
UHIMP - Phase 2: Heat Hotspot Identification (LOCAL VERSION — no GEE calls)

Reads the GeoTIFFs you already exported from GEE and does everything else
locally in Python: FR-2.3 (classification) and FR-2.4 (clustering).

Requires you to have downloaded these from Google Drive into a local folder:
    Delhi_LST.tif
    Delhi_NDVI.tif
    Delhi_NDBI.tif
    Delhi_NDWI.tif
    Delhi_LULC.tif
    (Delhi_HeatHotspots.tif is superseded by this script's own classification)

Install once:
    pip install rasterio numpy pandas geopandas scikit-learn shapely matplotlib
    pip install esda libpysal      # optional, for Getis-Ord Gi* cross-check

Run:
    python phase2_local.py --data-dir ./data/raw
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy as pixel_to_xy
import geopandas as gpd
from shapely.geometry import Point
from sklearn.cluster import DBSCAN


# ---------------------------------------------------------------------------
# 1. Load raster
# ---------------------------------------------------------------------------
def load_raster(path):
    """Reads a single-band GeoTIFF, returns (array, transform, crs, nodata)."""
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float64")
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
    return arr, transform, crs


# ---------------------------------------------------------------------------
# 2. FR-2.3 — Percentile / stddev heat stress classification
# ---------------------------------------------------------------------------
def classify_heat_stress(lst_array, method="percentile",
                          percentiles=(30, 60, 90), std_multipliers=(0.5, 0.5, 1.5)):
    """
    Classifies an LST numpy array into 4 categories relative to its own
    distribution (NaNs preserved as NaN in the output).

        0 = Low, 1 = Moderate, 2 = High, 3 = Severe

    method="percentile": cutoffs at the given percentiles of valid pixels.
    method="stddev": cutoffs at mean ± multiples of std dev.
    """
    valid = lst_array[~np.isnan(lst_array)]

    if method == "percentile":
        low_cut, mod_cut, high_cut = np.percentile(valid, percentiles)
    else:
        mean, std = valid.mean(), valid.std()
        low_cut = mean - std_multipliers[0] * std
        mod_cut = mean + std_multipliers[1] * std
        high_cut = mean + std_multipliers[2] * std

    classified = np.full(lst_array.shape, np.nan)
    mask_valid = ~np.isnan(lst_array)

    classified[mask_valid & (lst_array < low_cut)] = 0
    classified[mask_valid & (lst_array >= low_cut) & (lst_array < mod_cut)] = 1
    classified[mask_valid & (lst_array >= mod_cut) & (lst_array < high_cut)] = 2
    classified[mask_valid & (lst_array >= high_cut)] = 3

    cutoffs = {"low_cut": float(low_cut), "mod_cut": float(mod_cut), "high_cut": float(high_cut)}
    return classified, cutoffs


# ---------------------------------------------------------------------------
# 3. FR-2.4 — Spatial clustering into hotspot polygons
# ---------------------------------------------------------------------------
def raster_cells_to_points(classified_array, lst_array, transform, crs, min_class=2):
    """
    Converts High/Severe (class >= min_class) raster cells into a GeoDataFrame
    of points (cell centers), carrying the LST value along for later stats.
    """
    rows, cols = np.where(classified_array >= min_class)
    if len(rows) == 0:
        raise ValueError("No High/Severe cells found — check classification cutoffs.")

    xs, ys = pixel_to_xy(transform, rows, cols)
    lst_vals = lst_array[rows, cols]

    gdf = gpd.GeoDataFrame(
        {"LST": lst_vals, "row": rows, "col": cols},
        geometry=[Point(x, y) for x, y in zip(xs, ys)],
        crs=crs,
    )
    return gdf


def cluster_hotspots_dbscan(points_gdf, eps_m=150, min_samples=5):
    """
    Runs DBSCAN in meters (reprojects to a local UTM zone first, since raw
    lon/lat degrees don't have consistent distance meaning).
    Returns (hotspot_polygons_gdf, points_gdf_with_cluster_labels).
    """
    # Delhi falls in UTM zone 43N (EPSG:32643)
    utm_crs = "EPSG:32643"
    gdf_utm = points_gdf.to_crs(utm_crs)

    coords = np.column_stack([gdf_utm.geometry.x, gdf_utm.geometry.y])
    db = DBSCAN(eps=eps_m, min_samples=min_samples).fit(coords)

    gdf_utm = gdf_utm.copy()
    gdf_utm["cluster"] = db.labels_

    clustered = gdf_utm[gdf_utm["cluster"] != -1]  # drop noise (-1)
    n_noise = (gdf_utm["cluster"] == -1).sum()
    print(f"DBSCAN: {gdf_utm['cluster'].nunique() - (1 if n_noise else 0)} clusters found, "
          f"{n_noise} noise points dropped out of {len(gdf_utm)} total")

    if len(clustered) == 0:
        raise ValueError("DBSCAN found no clusters — try increasing eps_m or lowering min_samples.")

    polygons = (
        clustered.groupby("cluster")
        .apply(lambda g: g.unary_union.convex_hull)
        .reset_index(name="geometry")
    )
    polygons = gpd.GeoDataFrame(polygons, geometry="geometry", crs=utm_crs)

    stats = clustered.groupby("cluster").agg(
        mean_LST=("LST", "mean"),
        max_LST=("LST", "max"),
        point_count=("LST", "count"),
    ).reset_index()
    polygons = polygons.merge(stats, on="cluster")

    # Add area in km^2 (meaningful now that we're in a projected CRS)
    polygons["area_km2"] = polygons.geometry.area / 1e6

    # Convert back to WGS84 for downstream use / export
    polygons_wgs84 = polygons.to_crs("EPSG:4326")
    points_wgs84 = gdf_utm.to_crs("EPSG:4326")

    return polygons_wgs84, points_wgs84


# ---------------------------------------------------------------------------
# 3b. Optional: Getis-Ord Gi* statistical cross-check
# ---------------------------------------------------------------------------
def getis_ord_gi_star(points_gdf, value_col="LST", k_neighbors=8):
    """Statistical cross-check against DBSCAN, per FR-2.4's 'e.g., DBSCAN or Getis-Ord Gi*'."""
    try:
        from libpysal.weights import KNN
        from esda.getisord import G_Local
    except ImportError:
        print("[Skipped] Getis-Ord Gi* requires: pip install esda libpysal")
        return None

    w = KNN.from_dataframe(points_gdf, k=k_neighbors)
    w.transform = "r"
    g_local = G_Local(points_gdf[value_col].values, w, star=True)

    result = points_gdf.copy()
    result["Gi_star_z"] = g_local.Zs
    result["Gi_star_p"] = g_local.p_sim
    result["hotspot_significant"] = (result["Gi_star_z"] > 1.96) & (result["Gi_star_p"] < 0.05)
    return result


# ---------------------------------------------------------------------------
# 4. Main pipeline
# ---------------------------------------------------------------------------
def run_phase2(data_dir, output_dir, method="percentile", eps_m=75, min_samples=5):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load LST ----
    lst_path = data_dir / "Delhi_LST.tif"
    print(f"Loading {lst_path} ...")
    lst_array, transform, crs = load_raster(lst_path)
    valid_pct = 100 * (~np.isnan(lst_array)).sum() / lst_array.size
    print(f"LST raster: shape={lst_array.shape}, valid pixels={valid_pct:.1f}%, "
          f"range=[{np.nanmin(lst_array):.1f}, {np.nanmax(lst_array):.1f}] °C")

    # ---- FR-2.3: Classification ----
    classified, cutoffs = classify_heat_stress(lst_array, method=method)
    print(f"\nHeat stress cutoffs ({method}):", cutoffs)
    for cls, label in enumerate(["Low", "Moderate", "High", "Severe"]):
        count = np.sum(classified == cls)
        print(f"  Class {cls} ({label}): {count:,} pixels")

    # Save classified raster
    class_out_path = output_dir / "Delhi_HeatClass_4tier.tif"
    with rasterio.open(lst_path) as src:
        profile = src.profile
    profile.update(dtype="float32", nodata=np.nan)
    with rasterio.open(class_out_path, "w", **profile) as dst:
        dst.write(classified.astype("float32"), 1)
    print(f"Saved: {class_out_path}")

    # ---- FR-2.4: Clustering ----
    print("\nConverting High/Severe cells to points for clustering...")
    points_gdf = raster_cells_to_points(classified, lst_array, transform, crs, min_class=2)
    print(f"{len(points_gdf):,} High/Severe cells found")

    hotspot_polygons, points_with_clusters = cluster_hotspots_dbscan(
        points_gdf, eps_m=eps_m, min_samples=min_samples
    )

    print(f"\nTop hotspot clusters by mean LST:")
    print(hotspot_polygons[["cluster", "mean_LST", "max_LST", "point_count", "area_km2"]]
          .sort_values("mean_LST", ascending=False).to_string(index=False))

    polygons_out_path = output_dir / "Delhi_HeatHotspot_Polygons.geojson"
    hotspot_polygons.to_file(polygons_out_path, driver="GeoJSON")
    print(f"Saved: {polygons_out_path}")

    # ---- Optional Gi* cross-check ----
    gi_result = getis_ord_gi_star(points_with_clusters, value_col="LST")
    if gi_result is not None:
        n_sig = gi_result["hotspot_significant"].sum()
        print(f"\nGetis-Ord Gi* cross-check: {n_sig:,} statistically significant hotspot "
              f"points out of {len(gi_result):,}")
        gi_out_path = output_dir / "Delhi_GiStar_points.geojson"
        gi_result.to_file(gi_out_path, driver="GeoJSON")
        print(f"Saved: {gi_out_path}")

    print("\n--- Phase 2 (local) complete ---")
    print("FR-2.1: uses your existing exported LST (already emissivity-corrected upstream)")
    print("FR-2.2: not implemented (ECOSTRESS fusion) — documented limitation")
    print("FR-2.3: done — adaptive classification, see cutoffs above")
    print("FR-2.4: done — DBSCAN polygons" + (" + Gi* cross-check" if gi_result is not None else ""))
    print("FR-2.5: supported structurally — rerun this script against a different composite for other periods")

    return classified, hotspot_polygons


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="./data/raw",
                         help="Folder containing the GeoTIFFs downloaded from Google Drive")
    parser.add_argument("--output-dir", default="./outputs/heat_maps")
    parser.add_argument("--method", default="percentile", choices=["percentile", "stddev"])
    parser.add_argument("--eps-m", type=float, default=75,
                         help="DBSCAN neighborhood radius in meters")
    parser.add_argument("--min-samples", type=int, default=5,
                         help="DBSCAN minimum points to form a cluster")
    args = parser.parse_args()

    run_phase2(args.data_dir, args.output_dir, args.method, args.eps_m, args.min_samples)