"""Generate data used for clustering.

Created features:
['number_of_persons_injured', 
'number_of_persons_killed', 'number_of_pedestrians_injured',
'number_of_pedestrians_killed', 'number_of_cyclist_injured',
'number_of_cyclist_killed', 'number_of_motorist_injured',
'number_of_motorist_killed', 'factor__driver_inattention_distraction',
'factor__failure_to_yield_right_of_way',
'factor__following_too_closely', 'factor__backing_unsafely',
'factor__other_vehicular', 'factor__fatigued_drowsy',
'factor__turning_improperly', 'factor__passing_or_lane_usage_improper',
'factor__passing_too_closely', 'factor__unsafe_lane_changing',
'factor__traffic_control_disregarded', 'factor__driver_inexperience',
'vehicle__passenger_vehicle', 'vehicle__suv', 'vehicle__sedan',
'vehicle__taxi', 'vehicle__van', 'vehicle__pick_up_truck',
'vehicle__bus', 'vehicle__bicycle', 'vehicle__ambulance',
'vehicle__tractor', 'vehicle__motorcycle', 'hour_0', 'hour_1', 'hour_2',
'hour_3', 'hour_4', 'hour_5', 'hour_6', 'hour_7', 'hour_8', 'hour_9',
'hour_10', 'hour_11', 'hour_12', 'hour_13', 'hour_14', 'hour_15',
'hour_16', 'hour_17', 'hour_18', 'hour_19', 'hour_20', 'hour_21',
'hour_22', 'hour_23', 'monday', 'tuesday', 'wednesday', 'thursday',
'friday', 'saturday', 'sunday', 'is_weekend', 'january', 'february',
'march', 'april', 'may', 'june', 'july', 'august', 'september',
'october', 'november', 'december', 'is_intersection', 'is_not_intersection']
"""

import logging
import pandas as pd
import geopandas as geopd
import datetime

logging.basicConfig(level=logging.INFO)

STREETS_CRASHES_FILENAME = 'streets_with_crashes.gpkg'
OUTPUT_CSV_FILENAME = 'crashes_by_street.csv'

# Ordered by frequency
CONTR_FACTORS = [
    'driver_inattention_distraction',
    'failure_to_yield_right_of_way',
    'following_too_closely',
    'backing_unsafely',
    'other_vehicular',
    'fatigued_drowsy',
    'turning_improperly',
    'passing_or_lane_usage_improper',
    'passing_too_closely',
    'unsafe_lane_changing',
    'traffic_control_disregarded',
    'driver_inexperience'
]
# Ordered by frequency
VEHICLE_TYPES = {
    # <vehicle type>: <vehicle match>  # Example 
    'passenger_vehicle': 'passenger', # PASSENGER VEHICLE
    'suv': 'sport_utility',  # SPORT UTILITY / STATION WAGON
    'sedan': 'sedan',  # Sedan
    'taxi': 'taxi',  # TAXI
    'van': 'van',  # VAN
    'pick_up_truck': 'pick_up_truck',  # PICK-UP TRUCK
    'bus': 'bus',  # BUS
    'bicycle': ['bicycle', 'bike'],  # BICYCLE
    'ambulance':  'ambulance', # AMBULANCE
    'tractor': 'tractor',  # Tractor Truck Diese
    'motorcycle': 'motorcycle',  # Motorcycle
}
WEEKDAY_MAP = {
    0: 'monday',
    1: 'tuesday',
    2: 'wednesday',
    3: 'thursday',
    4: 'friday',
    5: 'saturday',
    6: 'sunday'
}
IS_WEEKEND = [5, 6]
MONTH_MAP = {
    1: 'january',
    2: 'february',
    3: 'march',
    4: 'april',
    5: 'may',
    6: 'june',
    7: 'july',
    8: 'august',
    9: 'september',
    10: 'october',
    11: 'november',
    12: 'december'
}
HIGHWAY_NAMES = [
    'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'motorway',
    'unclassified'
]
REMOVE_COLS = [
    'name', 'highway', 'city', 'index_right', 'crash_date',
    'contributing_factor_vehicle_1', 'vehicle_type_code_1', 'geometry']


def clean_value(name):
    if not name:
        return ''
    chars = [' ', '/', '-']
    name = name.lower().strip()
    for c in chars:
        name = name.replace(c, '_')
    return name


def create_contrib_factors_features(gdf):
    """Create contributing factors features."""
    logging.info('Creating contributing factors features')
    def trans_factor(factor):
        def wrap(val):
            val = clean_value(val)
            return int(val == factor)
        return wrap
    column = 'contributing_factor_vehicle_1'
    for cont_fact in CONTR_FACTORS:
        gdf['factor__' + cont_fact] = gdf[column].transform(
            trans_factor(cont_fact))


def create_vehicle_features(gdf):
    """Create vehicle types features."""
    logging.info('Creating vehicle types features')
    def trans_veh_type(veh_match):
        def wrap(val):
            val = clean_value(val)
            is_match = False
            if isinstance(veh_match, list):
                for m in veh_match:
                    if m in val:
                        is_match = True
                        break
            else:
                is_match = veh_match in val
            return int(is_match)
        return wrap

    for veh_type, veh_match in VEHICLE_TYPES.items():
        gdf['vehicle__' + veh_type] = gdf['vehicle_type_code_1'].transform(
            trans_veh_type(veh_match))


def create_datetime_features(gdf):
    """Create date and time features."""
    logging.info('Creating date and time features')
    gdf['crash_date'] = gdf['crash_date'].transform(
        datetime.datetime.fromisoformat)
    crash_date = gdf['crash_date']
    # Hour
    for i in range(24):
        gdf[f'hour_{i}'] = crash_date.transform(lambda x: int(x.hour == i))
    # Weekday
    for i in range(7):
        wd = WEEKDAY_MAP[i]
        gdf[wd] = crash_date.transform(lambda x: int(x.weekday() == i))
    # Is weekend
    gdf['is_weekend'] = crash_date.transform(
        lambda x: int(x.weekday() in IS_WEEKEND))
    # Month
    for i in range(1, 13):
        month = MONTH_MAP[i]
        gdf[month] = crash_date.transform(lambda x: int(x.month == i))


def create_intersection_feature(gdf):
    """Creates feature if crash happened at intersection 1 or not 0."""
    logging.info('Creating intersection feature')
    is_intersection = gdf['index_right'].duplicated(keep=False)
    gdf['is_intersection'] = is_intersection.transform(int)
    gdf['is_not_intersection'] = is_intersection.transform(lambda x: int(not x))


def aggregate_data(filename):
    # 74 features!
    logging.info('Loading file...')
    gdf = geopd.read_file(filename)
    # Transform columns
    # Remove rows with city missing
    gdf = gdf[gdf['city'] != '']
    gdf.insert(0, 'street_city', gdf['name'] + ', ' + gdf['city'])

    # Creates features
    create_contrib_factors_features(gdf)
    create_vehicle_features(gdf)
    create_datetime_features(gdf)
    create_intersection_feature(gdf)

    # Remove unnecessary columns
    for col in REMOVE_COLS:
        del gdf[col]
    df = pd.DataFrame(gdf)
    df.reset_index()
    df = df.groupby(['street_city']).sum()
    df = df.sort_values(by=['street_city'])
    logging.info('Saving to CSV file: %s', OUTPUT_CSV_FILENAME)
    df.to_csv(OUTPUT_CSV_FILENAME)


def fix_persons_injured():
    # For some reason I didn't extract the field but it can be derived from other columns 
    df = pd.read_csv(OUTPUT_CSV_FILENAME)
    persons_injured = df['number_of_pedestrians_injured'] + df['number_of_cyclist_injured'] + df['number_of_motorist_injured']
    df.insert(1, 'number_of_persons_injured', persons_injured)
    df.to_csv(OUTPUT_CSV_FILENAME, index=False)


def fix_persons_killed():
    # For some reason the column is float, not int
    df = pd.read_csv(OUTPUT_CSV_FILENAME)
    column = 'number_of_persons_killed'
    df[column] = df[column].transform(int)
    df.to_csv(OUTPUT_CSV_FILENAME, index=False)


if __name__ == '__main__':
    aggregate_data(STREETS_CRASHES_FILENAME)
    fix_persons_injured()
    # fix_persons_killed()
