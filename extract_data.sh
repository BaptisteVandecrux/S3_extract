mkdir out

for d in /media/jeb/ice/Sentinel-3/_zip/*/ ; do
    echo "                                      "
    echo "==========================================="
    echo "$d"
    echo "==========================================="
    if [ -d "out/$(basename $d)" ]; then
  	echo "  "
	echo "folder exists, skipping"
	echo "   "
	continue
    fi
    mkdir out/$(basename $d)
    mkdir out/$(basename $d)/out1
    mkdir out/$(basename $d)/out2
    
    python s3_band_extract.py -i "$d" -c "AWS.csv" -o "out/$(basename $d)/out1" -b Oa01_radiance Oa02_radiance Oa03_radiance Oa04_radiance Oa05_radiance Oa06_radiance Oa07_radiance Oa08_radiance Oa09_radiance Oa10_radiance Oa11_radiance Oa12_radiance Oa13_radiance Oa14_radiance Oa15_radiance Oa16_radiance Oa17_radiance Oa18_radiance Oa19_radiance Oa20_radiance Oa21_radiance  altitude latitude longitude solar_flux_band_1 solar_flux_band_2 solar_flux_band_3 solar_flux_band_4 solar_flux_band_5 solar_flux_band_6 solar_flux_band_7 solar_flux_band_8 solar_flux_band_9 solar_flux_band_10 solar_flux_band_11 solar_flux_band_12 solar_flux_band_13 solar_flux_band_14 solar_flux_band_15 solar_flux_band_16 solar_flux_band_17 solar_flux_band_18 solar_flux_band_19 solar_flux_band_20 solar_flux_band_21 OAA OZA SAA SZA atmospheric_temperature_profile_pressure_level_1 atmospheric_temperature_profile_pressure_level_2 atmospheric_temperature_profile_pressure_level_3  atmospheric_temperature_profile_pressure_level_4 atmospheric_temperature_profile_pressure_level_5 atmospheric_temperature_profile_pressure_level_6 atmospheric_temperature_profile_pressure_level_7 atmospheric_temperature_profile_pressure_level_8 atmospheric_temperature_profile_pressure_level_9 atmospheric_temperature_profile_pressure_level_10 atmospheric_temperature_profile_pressure_level_11 atmospheric_temperature_profile_pressure_level_12 atmospheric_temperature_profile_pressure_level_13 atmospheric_temperature_profile_pressure_level_14 atmospheric_temperature_profile_pressure_level_15 atmospheric_temperature_profile_pressure_level_16 atmospheric_temperature_profile_pressure_level_17 atmospheric_temperature_profile_pressure_level_18 atmospheric_temperature_profile_pressure_level_19 atmospheric_temperature_profile_pressure_level_20 atmospheric_temperature_profile_pressure_level_21 atmospheric_temperature_profile_pressure_level_22 atmospheric_temperature_profile_pressure_level_23 atmospheric_temperature_profile_pressure_level_24 atmospheric_temperature_profile_pressure_level_25 horizontal_wind_vector_1 horizontal_wind_vector_2 humidity sea_level_pressure total_columnar_water_vapour total_ozone
 
    python s3_extract_snow_products.py -i "$d" -c "AWS.csv" -o "out/$(basename $d)/out2" -p false -d 0.05 -g false -e yes
done
