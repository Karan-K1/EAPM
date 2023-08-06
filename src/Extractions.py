from pyopensky import OpenskyImpalaWrapper, EHSHelper
import pandas as pd
import numpy as np

opensky = OpenskyImpalaWrapper()
ehs = EHSHelper()

def callsign_flights(DF_Flight):
    DF_Flight_callsigns=DF_Flight.callsign.unique().tolist()

    # This is to remove nan values from the array
    callsigns = []
    for callsign in DF_Flight_callsigns:
        if type(callsign) == float:
            continue
        else:
            callsigns.append(callsign)
    print(callsigns)

    df_dict = {
        callsign: DF_Flight.loc[DF_Flight['callsign'] == callsign]
        for callsign in callsigns
    }
    
    return df_dict

def modeS(icaos, df_radar, df_modeS):
    """
    returns a dataframe which has found the corresponding TAS and mach speeds
    :param icaos: list of icaos to obtain data for
    :param df_radar: a dataframe of the track data
    :param df_modeS: a dataframe of the mode-S data
    :return: dataframe with the added TAS and Mach speeds
    """
    # Create new column fields
    df_radar['mach'] = np.NAN
    df_radar['tas'] = np.NAN
    df_radar['temp'] = np.NAN

    # Change times to integers
    df_modeS['time'] = df_modeS['time'].astype(int)

    iteration = 1
    for i in icaos:
        df_times_TAS = df_modeS.loc[(df_modeS['icao24'] == i) & (df_modeS['bds'] == 'BDS50')].time.unique()
        df_times_Mach = df_modeS.loc[(df_modeS['icao24'] == i) & (df_modeS['bds'] == 'BDS60')].time.unique()

        for j in df_times_TAS:
            print("TAS Iteration:", iteration,"with flight =", i," and Time =", j)
            TAS = df_modeS.loc[(df_modeS['time'] == j)  & (df_modeS['icao24'] == i), 'tas50'].dropna().values[0]
            df_radar.loc[(df_radar['time'] == j) & (df_radar['icao24'] == i), 'tas'] = TAS

            # iteration += 1

        for k in df_times_Mach:
            print("Mach Iteration:", iteration,"with flight =", i," and Time =", k)
            MACH = df_modeS.loc[(df_modeS['time'] == k) & (df_modeS['icao24'] == i), 'mach60'].dropna().values[0]
            df_radar.loc[(df_radar['time'] == k) & (df_radar['icao24'] == i), 'mach'] = MACH

            # iteration += 1
            
    df_radar['temp'] = 0.00249226*((df_radar['tas']**2)/(df_radar['mach']**2))

    return df_radar

def flight_extraction(start, end, icao24, number, bound):
    

    # Flight Query
    flight = opensky.query(
        type    = "adsb",
        start   = start,    # In format "YYYY-MM-DD 00:00:00"
        end     = end,        # In format "YYYY-MM-DD 00:00:00"
        icao24  = icao24,
        bound   = bound
    )

    # Mode-S Query
    ehs.require_bds(["BDS50", "BDS60"])

    ModeS = ehs.get(
        icao24  = icao24,
        start   = start,
        end     = end,
    )
    
    flight = modeS(icao24, flight, ModeS)
    flight = flight.dropna(axis = 0, subset = ['lat', 'lon', 'velocity'])
    
    df_dict_Flight = callsign_flights(flight)

    for count,value in enumerate(df_dict_Flight):
        df_dict_Flight[value].to_csv(csv_loc+number+str(count)+'.csv', index=False)