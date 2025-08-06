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

params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeName": type_name,
    "outputFormat": "application/json"  # More explicit
}

print("Downloading WFS data...")
response = requests.get(wfs_url, params=params)
response.raise_for_status()

# Read as GeoDataFrame
gdf = gpd.read_file(StringIO(response.text))

print(f"Downloaded {len(gdf)} features.")

# --- Fix geometry ---
gdf = gdf[gdf.geometry.notnull()]
gdf = gdf[gdf.is_valid]

# Ensure correct geometry column is active
gdf.set_geometry("geometry", inplace=True)

# --- Convert to Spatial DataFrame ---
sdf = GeoAccessor.from_geodataframe(gdf)

# --- AGOL Layer Setup ---
feature_layer_id = "d6aadf0d813a4babab51c4104a72338b"
fl_item = gis.content.get(feature_layer_id)

if fl_item is None:
    raise ValueError("Feature layer item not found. Check the item ID.")

layer = fl_item.layers[0]

# --- Upload ---
print("Truncating existing layer...")
layer.manager.truncate()

print("Uploading new data in batches...")
batch_size = 500
features = sdf.spatial.to_featureset().features

# Verify at least one feature has geometry
assert "geometry" in features[0], "❌ Geometry missing in uploaded features."

for i in range(0, len(features), batch_size):
    batch = features[i:i + batch_size]
    print(f"Uploading batch {i // batch_size + 1} with {len(batch)} features...")
    result = layer.edit_features(adds=batch)
    if "addResults" not in result or not all(f["success"] for f in result["addResults"]):
        raise RuntimeError("Some features failed to upload.")

print("✅ Update complete.")
