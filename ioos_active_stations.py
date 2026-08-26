#!/usr/bin/env python

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
# These features makes Sensor map an extremely useful tool for quick data explorations but now imagine if you want automate that instead of exploring the Sensor Map interactively? Or if you want to make multiple small modification to your query? It would be very tedious and error prone to try that with the Sensor Map interface. The good news is that we can automate that by querying the ERDDAP server directly.
#
# We can search for datasets reporting wave data in the last 30 days. We can return the unique coordinates for each dataset so we can build a map.


import folium
import geopandas as gpd
import pandas as pd
from erddapy import ERDDAP
from erddapy.core.url import urlopen


## function to collect appropriate CF standard names
def get_cf_std_name():
    url = "https://cfconventions.org/Data/cf-standard-names/current/src/cf-standard-name-table.xml"

    tbl_version = pd.read_xml(url, xpath="./*")["version_number"][0].astype(int)
    df = pd.read_xml(url, xpath="entry")

    std_names = df.loc[
        (
            df["id"].str.contains("sea_surface_wave_")
            | df["id"].str.contains("sea_surface_swell_")
            | df["id"].str.contains("sea_surface_wind_wave_")
        )
    ]

    print(f"CF Standard Name Table: {tbl_version}")

    sensor_map_std_names = pd.read_csv(
        "https://erddap.sensors.ioos.us/erddap/categorize/standard_name/index.csv"
    )

    # filter to only standard names that are in the sensor map erddap
    refine_std_names = sensor_map_std_names.merge(std_names, left_on="Category", right_on="id")

    print(f"Number of appropriate CF Standard Names in Sensor Map: {len(refine_std_names)}")
    print(f"Appropriate CF Standard Names in Sensor Map:\n{refine_std_names['id'].tolist()}")

    return refine_std_names


def get_cdip_stations(std_names):

    server = "https://erddap.sensors.ioos.us/erddap"
    e = ERDDAP(server=server, protocol="tabledap")

    # we know ism datasets are duplicates of cdip datasets.
    search_for = 'cdip -"ism-cencoos" -"ism-secoora" -"ism-caricoos" -"ism-gcoos" -"ism-aoos" -"ism-glos-obs_264"'

    df_dsets_out = pd.DataFrame()
    for std_name in std_names["id"].tolist():
        kw = {
            "min_time": "now-30days",
            "standard_name": std_name,
            "search_for": search_for,
        }

        url = e.get_search_url(response="csv", **kw)

        # test for valid data.
        try:
            df_dsets = pd.read_csv(urlopen(url))

        except Exception as err:
            print(f"No CDIP datasets found for {std_name}: {err}")
            df_dsets = pd.DataFrame()

        df_dsets_out = pd.concat([df_dsets_out, df_dsets])

    dataset_ids = sorted(set(df_dsets_out["Dataset ID"]))

    ## get coords for each station
    e.variables = ["longitude", "latitude"]
    e.constraints = {
        "time>=": "now-30days",
        "time<": "now",
    }
    kw = {"distinct": True}

    cdip_gdf = gpd.GeoDataFrame()
    for dataset_id in dataset_ids:
        e.dataset_id = dataset_id
        try:
            url = e.get_download_url(response="geoJson", **kw)

            gdf = gpd.read_file(urlopen(url))

            gdf = gdf.explode(ignore_index=False)

            gdf["dataset_id"] = dataset_id
            gdf["info_url"] = e.get_info_url(response="html")
            gdf["href"] = [f'<a href="{url}" target="_blank">{url}</a>' for url in gdf["info_url"]]
        except Exception as err:
            gdf = gpd.GeoDataFrame()
            print(f"{dataset_id} no valid data from {server}: {err}")

        cdip_gdf = pd.concat([cdip_gdf, gdf])

    # set crs once, after all stations have been collected
    if not cdip_gdf.empty:
        cdip_gdf.set_crs(epsg=4326, inplace=True)

    return cdip_gdf


def get_ndbc_stations(std_names):

    server = "https://erddap.sensors.ioos.us/erddap"
    e = ERDDAP(server=server, protocol="tabledap")

    # we know ism datasets are duplicates of ndbc datasets.
    search_for = (
        'ndbc -"cdip" -"ism-cencoos" -"ism-secoora" -"ism-aoos" -"ism-glos" -"edu_fit_sipf1"'
    )

    df_dsets_out = pd.DataFrame()
    for std_name in std_names["id"].tolist():
        kw = {
            "min_time": "now-30days",
            "standard_name": std_name,
            "search_for": search_for,
        }

        url = e.get_search_url(response="csv", **kw)
        try:
            df_dsets = pd.read_csv(urlopen(url))

        except Exception as err:
            print(f"No NDBC datasets found for {std_name}: {err}")
            df_dsets = pd.DataFrame()

        df_dsets_out = pd.concat([df_dsets_out, df_dsets])

    dataset_ids = sorted(set(df_dsets_out["Dataset ID"]))

    ## get coords for each station
    e.variables = ["longitude", "latitude"]
    e.constraints = {
        "time>=": "now-30days",
        "time<": "now",
    }
    kw = {"distinct": True}

    ndbc_gdf = gpd.GeoDataFrame()
    for dataset_id in dataset_ids:
        e.dataset_id = dataset_id
        try:
            url = e.get_download_url(response="geoJson", **kw)

            gdf = gpd.read_file(urlopen(url))
            # convert multipoints (erddap geoJson response returns) to points
            gdf = gdf.explode(ignore_index=False)

            gdf["dataset_id"] = dataset_id
            gdf["info_url"] = e.get_info_url(response="html")
            gdf["href"] = [f'<a href="{url}" target="_blank">{url}</a>' for url in gdf["info_url"]]
        except Exception as err:
            gdf = gpd.GeoDataFrame()
            print(f"{dataset_id} no valid data from {server}: {err}")

        ndbc_gdf = pd.concat([ndbc_gdf, gdf])

    # set crs once, after all stations have been collected
    if not ndbc_gdf.empty:
        ndbc_gdf.set_crs(epsg=4326, inplace=True)

    return ndbc_gdf


def get_ra_stations(std_names):

    server = "https://erddap.sensors.ioos.us/erddap"
    e = ERDDAP(server=server, protocol="tabledap")

    # gathering all relevant stations not affiliated with ndbc or cdip.
    # ignore one glider with incorrect cf standard name for su variable.
    search_for = '-"ndbc" -"cdip" -"ioos-gliderdac-SG276-20260630T1502"'

    df_dsets_out = pd.DataFrame()
    for std_name in std_names["id"].tolist():
        kw = {
            "min_time": "now-30days",
            "standard_name": std_name,
            "search_for": search_for,
        }

        url = e.get_search_url(response="csv", **kw)
        try:
            df_dsets = pd.read_csv(urlopen(url))

        except Exception as err:
            print(f"No RA datasets found for {std_name}: {err}")
            df_dsets = pd.DataFrame()

        df_dsets_out = pd.concat([df_dsets_out, df_dsets])

    dataset_ids = sorted(set(df_dsets_out["Dataset ID"]))

    ## get coords for each station
    e.variables = ["longitude", "latitude"]
    e.constraints = {
        "time>=": "now-30days",
        "time<": "now",
    }
    kw = {"distinct": True}

    sensor_gdf = gpd.GeoDataFrame()
    for dataset_id in dataset_ids:
        e.dataset_id = dataset_id
        try:
            url = e.get_download_url(response="geoJson", **kw)

            gdf = gpd.read_file(urlopen(url))
            gdf = gdf.explode(ignore_index=False)
            gdf["dataset_id"] = dataset_id
            gdf["info_url"] = e.get_info_url(response="html")
            gdf["href"] = [f'<a href="{url}" target="_blank">{url}</a>' for url in gdf["info_url"]]
        except Exception as err:
            gdf = gpd.GeoDataFrame()
            print(f"{dataset_id} no valid data from {server}: {err}")

        sensor_gdf = pd.concat([sensor_gdf, gdf])

    # set crs once, after all stations have been collected
    if not sensor_gdf.empty:
        sensor_gdf.set_crs(epsg=4326, inplace=True)

    return sensor_gdf


# Finally, we can make a map of the stations that have reported data in the last 30 days.


# ## Get HF-Radar stations with wave info
def get_hfradar_data():

    server = "https://hfradar.ioos.us/erddap/"
    e = ERDDAP(server=server, protocol="tabledap")

    # skip the UPR_FRDO_hfr_wave dataset because coordinates are incorrect.
    kw = {
        "min_time": "now-30days",
        "search_for": '"Wave data" -"UPR_FRDO_hfr_wave"',
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

    hfr_gdf = gpd.GeoDataFrame()
    for dataset_id in dataset_ids:
        e.dataset_id = dataset_id
        try:
            url = e.get_download_url(response="geoJson", **kw)

            gdf = gpd.read_file(urlopen(url))
            gdf = gdf.explode(ignore_index=False)

            gdf["dataset_id"] = dataset_id
            gdf["info_url"] = e.get_info_url(response="html")
            gdf["href"] = [f'<a href="{url}" target="_blank">{url}</a>' for url in gdf["info_url"]]
        except Exception as err:
            print(f"{dataset_id} no valid data from {server}: {err}")
            gdf = gpd.GeoDataFrame()

        hfr_gdf = pd.concat([hfr_gdf, gdf])

    # set crs once, after all stations have been collected
    if not hfr_gdf.empty:
        hfr_gdf.set_crs(epsg=4326, inplace=True)

    return hfr_gdf


# ## Read in data from CY2025 Asset Inventory
#
# Gather appropriate wave datasets from https://erddap.ioos.us/erddap/tabledap/processed_asset_inventory.html
#
# Wave datasets are defined by `Waves="X"`.


def get_asset_inventory_data():

    server = "https://erddap.ioos.us/erddap/"
    e = ERDDAP(server=server, protocol="tabledap")

    e.constraints = {
        "Year=": "max(Year)",
        "Waves=": "X",
    }

    e.dataset_id = "processed_asset_inventory"
    url = e.get_download_url(response="geoJson")
    asset_inventory_gdf = gpd.read_file(urlopen(url))
    asset_inventory_gdf.set_crs(epsg=4326, inplace=True)
    asset_inventory_gdf["info_url"] = e.get_info_url(response="html")
    asset_inventory_gdf["href"] = [
        f'<a href="{url}" target="_blank">{url}</a>' for url in asset_inventory_gdf["info_url"]
    ]

    return asset_inventory_gdf


## Cross check those standard names with what is actually in sensor map https://erddap.sensors.ioos.us/erddap/categorize/standard_name/index.csv
std_names = get_cf_std_name()

ra_gdf = get_ra_stations(std_names)
ra_gdf["label"] = "RA"

cdip_gdf = get_cdip_stations(std_names)
cdip_gdf["label"] = "CDIP"

ndbc_gdf = get_ndbc_stations(std_names)
ndbc_gdf["label"] = "NDBC"

## Let's do some cleaning of duplicates
gdf_ra_ndbc = pd.concat([ra_gdf, ndbc_gdf])
gdf_ra_ndbc_dups = gdf_ra_ndbc[gdf_ra_ndbc.duplicated(subset="geometry", keep=False)]
ra_ids2remove = gdf_ra_ndbc_dups.loc[
    gdf_ra_ndbc_dups["dataset_id"].str.contains("ism-glos")
    | gdf_ra_ndbc_dups["dataset_id"].str.contains("ism-aoos")
]
ra_gdf = ra_gdf[~ra_gdf["dataset_id"].isin(ra_ids2remove["dataset_id"])]

print(f"RA Stations: {len(ra_gdf)}")
print(f"NDBC Stations: {len(ndbc_gdf)}")
print(f"CDIP Stations: {len(cdip_gdf)}")

hfr_gdf = get_hfradar_data()
print(f"HFRadar Stations: {len(hfr_gdf)}")

asset_inventory_gdf = get_asset_inventory_data()
print(f"Asset Inventory Stations: {len(asset_inventory_gdf)}")

# Now make a map with those layers
## Initialize map
m = folium.Map(
    tiles=None,
    zoom_start=13,
)

## Add base Layers
tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
gh_repo = "https://github.com/ioos/ioos_wave_assets"
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
    name=f"&#128994;Asset Inventory: {len(asset_inventory_gdf)}",
    marker=folium.CircleMarker(radius=1, color="green"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["station_long_name"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["href"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

# Add sensor map to map
folium.GeoJson(
    data=ra_gdf,
    name=f"&#128308;RA Stations: {len(ra_gdf)}",
    marker=folium.CircleMarker(radius=5, color="red"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["dataset_id"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["href"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

# Add sensor map to map
folium.GeoJson(
    data=cdip_gdf,
    name=f"&#128992;CDIP Stations: {len(cdip_gdf)}",
    marker=folium.CircleMarker(radius=5, color="orange"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["dataset_id"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["href"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

# Add sensor map to map
folium.GeoJson(
    data=ndbc_gdf,
    name=f"&#128995;NDBC Stations: {len(ndbc_gdf)}",
    marker=folium.CircleMarker(radius=5, color="purple"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["dataset_id"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["href"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

# Add hfr stations to map
folium.GeoJson(
    data=hfr_gdf,
    name=f"&#128309;HFR: {len(hfr_gdf)}",
    marker=folium.CircleMarker(radius=5, color="blue"),
    tooltip=folium.features.GeoJsonTooltip(
        fields=["dataset_id"],
        aliases=[""],
    ),
    popup=folium.features.GeoJsonPopup(
        fields=["href"],
        aliases=[""],
    ),
    show=True,
).add_to(m)

## Configure the map
folium.LayerControl(collapsed=True).add_to(m)
m.fit_bounds(m.get_bounds())
m.save("docs/index.html")
