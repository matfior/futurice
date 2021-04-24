
#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

"""
where_next, a simple python script to make informed decisions
free for non-commercial use
"""

from pyjstat import pyjstat
from datetime import datetime
import requests
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl

__author__ = 'Matteo Fiorillo'
__license__ = 'free for non-commercial use'
__version__ = '0.0.1'
__email__ = 'matteo.fiorillo@gmail.com'
__status__ = 'beta'

ICT_SIZE_URL = 'http://ec.europa.eu/eurostat/wdds/rest/data/v2.1/json/en/tin00074?nace_r2=ICT'
CLOUD_SERVICES_URL = 'http://ec.europa.eu/eurostat/wdds/rest/data/v2.1/json/en/isoc_cicce_use?sizen_r2=M_C10_S951_XK&sizen_r2=L_C10_S951_XK&unit=PC_ENT&indic_is=E_CC'
GDP_DATA_FILE = 'gdp_data.csv'
FILLER = 1

# Function to display dataframes nicely and entirely
def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

# This creates a timestamped filename so we don't overwrite our good work
def timeStamped(fname, fmt='%Y-%m-%d-%H-%M-%S-{fname}'):
    return datetime.now().strftime(fmt).format(fname=fname)

def ict_cloud():
    # Pull json data about the size of ICT sector in the country and convert it to dataframe
    ict = pyjstat.Dataset.read(ICT_SIZE_URL)
    ict_df = ict.write('dataframe')

    # Pull json data about the amount of cloud services used in country’s enterprises and convert it to dataframe
    cloud = pyjstat.Dataset.read(CLOUD_SERVICES_URL)
    cloud_df = cloud.write('dataframe')

    # Drop unnecessary columns and fill missing values
    ict_df = ict_df[["geo","time","value"]]
    ict_df = ict_df.fillna(FILLER)

    # We also need to aggregate (sum) values for cloud data since we want the overall values
    cloud_df = cloud_df[["geo","time","value"]]
    cloud_df = cloud_df.groupby(['geo','time']).sum()
    cloud_df = cloud_df.fillna(FILLER)

    # Merge the datasets (join based on year and country)
    ict_cloud_data = pd.merge(ict_df, cloud_df, left_on=['geo','time'], right_on = ['geo','time'])
    ict_cloud_data = ict_cloud_data.rename(columns={"value_x": "ict", "value_y": "cloud"})

    # Replace zeros with ones since we want to retain some information
    ict_cloud_data = ict_cloud_data.replace(0, 1)
    return ict_cloud_data

def gdp():
    # Import gdp data from provided CSV file
    gdp_data_df = pd.read_csv (GDP_DATA_FILE,delimiter='|')

    # Remove lines for countries that already have offices
    gdp_data_df = gdp_data_df[~gdp_data_df['2008'].str.contains("Office", na=False)]

    # Pivot dataframe to make the merge possible, rename columns and sort data
    gdp_data_df = gdp_data_df.melt(['Country'], var_name='time')
    gdp_data_df = gdp_data_df.rename(columns={"value": "gdp", "Country": "geo"})
    gdp_data_df = gdp_data_df.sort_values(by=['geo', 'time'])

    # To use gdp data we need to replace commas with dots and cast as float. We also fill missing values with ones
    gdp_data_df['gdp'] = gdp_data_df['gdp'].str.replace(',','.')
    gdp_data_df['gdp'] = gdp_data_df['gdp'].astype(float)
    gdp_data = gdp_data_df.fillna(1)

    return gdp_data

def attract():
    # Merge the two above dataframes (ict&cloud data, gdp data)
    attract_data = pd.merge(ict_cloud_data, gdp_data, left_on=['geo','time'], right_on = ['geo','time'])

    # Calculate attractiveness based on the supplied formula (GDP * percentage of ICT sector from GDP * usage of cloud computing in enterprises in a country)
    attract_data['attract'] = attract_data['ict'] * attract_data['cloud'] * attract_data['gdp']

    # Drop other columns
    attract_data = attract_data[["geo","time","attract"]]

    # Sort by attractiveness and year, desc 
    attract_data = attract_data.sort_values(by=['time','attract'], ascending=False)

    return attract_data

def print_results():
    # Finally, print a subset of the results
    year = attract_data["time"]
    max_year = year.max()
    attract_selection = attract_data[attract_data['time'].str.contains(max_year, na=False)]
    print_full(attract_selection)

    return attract_selection

def results_to_excel():
    # Export to excel
    attract_selection.to_excel(timeStamped('attractiveness.xlsx'))

ict_cloud_data = ict_cloud()
gdp_data = gdp()
attract_data = attract()
attract_selection = print_results()
results_to_excel()