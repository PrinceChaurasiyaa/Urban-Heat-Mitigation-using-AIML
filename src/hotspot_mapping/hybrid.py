"""
UHIMP - Phase 2: Heat Hotspot Identification
Method: Connected Components (shape) + Getis-Ord Gi* (statistical significance)
Replaces the DBSCAN approach, which mega-merged large contiguous hot regions
into single unusable polygons (see project notes).

Fills FR-2.1 (uses upstream corrected LST), FR-2.3, FR-2.4, FR-2.5.
FR-2.2 (ECOSTRESS fusion) intentionally not implemented — documented limitation.

Pipeline:
    1. Load LST raster, classify into Low/Moderate/High/Severe (FR-2.3)
    2. Connected Components on High+Severe mask -> candidate regions (shape)
    3. Getis-Ord Gi* on the full LST raster -> per-pixel z-score/p-value (significance)
    4. Keep only pixels that are BOTH in a candidate region AND statistically
       significant (z > 1.96, p < 0.05) -> final hotspot mask
    5. Re-run connected components on the filtered mask -> final hotspot polygons
       (this naturally splits mega-clusters, since non-significant "fringe"
       pixels get dropped, breaking weak connectivity bridges)

Install:
    pip install rasterio numpy pandas geopandas shapely scipy libpysal esda

Run:
    python phase2_gi_star.py --data-dir ./data/raw/landsat8 --output-dir ./outputs/heat_maps
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy as pixel_to_xy
from rasterio.features import shapes as raster_shapes
import geopandas as gpd
from shapely.geometry import shape as shapely_shape
from scipy import ndimage


# ---------------------------------------------------------------------------
# 1. Load raster
# ---------------------------------------------------------------------------
def load_raster(path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float64")
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
    return arr, transform, crs


# ---------------------------------------------------------------------------
# 2. FR-2.3 — Percentile / stddev classification (unchanged from before)
# ---------------------------------------------------------------------------
def classify_heat_stress(lst_array, method="percentile",
                          percentiles=(30, 60, 90), std_multipliers=(0.5, 0.5, 1.5)):
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
# 3. Connected Components — candidate region shapes (no distance parameter)
# ---------------------------------------------------------------------------
def connected_components(classified_array, min_class=2, connectivity=8):
    """
    Labels contiguous blobs of High+Severe pixels (class >= min_class).
    connectivity=8 treats diagonal neighbors as connected (standard for
    raster hotspot work); connectivity=4 is stricter (edge-only).

    Returns (labeled_array, num_features).
    """
    candidate_mask = np.where(classified_array >= min_class, 1, 0)

    if connectivity == 8:
        structure = np.ones((3, 3), dtype=int)
    else:
        structure = ndimage.generate_binary_structure(2, 1)

    labeled, num_features = ndimage.label(candidate_mask, structure=structure)
    print(f"Connected Components: {num_features} candidate regions found "
          f"(before significance filtering)")

    # Report the size distribution so you can see the mega-cluster problem directly
    sizes = ndimage.sum(candidate_mask, labeled, range(1, num_features + 1))
    if len(sizes) > 0:
        print(f"  Region sizes (pixels): min={sizes.min():.0f}, "
              f"median={np.median(sizes):.0f}, max={sizes.max():.0f}")
        print(f"  Largest region covers {sizes.max() / candidate_mask.sum() * 100:.1f}% "
              f"of all High/Severe pixels")

    return labeled, num_features


# ---------------------------------------------------------------------------
# 4. Getis-Ord Gi* — statistical significance per pixel
# ---------------------------------------------------------------------------
def compute_gi_star_raster(lst_array, k_neighbors=8, subsample_for_speed=None,
                            use_permutation_test=False, n_permutations=99):
    """
    Computes Getis-Ord Gi* z-scores for every valid pixel in the LST raster,
    using a KNN spatial weights graph built from pixel row/col positions.

    Full-resolution rasters (millions of pixels) make a dense/global KNN
    graph slow; `subsample_for_speed` lets you coarsen the grid for speed
    if needed (e.g., subsample_for_speed=2 uses every 2nd pixel in each
    dimension, then upsamples results back — trades resolution for runtime).

    use_permutation_test=False (default): skips esda's conditional-permutation
    p-value estimation entirely (the `_crand_plus`/joblib path that causes
    MemoryError on large rasters — each worker process has to pickle a chunk
    of the weights/data to ship across processes, which blows up RAM well
    before hundreds of thousands of pixels finish). Instead, the p-value is
    derived analytically from the z-score via the standard normal CDF, which
    is the same interpretation ("z > 1.96 = 95% confidence") most Gi* usage
    relies on anyway. Set True only on already-subsampled/small rasters where
    you specifically want esda's simulated p-values.

    Returns a z-score array the same shape as lst_array (NaN where invalid).
    """
    from libpysal.weights import KNN
    from esda.getisord import G_Local
    from scipy import stats as scipy_stats

    if subsample_for_speed and subsample_for_speed > 1:
        s = subsample_for_speed
        work_array = lst_array[::s, ::s]
    else:
        s = 1
        work_array = lst_array

    rows, cols = np.where(~np.isnan(work_array))
    values = work_array[rows, cols]
    coords = np.column_stack([cols, rows])  # x=col, y=row for KNN

    print(f"Computing Getis-Ord Gi* on {len(values):,} pixels "
          f"(k={k_neighbors} neighbors, permutation_test={use_permutation_test})...")

    w = KNN(coords, k=k_neighbors)
    w.transform = "r"

    permutations = n_permutations if use_permutation_test else 0
    g_local = G_Local(values, w, star=True, permutations=permutations)

    z_full = np.full(work_array.shape, np.nan)
    p_full = np.full(work_array.shape, np.nan)
    z_full[rows, cols] = g_local.Zs

    if use_permutation_test:
        p_full[rows, cols] = g_local.p_sim
    else:
        # Analytic two-tailed p-value from the z-score (standard normal),
        # avoids esda's permutation/joblib path entirely.
        p_full[rows, cols] = 2 * (1 - scipy_stats.norm.cdf(np.abs(g_local.Zs)))

    if s > 1:
        # Upsample back to original resolution via nearest-neighbor repeat
        z_full = np.repeat(np.repeat(z_full, s, axis=0), s, axis=1)[:lst_array.shape[0], :lst_array.shape[1]]
        p_full = np.repeat(np.repeat(p_full, s, axis=0), s, axis=1)[:lst_array.shape[0], :lst_array.shape[1]]

    return z_full, p_full


# ---------------------------------------------------------------------------
# 5. Combine: significant pixels within candidate regions -> final hotspots
# ---------------------------------------------------------------------------
def build_significant_hotspots(classified_array, z_array, p_array,
                                min_class=2, z_thresh=1.96, p_thresh=0.05,
                                connectivity=8, min_region_pixels=5):
    """
    Final hotspot mask = (candidate region pixel) AND (statistically significant).
    Re-labels connected components on this filtered mask, which naturally
    splits any mega-cluster wherever non-significant pixels break the chain.
    """
    candidate_mask = classified_array >= min_class
    significant_mask = (z_array > z_thresh) & (p_array < p_thresh)

    final_mask = candidate_mask & significant_mask

    structure = np.ones((3, 3), dtype=int) if connectivity == 8 else ndimage.generate_binary_structure(2, 1)
    labeled, num_features = ndimage.label(final_mask, structure=structure)

    # Drop tiny spurious regions below min_region_pixels
    sizes = ndimage.sum(final_mask, labeled, range(1, num_features + 1))
    small_labels = [i + 1 for i, sz in enumerate(sizes) if sz < min_region_pixels]
    for lbl in small_labels:
        labeled[labeled == lbl] = 0

    # Relabel to close numbering gaps
    labeled, num_features = ndimage.label(labeled > 0, structure=structure)

    print(f"\nFinal significant hotspots after Gi* filtering: {num_features} "
          f"(dropped {len(small_labels)} regions smaller than {min_region_pixels} pixels)")

    return labeled, num_features


# ---------------------------------------------------------------------------
# 6. Vectorize final labeled regions into polygons with stats
# ---------------------------------------------------------------------------
def labeled_regions_to_polygons(labeled_array, lst_array, z_array, transform, crs):
    """Converts the final labeled raster into a GeoDataFrame of hotspot polygons with stats."""
    records = []
    geoms = []

    mask = labeled_array > 0
    for geom, value in raster_shapes(labeled_array.astype("int32"), mask=mask, transform=transform):
        region_id = int(value)
        region_pixels = labeled_array == region_id
        rows, cols = np.where(region_pixels)

        records.append({
            "region_id": region_id,
            "mean_LST": float(np.nanmean(lst_array[region_pixels])),
            "max_LST": float(np.nanmax(lst_array[region_pixels])),
            "mean_Gi_star_z": float(np.nanmean(z_array[region_pixels])),
            "pixel_count": int(region_pixels.sum()),
        })
        geoms.append(shapely_shape(geom))

    gdf = gpd.GeoDataFrame(records, geometry=geoms, crs=crs)

    # Dissolve multi-part shapes sharing the same region_id (raster_shapes can
    # split a region into multiple polygon parts at pixel boundaries)
    gdf = gdf.dissolve(by="region_id", aggfunc={
        "mean_LST": "mean", "max_LST": "max", "mean_Gi_star_z": "mean", "pixel_count": "sum"
    }).reset_index()

    # Area in km^2 via UTM reprojection (Delhi = zone 43N)
    gdf_utm = gdf.to_crs("EPSG:32643")
    gdf["area_km2"] = gdf_utm.geometry.area / 1e6

    return gdf


# ---------------------------------------------------------------------------
# 7. Main pipeline
# ---------------------------------------------------------------------------
def run_phase2(data_dir, output_dir, method="percentile",
               k_neighbors=8, z_thresh=1.96, p_thresh=0.05,
               subsample_for_speed=None, min_region_pixels=5,
               use_permutation_test=False):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lst_path = data_dir / "Delhi_LST.tif"
    print(f"Loading {lst_path} ...")
    lst_array, transform, crs = load_raster(lst_path)
    valid_pct = 100 * (~np.isnan(lst_array)).sum() / lst_array.size
    print(f"LST raster: shape={lst_array.shape}, valid pixels={valid_pct:.1f}%, "
          f"range=[{np.nanmin(lst_array):.1f}, {np.nanmax(lst_array):.1f}] °C\n")

    # ---- FR-2.3 ----
    classified, cutoffs = classify_heat_stress(lst_array, method=method)
    print(f"Heat stress cutoffs ({method}): {cutoffs}")
    for cls, label in enumerate(["Low", "Moderate", "High", "Severe"]):
        print(f"  Class {cls} ({label}): {np.sum(classified == cls):,} pixels")

    class_out_path = output_dir / "Delhi_HeatClass_4tier.tif"
    with rasterio.open(lst_path) as src:
        profile = src.profile
    profile.update(dtype="float32", nodata=np.nan)
    with rasterio.open(class_out_path, "w", **profile) as dst:
        dst.write(classified.astype("float32"), 1)
    print(f"Saved: {class_out_path}\n")

    # ---- Connected Components (candidate shapes) ----
    candidate_labeled, n_candidates = connected_components(classified, min_class=2)

    # ---- Getis-Ord Gi* (significance) ----
    z_array, p_array = compute_gi_star_raster(
        lst_array, k_neighbors=k_neighbors, subsample_for_speed=subsample_for_speed,
        use_permutation_test=use_permutation_test,
    )

    gi_out_path = output_dir / "Delhi_GiStar_zscore.tif"
    with rasterio.open(gi_out_path, "w", **profile) as dst:
        dst.write(z_array.astype("float32"), 1)
    print(f"Saved: {gi_out_path}\n")

    # ---- FR-2.4: Final significant hotspots ----
    final_labeled, n_final = build_significant_hotspots(
        classified, z_array, p_array,
        min_class=2, z_thresh=z_thresh, p_thresh=p_thresh,
        min_region_pixels=min_region_pixels,
    )

    hotspot_gdf = labeled_regions_to_polygons(final_labeled, lst_array, z_array, transform, crs)
    hotspot_gdf = hotspot_gdf.sort_values("mean_LST", ascending=False)

    print(f"\nTop hotspots by mean LST:")
    print(hotspot_gdf[["region_id", "mean_LST", "max_LST", "mean_Gi_star_z", "area_km2", "pixel_count"]]
          .head(20).to_string(index=False))

    print(f"\nArea distribution check (no more mega-clusters expected):")
    print(f"  Largest hotspot: {hotspot_gdf['area_km2'].max():.2f} km²")
    print(f"  Median hotspot: {hotspot_gdf['area_km2'].median():.2f} km²")
    print(f"  Total hotspots: {len(hotspot_gdf)}")

    polygons_out_path = output_dir / "Delhi_HeatHotspot_Polygons_GiStar.geojson"
    hotspot_gdf.to_file(polygons_out_path, driver="GeoJSON")
    print(f"Saved: {polygons_out_path}")

    print("\n--- Phase 2 (Connected Components + Gi*) complete ---")
    print("FR-2.1: uses upstream corrected LST")
    print("FR-2.2: not implemented (ECOSTRESS fusion) — documented limitation")
    print("FR-2.3: done")
    print("FR-2.4: done — statistically significant hotspots, no mega-cluster artifact")
    print("FR-2.5: supported structurally — rerun against a different composite for other periods")

    return classified, hotspot_gdf


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="./data/raw/landsat8")
    parser.add_argument("--output-dir", default="./outputs/heat_maps")
    parser.add_argument("--method", default="percentile", choices=["percentile", "stddev"])
    parser.add_argument("--k-neighbors", type=int, default=8,
                         help="Number of neighbors for Gi* spatial weights")
    parser.add_argument("--z-thresh", type=float, default=1.96,
                         help="Gi* z-score threshold (1.96 = 95% confidence)")
    parser.add_argument("--p-thresh", type=float, default=0.05)
    parser.add_argument("--subsample", type=int, default=None,
                         help="Coarsen grid by this factor for Gi* speed (e.g. 2 or 4). "
                              "Recommended for rasters with >500k valid pixels.")
    parser.add_argument("--min-region-pixels", type=int, default=5)
    parser.add_argument("--use-permutation-test", action="store_true",
                         help="Use esda's simulated p-value (slow, memory-heavy on large "
                              "rasters — causes MemoryError above ~100k-200k pixels on "
                              "typical machines). Default off: p-value is derived "
                              "analytically from the z-score instead.")
    args = parser.parse_args()

    run_phase2(
        args.data_dir, args.output_dir, args.method,
        args.k_neighbors, args.z_thresh, args.p_thresh,
        args.subsample, args.min_region_pixels,
        args.use_permutation_test,
    )