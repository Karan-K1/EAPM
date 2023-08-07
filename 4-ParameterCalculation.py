import pandas as pd
import numpy as np
import os
from src.load_data import split_opf
from src.coeff_bada import ACData, Synonym
from src.fwparser import FixedWidthParser, ParseError
from pathlib import Path
from csv import writer

import pyBADA.constants as cons
import pyBADA.bada3 as b3
import pyBADA.conversions as conv
import pyBADA.atmosphere as atm
import pyBADA.aircraft as ac

def Bisection(func, low, high, ROCD, e):
    """
    Bisection algorithm to converge onto a value of mass
    """
    Step = 1
    
    # Input Section
    print('Low Mass: ', low)
    print('High Mass: ', high)
    print('Tolerable Error: ', e)

    def closest(lst, K):
        return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]

    for i in range(100): # Max interation
        print("")
        if Step == 1:
            Cal_ROCDs = []
            masses = np.linspace(start = low, stop = high, num = 50) 
            for m in masses:
                cal_rocd = func(m)
                Cal_ROCDs.append(cal_rocd)

            closest_value = closest(Cal_ROCDs, ROCD)
            mass = masses[Cal_ROCDs.index(closest_value)]
            print('Iteration-%d, mass = %0.6f and ROCD = %0.6f' % (Step, mass, closest_value))

            if abs(ROCD - closest_value) < float(e):
                print('Iteration complete')
                break
            else:
                new_low = abs(mass - ((high-low)/2))
                print(f"Low: {low}")
                new_high = abs(mass + ((high-low)/2))
                print(f"High: {high}")
                Step = Step + 1
        else:
            low = new_low
            high = new_high
            Cal_ROCDs = []
            masses = np.linspace(start = low, stop = high, num = 50) 
            for m in masses:
                cal_rocd = func(m)
                Cal_ROCDs.append(cal_rocd)

            closest_value = closest(Cal_ROCDs, ROCD)
            mass = masses[Cal_ROCDs.index(closest_value)]
            print('Iteration-%d, mass = %0.6f and ROCD = %0.6f' % (Step, mass, closest_value))

            if abs(ROCD - closest_value) < float(e):
                print('Iteration complete')
                break
            else:
                new_low = abs(mass - ((high-low)/2))
                print(f"Low: {low}")
                new_high = abs(mass + ((high-low)/2))
                print(f"High: {high}")
                Step = Step + 1
    return mass

def mass_calculation(T_atm, H_p, BankAngle, TAS, ROCD, Mach, error):

    """
    This code calculates the mass of an aircraft using the bisection method. This method only accounts for the climb phase. Make sure to keep it in SI units. This calculation needs to know whether the M is constant or the CAS is constant.

    :param T_atm: (K) The temperature of the atmosphere
    :param H_p: (m) This is the Altitude preferably geopotential altitude at which the aircraft is at.
    :param BankAngle: Bank angle usually 30
    :param TAS: (m/s) True Air Speed that the aircraft is travelling at
    :param ROCD: (m/s) Rate Of Climb or Descent
    :param error: Amount of error allowed
    
    :return mass: (kg) Mass of the aircraft
    :return V1: (knots) Calibrated Air Speed
    :return V2: (knots) Calibrated Air Speed
    :return Mach: Mach Number of the Aircraft
    """
    mass_min = A320_data.mass['minimum']
    mass_max = A320_data.mass['maximum']
    dT = (T_atm - (15-(2*H_p/1000*3.28084)) - 273.15) # Calculates Temp in Kelvin after converting altitude to ft
    # dT = (T_atm-(2*15*H0))
    (theta_norm, delta_norm, sigma_norm) = atm.atmosphereProperties(H_p, dT)
    # bankangle  = A320.flightEnvelope.getBankAngle(phase="cl", flightUnit="mil", value="nom")
    LoadFactor = A320.loadFactor(BankAngle)
    
    # print(A320.Thrust(H0, (T_atm-(2*15*H0)), "MCMB"))

    Thrust  = A320.Thrust(H_p, dT, "MCMB") # Normal thrust, in most phases
    # ThrMax  = A320.TMax(H_p, dT, "MCMB") # Thrust max, usually in the climb phase

    def Drag(sigma_norm, mass, TAS, LoadFactor):
        CL      = A320.CL(sigma_norm, mass, TAS, LoadFactor)
        CD      = A320.CD(CL, 'IC')
        # print(f"CL: {CL}, CD: {CD}")
        return A320.D(sigma_norm, TAS, CD)
    
    ESF     = A320.flightEnvelope.esf(flightEvolution = "constCAS", phase = "cl", h = H_p, DeltaTau = dT, v = Mach)

    print(f"dt: {dT}, theta: {theta_norm}, sigma: {sigma_norm}, delta: {delta_norm}, LF: {LoadFactor}, Thrust: {Thrust}, ESF: {ESF}")
    ROCD_func = lambda mass: (A320.ROCD(Thrust, Drag(sigma_norm, mass, TAS, LoadFactor), TAS, mass, ESF, H_p, dT))
    # Parameters to calculate
    mass        = Bisection(ROCD_func, mass_min, mass_max, ROCD, error)
    (CAS)    = A320.ARPM.climbSpeed(theta_norm, delta_norm, mass, H_p, dT)
    # print("--------------------")
    # print(f"* Final Mass: {mass}")
    # print(f"* CAS (V_1, V_2): {CAS}")
    # print("--------------------")
    return mass, CAS

A320_data = b3.Parse()
A320_data.parseAPF("data/BADA/", "A320__")
A320_data.parseOPF("data/BADA/", "A320__")
A320_data.parseGPF("data/BADA/")

A320                   = b3.BADA3(AC = A320_data)
A320.flightEnvelope    = b3.FlightEnvelope(A320_data)
A320.ARPM              = b3.ARPM(A320_data)

if not os.path.exists('data/flight_parameters'):
    os.makedirs('data/flight_parameters')

# Inputs
# NOTE a revision number is included below in case 
num = 4         # <--- Update the identification number
revision = 0    # <--- Update the revision number 
loc_flight = f"data/3-Flights+Met/Met_{num}/"
readpickle = False # <--- Update whether to read a pickle file

print("--Starting parameter calculation--")

with open(f'data/flight_parameters/FP_{num}.csv', 'a', newline='') as f_object: # 
    writer_object = writer(f_object) # Pass the CSV  file object to the writer() function
    # Result - a writer object
    writer_object.writerow(["flightid", "datedepart", "mass", "V1", "mach"]) # Pass the data in the list as an argument into the writerow() function
    f_object.close() # Close the file object

for filename in os.listdir(loc_flight):
    ProcessedFlights = os.listdir(f"data/4-Flights_processed/{num}-{revision}")

    if filename.replace('Met_',"F") in ProcessedFlights:
        continue
    else:
        print(f"Reading {filename}")
        if readpickle == True:
            df_flight = pd.read_pickle(loc_flight+filename.replace('csv', 'pkl'))
        else:
            df_flight = pd.read_csv(loc_flight+filename) 
        mass_values = []
        cas_values  = []
        V1          = []
        V2          = []
        datedepart  = []

        for row in range(len(df_flight)):               # Conversion
            alt = df_flight.iloc[row]['alt']*0.3048     #
            spd = df_flight.iloc[row]['spd']/1.94384    #
            ts  = df_flight.iloc[row]['ts']
            roc = df_flight.iloc[row]['roc']/196.85     #
            mach= df_flight.iloc[row]['mach']
            temp= df_flight.iloc[row]['temp']
            tas = df_flight.iloc[row]['tas']/1.94384    # 

            mass, CAS = mass_calculation(
                H_p         = alt, 
                T_atm       = temp, 
                TAS         = tas, 
                ROCD        = roc, 
                BankAngle   = 0, # Note this is an assumption that bank angle is zero
                Mach        = mach,
                error       = 0.5)

            mass_values.append(mass)
            cas_values.append(CAS)

        for v in cas_values:
            V1.append(v[0])
            # V2.append(v[1])
        df_flight['mass'] = mass_values
        df_flight['V1'] = V1
        # df_flight['V2'] = V2

        # Extra processing goes here
        mass_min = A320_data.mass['minimum']
        mass_max = A320_data.mass['maximum']

        # df_dropped = df_flight[(df_flight['mass'] < mass_max) & (df_flight['mass'] > mass_min)]
        df_dropped  = df_flight
        if len(df_dropped) == 0:
            continue
        else:
            mean_mass   = df_dropped['mass'].mean() 
            mean_V1     = df_dropped['V1'].mean()
            # mean_V2   = df_dropped['V2'].mean()
            mean_mach   = df_dropped['mach'].mean()
            filename    = filename.replace('Met_','F')
            FlightID    = filename.replace('.csv','')
            # for i in df_dropped['ts']:
            #     datedepart.append(conv.unix2date(i)[2:10].replace('-',''))
            datedepart = conv.unix2date(int(df_dropped['ts'][0]))[2:10].replace('-','')

            parameter_list = [FlightID, datedepart, mean_mass, mean_V1, mean_mach]
            
            with open(f'data/flight_parameters/FP_{num}.csv', 'a', newline='') as f_object:
                # Pass the CSV  file object to the writer() function
                writer_object = writer(f_object) # Result - a writer object
                writer_object.writerow(parameter_list)  # Pass the data in the list as an argument into the writerow() function
                
                f_object.close() # Close the file object

            # The two following lines are either to create a csv or a pickle output, you would need to specify the file folder number
            # df_dropped.to_csv(f"data/4-Flights_processed/{num}-{revision}/{filename}") # Create a csv output
            df_dropped.to_pickle(f"data/4-Flights_processed/{num}-{revision}/{filename.replace('csv','pkl')}") # Create a pickle file output