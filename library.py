# coding=utf-8
import json
from pathlib import Path

LIBRARY_VERSION = 'osm_2022'

def read_tags():
    ''' Read tags '''
    # read json file
    # tags = {'amenity':True, 
    #       'landuse':['retail','commercial'], 
    #       'highway':'bus_stop'}

    env_path = Path(__file__).parent
    library_name = LIBRARY_VERSION + '.json'
    schema = env_path.joinpath('tags', library_name)
    text = schema.read_text()

    # get a dictionary
    data = json.loads(text)

    return data