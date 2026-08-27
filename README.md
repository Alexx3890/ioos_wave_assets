# ioos_wave_assets
A dynamic map of IOOS stations reporting wave data collected from the IOOS Sensor Map ERDDAP. https://erddap.sensors.ioos.us/erddap/index.html

## Sensor map queries
At the end here is my search criteria for each of the sensor map queries:

[CDIP](https://erddap.sensors.ioos.us/erddap/search/advanced.html?page=1&itemsPerPage=1000&searchFor=cdip+-%22ism-cencoos%22+-%22ism-secoora%22+-%22ism-caricoos%22+-%22ism-gcoos%22+-%22ism-aoos%22+-%22ism-glos-obs_264%22&protocol=%28ANY%29&cdm_data_type=%28ANY%29&institution=%28ANY%29&ioos_category=%28ANY%29&keywords=%28ANY%29&long_name=%28ANY%29&standard_name=sea_surface_wave_significant_height&variableName=%28ANY%29&maxLat=&minLon=&maxLon=&minLat=&minTime=now-30days&maxTime=): `cdip -"ism-cencoos" -"ism-secoora" -"ism-caricoos" -"ism-gcoos" -"ism-aoos" -"ism-glos-obs_264"`

[NDBC](https://erddap.sensors.ioos.us/erddap/search/advanced.html?page=1&itemsPerPage=1000&searchFor=ndbc+-%22cdip%22+-%22ism-cencoos%22+-%22ism-secoora%22+-%22ism-aoos%22+-%22ism-glos%22+-%22edu_fit_sipf1%22&protocol=%28ANY%29&cdm_data_type=%28ANY%29&institution=%28ANY%29&ioos_category=%28ANY%29&keywords=%28ANY%29&long_name=%28ANY%29&standard_name=sea_surface_wave_significant_height&variableName=%28ANY%29&maxLat=&minLon=&maxLon=&minLat=&minTime=now-30days&maxTime=): `ndbc -"cdip" -"ism-cencoos" -"ism-secoora" -"ism-aoos" -"ism-glos" -"edu_fit_sipf1"`

[RA](https://erddap.sensors.ioos.us/erddap/search/advanced.html?page=1&itemsPerPage=1000&searchFor=-%22ndbc%22+-%22cdip%22+-%22ioos-gliderdac-SG276-20260630T1502%22&protocol=%28ANY%29&cdm_data_type=%28ANY%29&institution=%28ANY%29&ioos_category=%28ANY%29&keywords=%28ANY%29&long_name=%28ANY%29&standard_name=sea_surface_wave_significant_height&variableName=%28ANY%29&maxLat=&minLon=&maxLon=&minLat=&minTime=now-30days&maxTime=): `-"ndbc" -"cdip" -"ioos-gliderdac-SG276-20260630T1502"`

For each of those groupings we search for relevant CF standard names:

```
['sea_surface_swell_wave_from_direction', 'sea_surface_swell_wave_period', 'sea_surface_swell_wave_significant_height', 'sea_surface_wave_directional_spread', 'sea_surface_wave_directional_spread_at_variance_spectral_density_maximum', 'sea_surface_wave_from_direction', 'sea_surface_wave_from_direction_at_variance_spectral_density_maximum', 'sea_surface_wave_maximum_height', 'sea_surface_wave_maximum_period', 'sea_surface_wave_mean_height', 'sea_surface_wave_mean_height_of_highest_tenth', 'sea_surface_wave_mean_period', 'sea_surface_wave_period_at_variance_spectral_density_maximum', 'sea_surface_wave_significant_height', 'sea_surface_wave_significant_period', 'sea_surface_wave_to_direction', 'sea_surface_wind_wave_from_direction', 'sea_surface_wind_wave_period', 'sea_surface_wind_wave_significant_height']
```

and limit to the datasets that have reported data in the last month

```
"min_time": "now-30days"
```

We had to make executive decisions on where to classify some glos and aoos stations as it isn't clear if they should be RA or NDBC stations. At the end of the day, I assigned them to NDBC. There was a total of 15 stations matching this criteria.

## Asset Inventory
This is a relatively simple query to an ERDDAP dataset:
https://erddap.ioos.us/erddap/tabledap/processed_asset_inventory.htmlTable?Year%2CRA%2Clatitude%2Clongitude%2Cstation_long_name%2CPlatform%2COperational%2Cstation_deployment%2CRA_Funded%2CWater_temp%2CSalinity%2CWtr_press%2CDew_pt%2CRel_hum%2CAir_temp%2CWinds%2CAir_press%2CPrecip%2CSolar_radn%2CVisibility%2CWater_level%2CWaves%2CCurrents%2CTurbidity%2CDO%2CpCO2_water%2CpCO2_air%2CTCO2%2CpH%2COmgArag_st%2CChl%2CNitrate%2CCDOM%2CAlkalinity%2CAcoustics%2CRaw_Vars%2Ccrs&Year=max(Year)&Waves=%22X%22

## HFRadar
Search through hfradar.ioos.us/erddap for
```"Wave data" -"UPR_FRDO_hfr_wave"```
We skip UPR because the coordinates are bogus.


## Known caveats
* This is all dependent on the sensor map and the frequency at which it is pulling new data in. It pulls in new data every 15 minutes, but new metadata every day, so there is a +/- to the dataset count each day.
* There could be duplicates in the RA, NDBC, and CDIP layers. I've tried to catch all the edge cases, but there could be more.
* This represents the last **month** of **wave** observations from the sensor map and HFRnet. 
* The Asset Inventory layer is self reported every calendar year. So, we are presenting the most recent calendar year wave assets. There are expected duplicates with what is in the sensor map. That is okay.
* Sensor map might not capture all of the stations from CDIP, NDBC, and RAs. So, these numbers should be used as rough approximations.
* The script to generate the map and metrics is either run monthly or on-demand. Check revision history for when the last data capture was run.
