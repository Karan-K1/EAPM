import pandas as pd
import os

def read_flight_plan(FP_Loc:str, AC_type:str ):
    """
    Read the DDR2 file and return a flight plan with the listed properties.

    :param FP_loc: File path to the  flight plan
    :param AC_type: The type of aircraft such as Airbus A320 as A320, Boeing 737 as B737

    :return FP: flight plan dataframe
    """
    titles = [
    'origin (ADEP)',
    'destination (ADES)',
    'not used',
    'aircraft type',
    'RFL',
    'zone origin', 
    'zone destin',
    'flight ID',
    'date departure',
    'time departure',
    'time arrival',
    'callsign',
    'company',
    'Seperator1',
    'Universal Unique ID',
    'Fips cloned',
    'Separator2',
    'Flight SAAM ID',
    'Flight SAMAD ID',
    'TACT ID',
    'SSR_CODE',
    'REGISTRATION',
    'Planned Date departure',
    'Planned Time departure',
    'ATFM DELAY',
    'REROUTING STATE',
    'most pen reg',
    'type',
    'equipment',
    'ICAO equipment',
    'COM equipment',
    'SUR equipment',
    'SSR equipment',
    'SURVIVAL equip.',
    'PERSONS ON BOARD',
    'top FL',
    'max RFL',
    'FLT PLN SOURCE',
    'Separator3',
    'aobt',
    'IFPS_ID',
    'iobt',
    'originalFlightDataQuality',
    'flightDataQuality',
    'source',
    'exemptionReasonType',
    'exemptionReasonDistance',
    'lateFiler',
    'lateUpdater',
    'northAtlanticFlight',
    'cobt',
    'eobt',
    'flightState',
    'previousToActivationFlightState',
    'suspensionStatus',
    'tactId',
    'samCtot',
    'samSent',
    'sipCtot',
    'sipSent',
    'slotForced',
    'mostPenalizingRegulationId',
    'regulationsAffectedByNrOfInstances',
    'excludedFromNrOfInstances',
    'lastReceivedAtfmMessageTitle',
    'lastReceivedMessageTitle',
    'lastSentAtfmMessageTitle',
    'manualExemptionReason',
    'sensitiveFlight',
    'readyForImprovement',
    'readyToDepart',
    'revisedTaxiTime',
    'tis',
    'trs',
    'toBeSentSlotMessageTitle',
    'toBeSentProposalMessageTitle',
    'lastSentSlotMessageTitle',
    'lastSentProposalMessageTitle',
    'lastSentSlotMessage',
    'lastSentProposalMessage',
    'flightCountOption',
    'normalFlightTactId',
    'proposalFlightTactId',
    'operatingAircraftOperatorIcaoId',
    'reroutingWhy',
    'reroutedFlightState',
    'runwayVisualRange',
    'ftfmAiracCycleReleaseNumber',
    'ftfmEnvBaselineNumber',
    'rtfmAiracCycleReleaseNumber',
    'rtfmEnvBaselineNumber',
    'ctfmAiracCycleReleaseNumber',
    'ctfmEnvBaselineNumber',
    'lastReceivedProgressMessage',
    'Separator4']

    FP = pd.read_csv(filepath_or_buffer = FP_Loc, sep = ';', names = titles, index_col=False, dtype={'SSR_CODE':'str', 'callsign': 'str'})

    FP = FP[[
        'SSR_CODE',             # Will be dropped
        'callsign',             # Will be dropped
        'date departure',       # Important to find the day later on
        'origin (ADEP)',        # Origin
        'destination (ADES)',   # Destination
        'aircraft type',        # Aircraft Type
        'RFL',                  # Flight Level
        'company',              # Operator
        'type',                 # Flight Type
        'Planned Time departure', # Time Departure
        'sensitiveFlight',
        'flightState', 
        'originalFlightDataQuality', 
        'most pen reg', # Regulations
        'regulationsAffectedByNrOfInstances', # Regulations
        'exemptionReasonType', # Exemption
        'manualExemptionReason'# Exemption
        ]] # Alternative

    FP = FP.loc[(FP['aircraft type'] == AC_type)]
    FP = FP.dropna(axis = 0, subset = ['SSR_CODE', 'callsign'])
    return FP

def concat_flight_plan(FlightPlans, FlightPlanConcat, AC_type: str):
    """
    For a particular aircraft type Concatonate flight plans to a dataframe  

    :param FlightPlans: File path to the  flight plans
    :param FlightPlanConcat: File name path for the concatanated set
    :param AC_type: The type of aircraft such as Airbus A320 as A320, Boeing 737 as B737

    :return FP: flight plan dataframe
    """
    FP = pd.DataFrame()
    for filename in os.listdir(FlightPlans):
        FP_read = read_flight_plan(FlightPlans+filename, AC_type)
        FP =pd.concat([FP,FP_read])
    FP.to_csv(path_or_buf = FlightPlanConcat, index=False, header=True)
    return FP

if not os.path.exists('data/0-FlightPlans'):
    os.makedirs('data/0-FlightPlans')

# Create the flight plan csv file from EUROCONTROLs DDR2 dataset

print("--Creating the Flight Plan file--")
folder_year = str(input("Enter folder year (in format YYYYMM) of the DDR2 to read:"))
FP_csv = str(input("Enter the generated flight plan csv filename (e.g. FP202205):"))
AC_type = str(input("Enter aircraft type (currently code only works for A320):"))
FlightPlan = concat_flight_plan("data/DDR2/" + folder_year + "/","data/0-FlightPlans/"+FP_csv+".csv", AC_type)
