# WARNING: The script generate a huge file (over 5.4Gb)
import pandas as pd
import geopandas as geopd


STREETS_COLUMNS = ['name', 'highway', 'city', 'geometry']


def load_buffered_streets():
    streets_gdf = geopd.read_file('nyc_streets.gpkg')
    streets_gdf = streets_gdf.to_crs('epsg:3395')  # convert to different crs that understands meters
    streets_gdf['geometry'] = streets_gdf.buffer(10)  # in meters
    streets_gdf = streets_gdf.to_crs('epsg:4326')
    # streets_gdf.to_file('buffered_streets.gpkg', layer='test', driver='GPKG')  # Don't really need to save ?
    return streets_gdf


def create_geojoin_file():
    # buffer1.gpkg is a large file (160Mb) so should be generated
    # streets_gdf = geopd.read_file('buffered_streets.gpkg')  # epsg:4326
    streets_gdf = load_buffered_streets()
    crashes_gdf = geopd.read_file('crashes.gpkg')  # epsg:4326

    # Use only columns relevant for calculations
    streets_gdf = streets_gdf[STREETS_COLUMNS]

    result_gdf = geopd.sjoin(streets_gdf, crashes_gdf)
    columns = list(result_gdf.columns)
    columns.remove('geometry')
    # Remove duplicates
    result_gdf = result_gdf.drop_duplicates(columns, ignore_index=True)
    result_gdf = result_gdf.to_crs('epsg:4326')
    result_gdf.to_file(
        'streets_with_crashes.gpkg', layer='streets_with_crashes',
        driver='GPKG')


if __name__ == '__main__':
    create_geojoin_file()
