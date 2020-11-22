import datetime
import pandas as pd
import geopandas as geopd


CRASHES_FILENAME = 'Motor_Vehicle_Collisions_-_Crashes.csv'


def convert_column(name):
    return name.lower().replace(' ', '_')


def format_datetime(crash_date, crash_time):
    def func_date(val):
        return list(map(int, val.split('/')))
    def func_time(val):
        return list(map(int, val.split(':')))
    def func_dt(val):
        month, day, year, hour, minute = val
        dt = datetime.datetime(year, month, day, hour=hour, minute=minute)
        return dt.strftime('%Y-%m-%d %H:%M:00')
    crash_date = crash_date.apply(func_date)
    crash_time = crash_time.apply(func_time)
    dt = crash_date + crash_time
    return dt.apply(func_dt)


COLUMNS = [
    'crash_date', 'crash_time', 'number_of_persons_killed',
    'number_of_pedestrians_injured', 'number_of_pedestrians_killed',
    'number_of_cyclist_injured', 'number_of_cyclist_killed',
    'number_of_motorist_injured', 'number_of_motorist_killed',
    'contributing_factor_vehicle_1', 'vehicle_type_code_1']


def create_geofile():
    df = pd.read_csv(CRASHES_FILENAME, header=0, delimiter=',')
    lon, lat = df['LONGITUDE'], df['LATITUDE'] 
    # Rename columns
    col_map = {}
    for col in df.columns:
        col_map[col] = convert_column(col)
    df = df.rename(columns=col_map)
    df = df[COLUMNS]
    # Format datetime
    df['crash_date'] = format_datetime(df['crash_date'], df['crash_time'])
    del df['crash_time']

    gdf = geopd.GeoDataFrame(df, geometry=geopd.points_from_xy(lon, lat))
    gdf = gdf.set_crs('epsg:4326')
    gdf.to_file('crashes.gpkg', layer='crashes', driver='GPKG')


if __name__ == '__main__':
    create_geofile()
