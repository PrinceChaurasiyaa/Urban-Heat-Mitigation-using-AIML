import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

with rasterio.open("outputs/heat_maps/Delhi_HeatClass_4tier.tif") as src:
    heat = src.read(1)
    bounds = src.bounds

gdf = gpd.read_file("outputs/heat_maps/Delhi_HeatHotspot_Polygons.geojson")

cmap = ListedColormap([
    "#2ECC71",
    "#F1C40F",
    "#E67E22",
    "#E74C3C"
])

fig, ax = plt.subplots(figsize=(12,10))

ax.imshow(
    heat,
    cmap=cmap,
    extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
    origin="upper"
)

gdf.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1
)

plt.title("Urban Heat Hotspots")
plt.axis("off")
plt.show()