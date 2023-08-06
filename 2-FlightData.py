from pyopensky import OpenskyImpalaWrapper
from mpl_toolkits import mplot3d
from matplotlib.lines import Line2D

import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import os
import pickle
import csv

def callsign_flights(DF_Flight):
    """
    Find the callsigns in the flight dataframe and...
    :param DF_Flight: Give a dataframe of flights which have been queried on OpenSky.
    :type DF_Flight: DataFrame
    :return df_dict: Dictionary of flights.
    """
    DF_Flight_callsigns=DF_Flight.callsign.unique().tolist()

    # This is to remove nan values from the array
    callsigns = []
    for callsign in DF_Flight_callsigns:
        if type(callsign) == float:
            continue
        else:
            callsigns.append(callsign)
    
    df_dict = {}
    for callsign in callsigns:
        if DF_Flight.loc[DF_Flight['callsign'] == callsign].shape < (25,17): # If a flight has less than 25 rows then we discard it.
            continue
        elif DF_Flight.loc[DF_Flight['callsign'] == callsign].shape > (25000,17): # If a flight is more than around 1500KB then it has errors. 
            continue
        else:
            df_dict[callsign] = DF_Flight.loc[DF_Flight['callsign'] == callsign]
            
    return df_dict

def flight_extraction(start:datetime = None, end:datetime = None, icao24:str = None, number:int = None, bound: list = None, pickle_file: bool = False):
    """
    Queries the opensky database. Creates all the csv files of the individual flight and creates a flight record to correlate the icao and callsign to the flight number generated.
    
    :param start: Datetime of when the query starts in format "YYYY-MM-DD 00:00:00"
    :param end: Datetime of when the query ends in format "YYYY-MM-DD 00:00:00"
    :param icao24: The ICAO number of the flight to query
    :param number: ID prefix number to give the flights
    :param bound: Latitude and longitude coordinates to query the flights within
    """
    save_folder = "data/1-Flights/"

    # Flight Query
    flight = opensky.query(
        type    = "adsb",
        start   = start,      # In format "YYYY-MM-DD 00:00:00"
        end     = end,        # In format "YYYY-MM-DD 00:00:00"
        icao24  = icao24,
        bound   = bound
    )

    flight = flight.dropna(axis = 0, subset = ['lat', 'lon', 'velocity'])
    df_dict_Flight = callsign_flights(flight)
    record_list = [['file_number', 'icao', 'callsign','datedepart']]

    if not os.path.exists(f'{save_folder}Flights_{number}'):
        os.makedirs(f'{save_folder}Flights_{number}')

    for count,value in enumerate(df_dict_Flight):
        icao_number = df_dict_Flight[value].iloc[0,1]
        datedepart  = int(datetime.datetime.fromtimestamp(int(df_dict_Flight[value].iloc[0,0])).strftime('%Y-%m-%d %H:%M:%S')[0:10].replace('-',''))
        record_list.append([str(number)+str(count), icao_number, value, datedepart])
        if pickle_file == True:
            df_dict_Flight[value].to_pickle(f'{save_folder}Flights_{number}/{number}{count}.pkl')
        else:
            df_dict_Flight[value].to_csv(f'{save_folder}Flights_{number}/{number}{count}.csv', index=False)
        
    
    file = open(f'data/flight_record/FR_{number}.csv', 'w+', newline ='') 
    with file:
        write = csv.writer(file)
        write.writerows(record_list)

print("--- Initialising code ---")
number = int(input("Enter an identification number (this is an arbitrary number to help you track your pre-processing):"))

# The following block 
if number == 2:
    flight_plan_loc = "data/0-FlightPlans/NewFP202205.csv"
elif number == 3 or number == 4:
    flight_plan_loc = "data/0-FlightPlans/NewFP202206.csv"
elif number == 5:
    flight_plan_loc = "data/0-FlightPlans/FP202203.csv"
else:
    raise Exception("Oh no, that is not a valid number")

print("--Starting flight query--")

FP = pd.read_csv(filepath_or_buffer = flight_plan_loc, index_col=False)
# FP = pd.read_csv(filepath_or_buffer = 'data/0-FlightPlans/FP202203.csv', index_col=False)

SSR_Numbers = FP.SSR_CODE.unique().tolist()

# SSR_queries = SSR_Numbers[11:25] # For the flight plans in June 2022, find 11-20 icao numbers in that list and query the database and create a flight record
SSR_queries = SSR_Numbers[0:5] # For the flight plans in March 2022, find 0-5 icao numbers in that list and query the database and create a flight record

opensky = OpenskyImpalaWrapper()
print(f"Querying flights for: {SSR_queries}")

flight_extraction(
    start   = "2022-03-01 00:00:00",
    end     = "2022-03-05 00:00:00",
    icao24  = SSR_queries,
    
    number  = str(number), 
    pickle_file = False
)
print("Query complete")
print("Now run the flights through a flight phase identifier")