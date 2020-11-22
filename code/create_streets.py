
"""
% ogr2ogr -f GPKG nyc.gpkg new-york-latest.osm.pbf -spat -74.309432 40.518589 -73.667336 40.988810

Workflow:
new-york-latest.osm.pbf ->  (ogr2ogr with bounding box)
    nyc.gpkg -> (manual extraction of linear polygons)
        nyc_streets_raw.gpkg -> (create_streets.py)
            nyc_streets.gpkg
"""

import csv
import geopandas as geopd

HIGHWAY_NAMES = [
    'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'motorway', 'unclassified']
TAG_COUNTY = 'tiger:county'


def clean_county(name):
    return name.replace(' ', '').replace(',', '')


def extract_cities(tags):
    cities = []
    for tag_str in tags:
        city = ''
        if tag_str and TAG_COUNTY in tag_str:
            for tag in tag_str.split('",'):
                tag_key, tag_val = tag.split('=>')
                if TAG_COUNTY not in tag_key:
                    continue 
                city = tag_val[1:]
        cities.append(city)
    return cities


def create_streets():
    # Using geopandas
    streets_gdf = geopd.read_file('nyc_streets_raw.gpkg')
    print(streets_gdf.shape)  # 71983
    # Add index to filter by highway
    streets_gdf.index = streets_gdf['highway']
    # We are only interested in these road types
    streets_gdf = streets_gdf.loc[HIGHWAY_NAMES]  # count=59475
    streets_gdf['city'] = extract_cities(streets_gdf['other_tags'])
    # Order by (name, city)
    streets_gdf = streets_gdf.sort_values(by=['name', 'city'])
    streets_gdf.reset_index(drop=True, inplace=True)
    print(streets_gdf.shape)
    print(streets_gdf.head())
    streets_gdf = streets_gdf.set_crs('epsg:4326')
    streets_gdf.to_file('nyc_streets.gpkg', layer='nyc_streets', driver='GPKG')


if __name__ == '__main__':
    create_streets()
