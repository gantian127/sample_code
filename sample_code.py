"""
This is to count pixel numbers of multiple types in the binary snow cover maps.

Steps:
- default settings to define existing tif file folders and other info
- get binary snow cover maps from tif files and calculate pixel count
  a) initiate data frame to store pixel count results
  b) calculate pixel count in binary snow cover maps based on MODIS observation
  c) calculate pixel count in binary snow cover maps based on simulation SWE from SNOW-17 or UEB model
  d) compare binary snow cover maps from simulation and MODIS observation and calculate 4 types of pixel count
- save the data frame as a csv file

"""

import os

import gdalnumeric
import pandas as pd
import numpy as np


# default settings  ####################################################
# existing folders/files
valid_snow_date_path = os.path.join(os.getcwd(), 'valid_snow_date.csv')
modis_tif_folder = os.path.join(os.getcwd(), 'modis_tif_folder')
swe_tif_folders = [os.path.join(os.getcwd(), name) for name in ['snow17_tif_folder', 'ueb_tif_folder']]

# time for data processing
start_time = '2000/10/01'
end_time = '2010/06/30'


# get binary snow cover map and calculate pixel count ############################
# load valid data record
snow_date = pd.DataFrame.from_csv(valid_snow_date_path, header=0)

# define column names for a new data frame to store results
df_col_name = ['modis_snow', 'modis_dry', 'swe_snow', 'swe_dry', 'A', 'B', 'C', 'D']

for swe_tif_folder in swe_tif_folders:
    swe_col_name = os.path.basename(swe_tif_folder)

    if os.path.isdir(swe_tif_folder) and os.path.isdir(modis_tif_folder):
        # initiate data frame and csv file path to store pixel count results
        pixel_count = pd.DataFrame(index=snow_date.index, columns=df_col_name)
        pixel_count_path = os.path.join(os.getcwd(), 'pixel_count_{}.csv'.format(swe_col_name.split('_')[0]))

        # calculate pixel count
        for time in snow_date.index:
            modis_tif_path = os.path.join(modis_tif_folder, snow_date['modis_tif_folder'].ix[time])
            swe_tif_path = os.path.join(swe_tif_folder, snow_date[swe_col_name].ix[time])

            if os.path.isfile(swe_tif_path) and os.path.isfile(modis_tif_path):
                try:
                    # get MODIS binary snow cover map
                    modis = gdalnumeric.LoadFile(modis_tif_path)
                    modis_bin = np.where(modis[1] != 0, modis[0], -999)
                    modis_bin[modis_bin > 100] = -999
                    modis_bin[modis_bin > 0] = 1

                    # count MODIS snow and dry pixels
                    count_modis_snow = (modis_bin == 1).sum()
                    count_modis_dry = (modis_bin == 0).sum()

                    # get simulation binary snow cover map
                    swe = gdalnumeric.LoadFile(swe_tif_path)
                    swe_bin = np.where(modis_bin != -999, swe, -999)
                    swe_bin[swe_bin >= 1] = 1
                    swe_bin[(swe_bin >= 0) & (swe_bin < 1)] = 0

                    # count swe snow and dry pixels
                    count_swe_snow = (swe_bin == 1).sum()
                    count_swe_dry = (swe_bin == 0).sum()

                    # compare simulation and MODIS binary snow cover maps to get pixel count
                    # for 4 types: A(dry,dry), B(dry,snow), C(snow,dry), D(snow,snow)
                    compare_ab = np.where(swe_bin == 0, modis_bin, 999)
                    compare_cd = np.where(swe_bin == 1, modis_bin, 999)
                    a = (compare_ab == 0).sum()
                    b = (compare_ab == 1).sum()
                    c = (compare_cd == 0).sum()
                    d = (compare_cd == 1).sum()

                    # store pixel count to data frame
                    pixel_count.at[time, df_col_name] = [
                        count_modis_snow, count_modis_dry, count_swe_snow, count_swe_dry,
                        a, b, c, d,
                    ]

                except Exception as e:
                    pixel_count.drop(index=time, inplace=True)
                    print 'Failed to calculate pixel count at {}'.format(time)
                    continue
            else:
                pixel_count.drop(index=time, inplace=True)
                print 'Invalid tif file path at {}'.format(time)

        pixel_count.to_csv(pixel_count_path)
    else:
        print 'Missing tif file folder'

print 'Pixel count calculation is finished'
