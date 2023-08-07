import pandas as pd
import numpy as np
import csv
import os
import datetime

def FindDay(date):
    """
    0 is Sunday and 6 is Saturday 
    """
    day = datetime.datetime.strptime(str(date), '%y%m%d').weekday()
    return day

def label_encode(LE, path, filename):
    """
    Label encodes the flight plan dataframe
    """
    LE["aircraft type"]         = LE["aircraft type"].astype('category').cat.codes
    LE["origin (ADEP)"]         = LE["origin (ADEP)"].astype('category').cat.codes
    LE["destination (ADES)"]    = LE["destination (ADES)"].astype('category').cat.codes
    LE["company"]               = LE["company"].astype('category').cat.codes
    LE["type"]                  = LE["type"].astype('category').cat.codes
    LE["date departure"]        = LE["date departure"].apply(FindDay)
    LE["manualExemptionReason"] = LE["manualExemptionReason"].astype('category').cat.codes
    LE["exemptionReasonType"]   = LE["exemptionReasonType"].astype('category').cat.codes
    LE["most pen reg"]          = LE["most pen reg"].astype('category').cat.codes
    LE["originalFlightDataQuality"]   = LE["originalFlightDataQuality"].astype('category').cat.codes
    LE["flightState"]           = LE["flightState"].astype('category').cat.codes
    LE["sensitiveFlight"]       = LE["sensitiveFlight"].astype('category').cat.codes
    LE.rename(columns = {'date departure':'day'}, inplace = True)
    LE.reset_index(drop=True)
    # LETrainFP = LE.iloc[:-50]
    # LETestFP = LE.iloc[-50:]
    # LETrainFP.to_csv(path_or_buf = path + "Train" + filename + '.csv', index=False, header=True)
    # LETestFP.to_csv(path_or_buf = path + "Test" + filename + '.csv', index=False, header=True)
    LE.to_pickle(path = f"{path}/{filename}.pkl")
    return LE

def date_encode(X, path, filename):
    """
    Label encodes the flight plan dataframe
    """
    X["date departure"] = X['date departure'].apply(FindDay)
    X.rename(columns = {'date departure':'day'}, inplace = True)
    X.reset_index(drop=True)
    X.to_pickle(path = f"{path}{filename}.pkl")
    return X

print('--- Initiating ---')

number = int(input("Enter dataset number:"))
if number not in [2,3,4]:
    raise Exception("Enter a valid number")
revision = int(input("Enter a revision number:"))

if number == 2:
    Flight_Plan_loc = "data/0-FlightPlans/NewFP202205.csv"
elif number == 3 or number == 4:
    Flight_Plan_loc = "data/0-FlightPlans/NewFP202206.csv"
else:
    raise Exception("Oh no, that is not a valid number")

if not os.path.exists(f'data/5-Final/{number}-{revision}'):
    print(f'Creating folder {number}-{revision}')
    os.makedirs(f'data/5-Final/{number}-{revision}')

# Find the relevant flight plans
Flight_Plan     = pd.read_csv(Flight_Plan_loc)
Flight_Record   = pd.read_csv(f"data/flight_record/FR_{number}.csv", index_col='file_number')
Flight_Parameter= pd.read_csv(f"data/flight_parameters/FP_{number}.csv")

FP_filtered_excess = Flight_Plan[0:0]
FP_filtered = Flight_Plan[0:0]
for index, row in Flight_Parameter.iterrows():
    FID         = row['flightid'].replace('F','')   
    datedepart  = row['datedepart']                 
    codes       = Flight_Record.loc[int(FID)]       
    callsign    = codes['callsign']         
    SSR         = codes['icao']
    
    new_row     = Flight_Plan.loc[(Flight_Plan['callsign'] == callsign) & (Flight_Plan['date departure'] == datedepart)]
   
    filled_row = new_row.copy()
    filled_row['cas'] = row['V1']
    filled_row['mach']= row['mach']
    filled_row['mass']= row['mass']

    if len(filled_row) > 1:
        print(f"Length of row: {len(filled_row)}")
        FP_filtered_excess = pd.concat([FP_filtered_excess, filled_row])
    else:
        FP_filtered = pd.concat([FP_filtered, filled_row])

# Output without encoding
# FP_filtered.to_pickle(f"data/5-Final/{number}-{revision}/{number}Fin.pkl")
# FP_filtered_excess.to_pickle(f"data/5-Final/{number}-{revision}/{number}Rev.pkl")

LE = label_encode(LE = FP_filtered, path = f"data/5-Final/{number}-{revision}", filename = f"LE{number}")

print(LE.head())
print('---Process Complete---')