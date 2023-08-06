from pyopensky import EHSHelper
from time import mktime
import datetime
import pandas as pd
# import numpy as np
import os


def correlate_flights(number, readpickle:bool = False):
    if readpickle == True:
        FPI = pd.read_pickle(f"data/flight_phase_identified/FPI_{number}.pkl")
    else:
        FPI = pd.read_csv(f"data/flight_phase_identified/FPI_{number}.csv")
    FR = pd.read_csv(f"data/flight_record/FR_{number}.csv", index_col='file_number')
    FPI_climb = FPI.loc[FPI['prediction'] == 'climb']
    flight_ids = FPI_climb['flight_id'].unique()

    return FPI, FR, FPI_climb, flight_ids

def create_met_data(FR, FPI_climb, flight_ids, Number: int, readpickle:bool = False):

    if not os.path.exists(f'data/2-ModeS/ModeS_{Number}'):
        os.makedirs(f'data/2-ModeS/ModeS_{Number}')

    print("--Starting Met Data Retrieval--")
    ehs = EHSHelper()
    errors = []
    Completed_ModeS = [int(i.replace('ModeS_','').replace('.csv','')) for i in os.listdir(f"data/2-ModeS/ModeS_{Number}")]

    for id in flight_ids:
        if id in Completed_ModeS:
            continue
        else:
            print(f"Retrieving Met Data: {id}")
            icao_0 = FR.loc[id]['icao']
            FPI_climb_query = FPI_climb.loc[FPI_climb['flight_id'] == id]
            start = datetime.datetime.fromtimestamp(FPI_climb_query['ts'].min()-3600) #"2022-04-30 05:44:08"
            end =  datetime.datetime.fromtimestamp(FPI_climb_query['ts'].max()+3600) #"2022-04-30 05:58:32"
            
            ehs.require_bds(["BDS50", "BDS60"])
            ModeS_0 = ehs.get(icao24 =icao_0, start = start, end = end)
            try:
                if readpickle == True:
                    ModeS_0.to_pickle(path_or_buf = f'data/2-ModeS/ModeS_{Number}/ModeS_{id}.pkl')
                else:
                    ModeS_0.to_csv(path_or_buf = f'data/2-ModeS/ModeS_{Number}/ModeS_{id}.csv')
            except:
                errors.append(id)
                print("Encountered an error, no available Mode-S Messages")

    print(f'Flights which failed: {errors}')
    return errors

def add_met_data(FPI_climb, Number, readpickle:bool = False):
    print("--Adding met data--")
    ModeS_list = os.listdir(f"data/2-ModeS/ModeS_{Number}")
    PostFlightsMet = os.listdir(f"data/3-Flights+Met/Met_{Number}")
    print('--Initiated--')

    if not os.path.exists(f'data/3-Flights+Met/Met_{Number}'):
        os.makedirs(f'data/3-Flights+Met/Met_{Number}')

    for FlightID in ModeS_list:

        ID = FlightID.replace('.csv','')
        ID = int(ID.replace('ModeS_',''))
        if FlightID.replace('ModeS','Met') in PostFlightsMet:
            continue
        else:
            print("Flight ID:", ID)
            
            df_radar = FPI_climb.loc[FPI_climb['flight_id'] == ID]
            if readpickle == True:
                df_modeS = pd.read_pickle(f'data/2-ModeS/ModeS_{Number}/ModeS_{ID}.pkl')
            else:
                df_modeS = pd.read_csv(f'data/2-ModeS/ModeS_{Number}/ModeS_{ID}.csv')
            
            df_radar.is_copy = False
            df_modeS['time'] = df_modeS['time'].astype(int) # Change time to integers

            # Get times
            df_times_TAS = df_modeS.dropna(axis = 0, subset=['tas50']).time
            df_times_Mach = df_modeS.dropna(axis = 0, subset=['mach60']).time
            df_times = list(set(df_times_TAS) & set(df_times_Mach))

            if len(df_times) == 0:
                continue
            else:
                print('Filling out values...')
                for t in df_times:
                    TAS = df_modeS.loc[(df_modeS['time'] == t) & (df_modeS['bds'] == 'BDS50'), 'tas50']
                    df_radar.loc[df_radar['ts'] == t, 'tas'] = TAS.values[0]
                    MACH = df_modeS.loc[(df_modeS['time'] == t) & (df_modeS['bds'] == 'BDS60'), 'mach60']
                    df_radar.loc[df_radar['ts'] == t, 'mach'] = MACH.values[0]

                df_radar['temp'] = (288.15/(661.478**2))*((df_radar['tas']**2)/(df_radar['mach']**2))
                df_radar = df_radar.dropna(axis = 0, subset=['tas', 'mach'])
                if readpickle == True:
                    df_radar.to_pickle(f"data/3-Flights+Met/Met_{Number}/Met_{ID}.pkl")
                else:
                    df_radar.to_csv(f"data/3-Flights+Met/Met_{Number}/Met_{ID}.csv")

num = 5              # Update the identification number
pickle_file = False  # Specify whether the flight track data is a pickle file or not

(FPI, FR, FPI_climb, flight_ids) = correlate_flights(num, readpickle=pickle_file)
errors2 = create_met_data(FR, FPI_climb, flight_ids, num, readpickle=pickle_file)
add_met_data(FPI_climb, num, readpickle = True)

print(f"Flights which failed: {errors2}")
print("--- Process complete ---")