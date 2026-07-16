"""
UHIMP - Phase 2 add-on: Size tiering + visualization of Gi*-filtered hotspots.

Takes the output of hybrid.py (Delhi_HeatHotspot_Polygons_GiStar.geojson +
Delhi_HeatClass_4tier.tif) and:
    1. Adds a `tier` column (priority / moderate / minor) based on area_km2
    2. Renders a matplotlib map: classified LST background + hotspot outlines,
       color-coded and sized by tier, so you can actually eyeball whether
       large regions (like your 13.14 km² region 84) look like coherent
       urban features or residual over-merging artifacts.

Install (if not already):
    pip install matplotlib rasterio geopandas

Run:
    python phase2_visualize.py --output-dir ./outputs/heat_maps
"""

import argparse
from pathlib import Path

import numpy as np
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from rasterio.plot import plotting_extent


# ---------------------------------------------------------------------------
# 1. Size tiering
# ---------------------------------------------------------------------------
def add_size_tiers(gdf, priority_km2=1.0, moderate_km2=0.1):
    """
    Adds a `tier` column based on area_km2:
        priority: area_km2 >= priority_km2   (headline intervention zones)
        moderate: moderate_km2 <= area_km2 < priority_km2
        minor:    area_km2 < moderate_km2     (small, still real, secondary list)

    Defaults: priority >= 1 km², moderate 0.1-1 km², minor < 0.1 km²
    Tune these based on your city's scale and how many "priority" zones
    you actually want to headline in the final report.
    """
    def tier_fn(area):
        if area >= priority_km2:
            return "priority"
        elif area >= moderate_km2:
            return "moderate"
        else:
            return "minor"

    gdf = gdf.copy()
    gdf["tier"] = gdf["area_km2"].apply(tier_fn)

    counts = gdf["tier"].value_counts()
    print("Size tier breakdown:")
    for tier in ["priority", "moderate", "minor"]:
        n = counts.get(tier, 0)
        total_area = gdf.loc[gdf["tier"] == tier, "area_km2"].sum()
        print(f"  {tier:9s}: {n:4d} hotspots, {total_area:8.2f} km² total")

    return gdf


# ---------------------------------------------------------------------------
# 2. Visualization
# ---------------------------------------------------------------------------
def plot_hotspots(classified_tif_path, hotspot_gdf, output_path,
                   title="Delhi Urban Heat Hotspots (Gi*-filtered)"):
    """
    Renders the classified LST raster (Low/Moderate/High/Severe) as a
    background, with hotspot polygons overlaid, colored and styled by tier:
        priority: thick red outline
        moderate: medium orange outline
        minor:    thin, semi-transparent outline

    This lets you visually confirm whether large regions are coherent
    urban features or artifacts of residual merging.
    """
    with rasterio.open(classified_tif_path) as src:
        classified = src.read(1)
        extent = plotting_extent(src)
        raster_crs = src.crs

    classified_masked = np.ma.masked_invalid(classified)

    # Match your original 4-tier palette
    cmap = ListedColormap(["#2c7bb6", "#ffffbf", "#fdae61", "#d7191c"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)

    fig, ax = plt.subplots(figsize=(14, 12))
    ax.imshow(classified_masked, cmap=cmap, norm=norm, extent=extent, origin="upper")

    hotspot_gdf = hotspot_gdf.to_crs(raster_crs)

    tier_styles = {
        "priority": dict(edgecolor="black", facecolor="none", linewidth=2.2, alpha=1.0, zorder=3),
        "moderate": dict(edgecolor="dimgray", facecolor="none", linewidth=1.2, alpha=0.9, zorder=2),
        "minor":    dict(edgecolor="gray", facecolor="none", linewidth=0.5, alpha=0.6, zorder=1),
    }

    for tier, style in tier_styles.items():
        subset = hotspot_gdf[hotspot_gdf["tier"] == tier]
        if len(subset) > 0:
            subset.boundary.plot(ax=ax, **style)

    # Label only the priority hotspots (too cluttered otherwise)
    priority = hotspot_gdf[hotspot_gdf["tier"] == "priority"].sort_values(
        "area_km2", ascending=False
    )
    for idx, row in priority.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            f"#{row['region_id']}\n{row['area_km2']:.1f} km²\n{row['mean_LST']:.1f}°C",
            xy=(centroid.x, centroid.y),
            fontsize=8, ha="center", va="center",
            color="black", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.75, edgecolor="none"),
            zorder=4,
        )

    # Legend: heat classes + tier outlines
    class_legend = [
        Patch(facecolor="#2c7bb6", label="Low"),
        Patch(facecolor="#ffffbf", label="Moderate"),
        Patch(facecolor="#fdae61", label="High"),
        Patch(facecolor="#d7191c", label="Severe"),
    ]
    tier_legend = [
        Patch(edgecolor="black", facecolor="none", linewidth=2.2, label="Priority hotspot (\u2265 1 km\u00b2)"),
        Patch(edgecolor="dimgray", facecolor="none", linewidth=1.2, label="Moderate hotspot"),
        Patch(edgecolor="gray", facecolor="none", linewidth=0.5, label="Minor hotspot"),
    ]
    legend1 = ax.legend(handles=class_legend, loc="upper left", title="Heat class", framealpha=0.9)
    ax.add_artist(legend1)
    ax.legend(handles=tier_legend, loc="lower left", title="Hotspot tier", framealpha=0.9)

    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"\nSaved map: {output_path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Focused inspection of the largest hotspot (sanity-check merging artifact)
# ---------------------------------------------------------------------------
def plot_largest_hotspot_closeup(classified_tif_path, hotspot_gdf, output_path):
    """
    Zooms into just the single largest hotspot polygon, so you can visually
    judge whether it's a coherent urban feature (e.g. an industrial belt)
    or an oddly-shaped, thin, stretched artifact suggesting residual
    over-merging along a weak connectivity chain.
    """
    largest = hotspot_gdf.loc[hotspot_gdf["area_km2"].idxmax()]

    with rasterio.open(classified_tif_path) as src:
        classified = src.read(1)
        extent = plotting_extent(src)
        raster_crs = src.crs

    hotspot_gdf_proj = hotspot_gdf.to_crs(raster_crs)
    largest_geom = hotspot_gdf_proj.loc[hotspot_gdf_proj["area_km2"].idxmax(), "geometry"]

    minx, miny, maxx, maxy = largest_geom.bounds
    pad_x = (maxx - minx) * 0.3 or 0.01
    pad_y = (maxy - miny) * 0.3 or 0.01

    cmap = ListedColormap(["#2c7bb6", "#ffffbf", "#fdae61", "#d7191c"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)

    fig, ax = plt.subplots(figsize=(10, 9))
    classified_masked = np.ma.masked_invalid(classified)
    ax.imshow(classified_masked, cmap=cmap, norm=norm, extent=extent, origin="upper")

    gpd.GeoSeries([largest_geom], crs=raster_crs).boundary.plot(
        ax=ax, edgecolor="black", linewidth=2.5
    )

    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_title(
        f"Close-up: Largest hotspot (region {int(largest['region_id'])}, "
        f"{largest['area_km2']:.2f} km\u00b2, mean LST {largest['mean_LST']:.1f}\u00b0C)\n"
        f"Check shape: coherent zone, or thin/stretched merging artifact?",
        fontsize=11,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved close-up: {output_path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. Main
# ---------------------------------------------------------------------------
def main(output_dir, priority_km2, moderate_km2):
    output_dir = Path(output_dir)

    geojson_path = output_dir / "Delhi_HeatHotspot_Polygons_GiStar.geojson"
    classified_tif_path = output_dir / "Delhi_HeatClass_4tier.tif"

    print(f"Loading {geojson_path} ...")
    hotspot_gdf = gpd.read_file(geojson_path)
    print(f"{len(hotspot_gdf)} hotspot polygons loaded\n")

    # ---- Size tiering ----
    hotspot_gdf = add_size_tiers(hotspot_gdf, priority_km2=priority_km2, moderate_km2=moderate_km2)

    tiered_out_path = output_dir / "Delhi_HeatHotspot_Polygons_Tiered.geojson"
    hotspot_gdf.to_file(tiered_out_path, driver="GeoJSON")
    print(f"\nSaved tiered polygons: {tiered_out_path}")

    # ---- Full map ----
    plot_hotspots(
        classified_tif_path, hotspot_gdf,
        output_dir / "delhi_hotspots_map.png",
    )

    # ---- Close-up on the largest hotspot ----
    plot_largest_hotspot_closeup(
        classified_tif_path, hotspot_gdf,
        output_dir / "delhi_largest_hotspot_closeup.png",
    )

    print("\n--- Visualization complete ---")
    print(f"Review: {output_dir / 'delhi_hotspots_map.png'}")
    print(f"Review: {output_dir / 'delhi_largest_hotspot_closeup.png'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="./outputs/heat_maps",
                         help="Directory containing Delhi_HeatHotspot_Polygons_GiStar.geojson "
                              "and Delhi_HeatClass_4tier.tif from hybrid.py")
    parser.add_argument("--priority-km2", type=float, default=1.0,
                         help="Minimum area (km²) to classify a hotspot as 'priority'")
    parser.add_argument("--moderate-km2", type=float, default=0.1,
                         help="Minimum area (km²) to classify a hotspot as 'moderate' "
                              "(below this = 'minor')")
    args = parser.parse_args()

    main(args.output_dir, args.priority_km2, args.moderate_km2)