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
wfs_url = "https://environment.data.gov.uk/spatialdata/historic-landfill/wfs"
type_name = "dataset-7a955570-d465-11e4-a37c-f0def148f590:Historic_Landfill_Sites"

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
feature_layer_id = "c7647810cb124f47a3224692868e1d58"
fl_item = gis.content.get(feature_layer_id)
layer = fl_item.layers[0]

# Overwrite layer: truncate then add
print("Truncating existing layer...")
layer.manager.truncate()

print("Uploading new data in batches...")
batch_size = 500
features = sdf.spatial.to_featureset().features

for i in range(0, len(features), batch_size):
    batch = features[i:i + batch_size]
    print(f"Uploading batch {i // batch_size + 1} with {len(batch)} features...")
    layer.edit_features(adds=batch)

print("✅ Update complete.")


