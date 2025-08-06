from arcgis.gis import GIS
from arcgis.features import GeoAccessor
import geopandas as gpd
import os
import requests
from io import StringIO

# AGOL login
username = os.environ['AGOL_USERNAME']
password = os.environ['AGOL_PASSWORD']
gis = GIS("https://www.arcgis.com", username, password)

# --- WFS setup ---
wfs_url = "https://environment.data.gov.uk/spatialdata/aims-structure/wfs"
type_name = "dataset-6232eb53-0573-4183-bce2-0de344cd3820:AIMS_Structure_Point"

# Build valid GetFeature request
params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeName": type_name,
    "outputFormat": "json"
}

print("Downloading WFS data...")
response = requests.get(wfs_url, params=params)
response.raise_for_status()  # Raise error for HTTP 4xx/5xx

# Read GeoJSON as GeoDataFrame
gdf = gpd.read_file(StringIO(response.text))
print(f"Downloaded {len(gdf)} features.")

# Drop features without geometry
gdf = gdf[gdf.geometry.notnull()]

# Convert to Spatially Enabled DataFrame
sdf = GeoAccessor.from_geodataframe(gdf)

# --- AGOL Layer Setup ---
feature_layer_id = "d6aadf0d813a4babab51c4104a72338b"
fl_item = gis.content.get(feature_layer_id)
layer = fl_item.layers[0]

# Overwrite layer: truncate then add
print("Truncating existing layer...")
layer.manager.truncate()

print("Uploading new data...")
layer.edit_features(adds=sdf.spatial.to_featureset())

print("✅ Update complete.")


