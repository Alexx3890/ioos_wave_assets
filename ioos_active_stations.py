#!/usr/bin/env python
# coding: utf-8

# # Read realtime data from IOOS Sensor Map via ERDDAP tabledap
# 
# Created: 2026-07-22
# 
# Updated: 2026-07-22
# 
# Suppose you are exploring the [IOOS Sensor Map](https://sensors.ioos.us/),
# and would like to build a map of the recently active stations. (stations that have reported data in the last 30 days)
# 
# One can download the data in multiple forms from the site, but aggregating all the stations together on one map is tricky.
# 
# These features makes Sensor map an extremely useful tool for quick data explorations but now imagine if you want automate that instead of exploring the Sensor Map interactively? Or if you want to make multiple small modification to your query? It would be very tedious and error prone to try that with the Sensor Map interface. The good news is that we cab automate that by querying the ERDDAP server directly.
# 
# We can search for datasets reporting wave data in the last 30 days. We can return the unique coordinates for each dataset so we can build a map.


from erddapy import ERDDAP
import folium
import geopandas as gpd
import pandas as pd


server = "http://erddap.sensors.ioos.us/erddap"
e = ERDDAP(server=server, protocol="tabledap")

import pandas as pd

kw = {
    "min_time": "now-30days",
    "search_for": "waves"
}

url = e.get_search_url(response="csv", **kw)
df = pd.read_csv(url)
dataset_ids = df["Dataset ID"]

e.variables = ["longitude", "latitude"]
e.constraints = {
  "time>=": "now-30days",
  "time<": "now",
}
kw = {"distinct": True}

df_out = pd.DataFrame()
for dataset_id in dataset_ids:
    e.dataset_id = dataset_id
    try:
      df = e.to_pandas(
      response="csvp",
      **kw
    )
      df['dataset_id'] = dataset_id
    except:
      print(f"{dataset_id} no valid data.")


    df_out = pd.concat([df_out, df])

# convert to geodataframe

sensor_gdf = gpd.GeoDataFrame(
                df_out,
                geometry=gpd.points_from_xy(
                    df_out['longitude (degrees_east)'], df_out['latitude (degrees_north)']
                ),
                crs="epsg:4326",
            )


# Finally, we can make a map of the stations that have reported data in the last 30 days.

# ## Get HF-Radar stations with wave info

server = "https://hfradar.ioos.us/erddap/"
e = ERDDAP(server=server, protocol="tabledap")

kw = {
    "min_time": "now-30days",
    "search_for": "Wave data"
}

url = e.get_search_url(response="csv", **kw)
df = pd.read_csv(url)
dataset_ids = df["Dataset ID"]

e.variables = ["longitude", "latitude"]
e.constraints = {
  "time>=": "now-30days",
  "time<": "now",
}
kw = {"distinct": True}

df_out = pd.DataFrame()
for dataset_id in dataset_ids:
    e.dataset_id = dataset_id
    try:
      df = e.to_pandas(
      response="csvp",
      **kw
    )
      df['dataset_id'] = dataset_id
    except:
      print(f"{dataset_id} no valid data.")


    df_out = pd.concat([df_out, df])

# convert to geodataframe
hfr_gdf = gpd.GeoDataFrame(
                df_out,
                geometry=gpd.points_from_xy(
                    df_out['longitude (degrees_east)'], df_out['latitude (degrees_north)']
                ),
                crs="epsg:4326",
            )


# ## Read in data from CY2025 Asset Inventory
# 
# Gather appropriate wave datasets from https://erddap.ioos.us/erddap/tabledap/processed_asset_inventory.html
# 
# Wave datasets are defined by `Waves="X"`.

url = "https://erddap.ioos.us/erddap/tabledap/processed_asset_inventory.geoJson?&Year=2025&Waves=%22X%22"
asset_inventory_gdf = gpd.read_file(url)



# Now make a map with those layers
## Initialize map
m = folium.Map(
    tiles=None,
    zoom_start=13,
)

## Add base Layers
tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
gh_repo = "https://github.com/ioos/ioos_code_lab"
attr = f'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri | <a href="{gh_repo}" target="_blank">{gh_repo}</a>'
folium.raster_layers.TileLayer(
    name="Ocean",
    tiles=tiles,
    attr=attr,
).add_to(m)

tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}"
folium.raster_layers.TileLayer(
    tiles=tiles,
    name="OceanRef",
    attr=attr,
    overlay=True,
    control=False,
).add_to(m)

# Add asset inventory to map
folium.GeoJson(
    data=asset_inventory_gdf,
    name="Asset Inventory",#.format(name),
    marker=folium.CircleMarker(radius=1, color="green"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["station_long_name"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["station_long_name"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

# Add sensor map to map
folium.GeoJson(
    data=sensor_gdf,
    name="Sensor Map",#.format(name),
    marker=folium.CircleMarker(radius=5, color="red"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["dataset_id"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["dataset_id"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

# Add hfr stations to map
folium.GeoJson(
    data=hfr_gdf,
    name="HFR Map",#.format(name),
    marker=folium.CircleMarker(radius=5, color="blue"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["dataset_id"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["dataset_id"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

## Configure the map
folium.LayerControl(collapsed=True).add_to(m)
m.fit_bounds(m.get_bounds())
m.save("docs/index.html")

