#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract S3 OLCI SNOW processor results from S3 OLCI images
Written by Maxim Lamare
"""
import sys
from pathlib import Path
from argparse import ArgumentParser, ArgumentTypeError
import csv
import pandas as pd
from datetime import datetime
import re
from snappy_funcs import getS3values, getS3bands
import logging

logging.disable(logging.CRITICAL)


def str2bool(instring):
    """Convert string to boolean.

    Converts an input from a given list of possible inputs to the corresponding
     boolean.

    Args:
        instring (str): Input string: has to be in a predefined list.

    Returns:
        (bool): Boolean according to the input string.
    """
    if instring.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif instring.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise ArgumentTypeError("Boolean value expected.")


def natural_keys(text):
    """Sort strings naturally.

    Sort a list of strings in the natural sorting order.

    Args:
        text (str): Input text to be sorted

    Returns:
        (list): list of naturally sorted objects
    """

    def atoi(text):
        return int(text) if text.isdigit() else text

    return [atoi(c) for c in re.split("(\d+)", text)]


def main(
    sat_fold,
    coords_file,
    out_fold,
    pollution,
    delta_pol,
    gains,
    dem_prods,
    recovery,
    sat_platform
):

    logging.disable(logging.CRITICAL)

    """S3 OLCI extract.

    Extract the products generated by the S3 SNOW Processor for all images
    contained in a specified folder at given coordinates, specified in a csv
    file. Note, the images have to be unzipped raw S3 OLCI images. For each
    scene, the data is located in a *.SEN3 folder, in which the
    "xfdumanifest.xml" is stored.

    Args:
        sat_fold (PosixPath): Path to a folder containing S3 OLCI images
        coords_file (PosixPath): Path to a csv containing site coordinates
        out_fold (PosixPath): Path to a folder in which the output will be\
                              written
        pollution (bool): S3 SNOW dirty snow flag
        delta_pol (int): Delta value to consider dirty snow in S3 SNOW
        gains (bool): Consider vicarious calibration gains

    """
    # Initialise band list we will call from s3_band_values.
    band_list = [
        'atmospheric_temperature_profile_pressure_level_1', 
        'atmospheric_temperature_profile_pressure_level_2',
        'atmospheric_temperature_profile_pressure_level_3',
        'atmospheric_temperature_profile_pressure_level_4',
        'atmospheric_temperature_profile_pressure_level_5',
        'atmospheric_temperature_profile_pressure_level_6',
        'atmospheric_temperature_profile_pressure_level_7',
        'atmospheric_temperature_profile_pressure_level_8',
        'atmospheric_temperature_profile_pressure_level_9',
        'atmospheric_temperature_profile_pressure_level_10',
        'atmospheric_temperature_profile_pressure_level_11',
        'atmospheric_temperature_profile_pressure_level_12',
        'atmospheric_temperature_profile_pressure_level_13',
        'atmospheric_temperature_profile_pressure_level_14',
        'atmospheric_temperature_profile_pressure_level_15',
        'atmospheric_temperature_profile_pressure_level_16',
        'atmospheric_temperature_profile_pressure_level_17',
        'atmospheric_temperature_profile_pressure_level_18',
        'atmospheric_temperature_profile_pressure_level_19',
        'atmospheric_temperature_profile_pressure_level_20',
        'atmospheric_temperature_profile_pressure_level_21',
        'atmospheric_temperature_profile_pressure_level_22',
        'atmospheric_temperature_profile_pressure_level_23',
        'atmospheric_temperature_profile_pressure_level_24',
        'atmospheric_temperature_profile_pressure_level_25',
        'horizontal_wind_vector_1',
        'horizontal_wind_vector_2',
        'humidity',
        'sea_level_pressure',
        'total_columnar_water_vapour',
        'total_ozone',        
        ]

    # Initialise the list of coordinates
    coords = []

    # Open the list of coordinates to be processed. (Name, latitude, longitude)
    with open(str(coords_file), "r") as f:
        rdr = csv.reader(f)
        for row in rdr:
            coords.append((row[0], float(row[1]), float(row[2])))

    # Initialise boolean and String to create output .csv file name.
    # There should be a neater way of doing this.
    getOutputName = True
    outputName = ""

    # If the recovery mode is activated, don't process data: skip to data
    # sorting to salvage the coordinates that were saved
    if recovery:
        # List temporary files present in the output folder
        tmp_files = [x.name for x in out_fold.iterdir() if "tmp" in x.name]

        if tmp_files is None:
            raise Exception("No temporary files found!")
        else:
            # Get the sites that have a temporary file to salvage
            selected_coords = []
            for tmp in tmp_files:
                for x in coords:
                    if x[0] == tmp.split("_tmp")[0]:
                        selected_coords.append(x)

            # Overwrite coords variable for later generic processing
            coords = selected_coords

    # If not in recovery mode, then process as normal
    
    else:
        # Set the path of the log file for failed processing
        #output_errorfile = out_fold / "failed_log.txt"

        # Run the extraction from S3 and put results in dataframe
        
        # List folders in the satellite image directory (include all .SEN3 
        # folders that are located in 'sat_fold')
        satfolders = []
        pixcounter = 0
        # changed rglob to glob
        for p in sat_fold.glob("*"):
            if p.as_posix().endswith(".SEN3"):
                pixcounter += 1 
                satfolders.append(p)
        
        print(str(pixcounter) + " .SEN3 folders found in " + str(sat_fold))
        
        # To store results, make a dictionnary with sat_image.name as keys
        image_results = {}
        sat_image_num = 1
        for sat_image in satfolders:

            print("Processing image " + str(sat_image_num) + "/" + str(pixcounter) + ".")
            print(sat_image.name)
            sat_image_num += 1

            # Satellite image's full path
            s3path = sat_image / "xfdumanifest.xml"

            # Extract S3 data for the coordinates contained in the images
            s3_results = getS3values(
                str(s3path),
                coords,
                pollution,
                delta_pol,
                gains,
                dem_prods,
                #output_errorfile,
            )
            
            # If s3_results returns values extract the rest of the values from 
            # s3_band_values
            if len(s3_results) != 0:
                
                s3_band_values = getS3bands(
                    str(s3path),
                    coords,
                    band_list,
                    #output_errorfile,
                    "OLCI",
                    None
                )

                # Get time from the satellite image folder (quicker than
                # reading the xml file)
                sat_date = datetime.strptime(
                    sat_image.name.split("_")[7], "%Y%m%dT%H%M%S"
                )

                main_df = pd.DataFrame()
                # Put the data from the image into a panda dataframe
                for site in s3_results:
                    print(site)
                    alb_df = pd.DataFrame(s3_results[site], index=[sat_date])

                    # Append the name and location
                    alb_df["station"] = site

                    # Append date and time columns
                    alb_df["year"] = int(sat_date.year)
                    alb_df["month"] = int(sat_date.month)
                    alb_df["day"] = int(sat_date.day)
                    alb_df["hour"] = int(sat_date.hour)
                    alb_df["minute"] = int(sat_date.minute)
                    alb_df["second"] = int(sat_date.second)
                    alb_df["dayofyear"] = int(sat_date.timetuple().tm_yday)

                    # Defining output .csv file name.
                    if getOutputName:
                        outputName = str(sat_date.year) + "%02d" % (sat_date.month,) + "%02d" % (sat_date.day,)
                        print("Output filename: " + outputName)
                        getOutputName = False

                    # Append platform ID as numeric value (A=0, B=1)
                    sat_image_platform = sat_image.name[2]
                    if sat_image_platform == 'A':
                        sat_image_platform_num = 0
                    else:
                        sat_image_platform_num = 1
                    alb_df["platform"] = int(sat_image_platform_num)

                    # Add data from s3_band_values
                    for site1 in s3_band_values:
                        if site1 == site:
                            alb_df1 = pd.DataFrame(s3_band_values[site], index=[sat_date])
                            alb_df = pd.concat([alb_df, alb_df1], axis = 1)

                            # Add the image data to the general dataframe
                            main_df = main_df.append(alb_df)

                # try and delete the created objects.
                print("DELETING")
                del s3_results
                del s3_band_values

                # Not 100 on what's going on here.
                image_results[sat_image.name] = main_df
                print("Number of relevant files: " + str(len(image_results)))

                # Save to file to avoid storing in memory
                timeName = "%s_tmp.csv" % sat_image.name
                output_file = out_fold / timeName

                if output_file.is_file():
                    print("This should never be called.")
                    image_results[sat_image.name].to_csv(
                        str(output_file),
                        mode="a",
                        na_rep=-999,
                        header=False,
                        index=False,
                    )
                else:
                    image_results[sat_image.name].to_csv(                    
                        str(output_file),
                        mode="a",
                        na_rep=-999,
                        header=True,
                        index=False,
                    )

    # After having run the process for all the images, reopen the temp files
    # and sort the data correctly and collate into one .csv file named
    # yyyymmdd Year, month, day.

    # Set column order for sorted files
    columns = [
        "station",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "dayofyear",
        "platform",
        #"grain_diameter",
        "snow_specific_area",
        "ndsi",
        "ndbi",
        #"auto_cloud",  #We have processing problems with auto_cloud. Line 606 snappy_funcs.
        "sza",
        "vza",
        "saa",
        "vaa",
        "horizontal_wind_vector_1",
        "horizontal_wind_vector_2",
        "humidity",
        "sea_level_pressure",
        "total_columnar_water_vapour",
        "total_ozone", 
    ]


    # If the S3SNOW DEM plugin is run, add columns to the list
    if dem_prods:
        [
            columns.append(x)
            for x in ["altitude", "slope", "aspect", "elevation_variance"]
        ]

    # Initialise dataframe
    day_dataframe = pd.DataFrame()
    # Boolean so we will only get the column names once.
    first = True

    for sat_image_temp in image_results:
        
        # Recreate temporary .csv file name
        csv_name = "%s_tmp.csv" % sat_image_temp
        incsv = out_fold / csv_name
    
        if incsv.is_file():
            print("temp .csv file being processed.")
            temp_df = pd.read_csv(str(incsv), sep=",")
            # Remove temporary file:
            #incsv.unlink()  
            if first:
                day_dataframe = temp_df
                first = False
            else:
                # This looks and feels wrong. Needs checking and double checking.
                day_dataframe = pd.concat([day_dataframe, temp_df], ignore_index=True)


            
    # Get all rBRR, rTOA and atmos bands and natural sort
    rbrr_columns = [x for x in day_dataframe.columns if "BRR" in x]
    rbrr_columns.sort(key=natural_keys)

    rtoa_columns = [x for x in day_dataframe.columns if "reflectance" in x]
    rtoa_columns.sort(key=natural_keys)

    atmos_columns = [x for x in day_dataframe if "atmospheric" in x]
    atmos_columns.sort(key=natural_keys)

    # Reorder dataframe columns
    day_dataframe = day_dataframe[
        columns
        + rtoa_columns
        + rbrr_columns
        + atmos_columns
    ]

    # Reorder dates
    day_dataframe["dt"] = pd.to_datetime(
        day_dataframe[["year", "month", "day", "hour", "minute", "second"]]
    )
    day_dataframe.set_index("dt", inplace=True)
    day_dataframe.sort_index(inplace=True)

    print()
    print("Output name: " + outputName)

    # Save reordered file
    output_file = out_fold / outputName

    # Save dataframe to the csv file
    day_dataframe.to_csv(
        str(output_file),
        mode="a",
        na_rep=-999,
        header=True,
        index=False,
    )


if __name__ == "__main__":

    # If no arguments, return a help message
    if len(sys.argv) == 1:
        print(
            'No arguments provided. Please run the command: "python %s -h"'
            "for help." % sys.argv[0]
        )
        sys.exit(2)
    else:
        # Parse Arguments from command line
        parser = ArgumentParser(
            description="Import parameters for the complex"
            " terrain algrithm."
        )

        parser.add_argument(
            "-i",
            "--insat",
            metavar="Satellite image repository",
            required=True,
            help="Path to the folder containing the S3 OLCI images to be"
            " processed.",
        )
        parser.add_argument(
            "-c",
            "--coords",
            metavar="Site coordinates",
            required=True,
            help="Path to the input file containing the coordiantes for each"
            " site. Has to be a csv in format: site,lat,lon.",
        )
        parser.add_argument(
            "-o",
            "--output",
            metavar="Output",
            required=True,
            help="Path to the output folder, where the results will be saved.",
        )
        parser.add_argument(
            "-p",
            "--pollution",
            metavar="Consider snow pollution",
            default=False,
            type=str2bool,
            help="Boolean condition: switch the pollution flag on/off in the"
            " S3 SNOW processor.",
        )
        parser.add_argument(
            "-d",
            "--delta_p",
            metavar="Pollution delta",
            type=float,
            default=0.1,
            help="Reflectance delta (compared to theory) threshold to trigger"
            " the snow pollution calculations, when the pollution flag"
            " is on.",
        )
        parser.add_argument(
            "-g",
            "--gains",
            metavar="OLCI gain correction",
            type=str2bool,
            default=False,
            help="Boolean condition: switch the gain corrections on/off in the"
            " S3 SNOW processor.",
        )
        parser.add_argument(
            "-e",
            "--elevation",
            metavar="S3SNOW dem products",
            type=str2bool,
            default=False,
            help="Boolean condition: run the DEM product plugin.",
        )
        parser.add_argument(
            "-r",
            "--recovery",
            metavar="Recovery mode",
            type=str2bool,
            default=False,
            help="Boolean condition: run the recovery mode to salvage data.",
        )
        parser.add_argument(
            "-f",
            "--platform",
            metavar="Sentinel-3 atellite platform",
            required=False,
            default="AB",
            help="Specify the Sentinel-3 platform to include data from."
            "Options are 'A', 'B', or 'AB' (for both platforms).",
        )

        input_args = parser.parse_args()

        # Run main
        main(
            Path(input_args.insat),
            Path(input_args.coords),
            Path(input_args.output),
            input_args.pollution,
            input_args.delta_p,
            input_args.gains,
            input_args.elevation,
            input_args.recovery,
            input_args.platform,
        )
