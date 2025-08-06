from arcgis.gis import GIS
from arcgis.features import GeoAccessor
import geopandas as gpd
import os

# AGOL login
username = os.environ['AGOL_USERNAME']
password = os.environ['AGOL_PASSWORD']

gis = GIS("https://www.arcgis.com", username, password)

# WFS endpoint
wfs_url = "https://environment.data.gov.uk/spatialdata/aims-structure/wfs"
layer_name = "environment-agency:aims_structure"

print("Downloading WFS data...")
gdf = gpd.read_file(wfs_url, layer=layer_name)
gdf = gdf[gdf.geometry.notnull()]
print(f"Downloaded {len(gdf)} features.")

# Convert to Spatially Enabled DataFrame
sdf = GeoAccessor.from_geodataframe(gdf)

# AGOL Feature Layer to update
feature_layer_id = "1b3bc88f5f37407ea19641d786819977"
fl_item = gis.content.get(feature_layer_id)
layer = fl_item.layers[0]

print("Truncating existing layer...")
layer.manager.truncate()

print("Uploading new data...")
layer.edit_features(adds=sdf.spatial.to_featureset())

print("✅ Update complete.")