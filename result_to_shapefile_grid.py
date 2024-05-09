import os
import json
import geopandas as gpd
from shapely.geometry import LineString

def write_to_gpkg(name, data):
    for layer in data.keys():
        if data[layer].empty:
            continue

        data[layer].to_file(name, layer=layer, driver="GPKG")

dir_name = "RNGDet++_ft_multi_ins"

input_dir = f"{dir_name}/whole_tartu/json"

x_px = 0.2
y_px = -0.2

lanes = {'type': [],
     'turn_direction': [],
     'ref_velocity': [],
     'limit_velocity': [],
     'oneway': [],
     'left_width': [],
     'right_width': [],
     'comment': [],
     'export_to_lanelet2': [],
     'geometry': []}

for file in os.scandir(input_dir):
    if file.name[-5:] != '.json':
        continue
    
    name = file.name[:-5]
    with open(f"{input_dir}/{name}.json",'r') as jf:
        lane_graph = json.load(jf)

    with open(f"../data/lanes256/whole_tartu/center/center_{name}_sat.txt",'r') as f:
        coords = f.readlines()

    x_st = float(coords[1].strip()) - 204.8
    y_st = float(coords[0].strip()) + 204.8

    for e in lane_graph:
        edge = [(x_st+e[0][0]*x_px, y_st+e[0][1]*y_px), (x_st+e[1][0]*x_px, y_st+e[1][1]*y_px)]
        lane = LineString(edge)

        lanes['type'].append('1')
        lanes['turn_direction'].append('0')
        lanes['ref_velocity'].append('40')
        lanes['limit_velocity'].append('50')
        lanes['oneway'].append(True)
        lanes['left_width'].append('1.2')
        lanes['right_width'].append('1.2')
        lanes['comment'].append(name)
        lanes['export_to_lanelet2'].append(True)
        lanes['geometry'].append(lane)


gdf = gpd.GeoDataFrame(lanes, crs="EPSG:3301")

write_to_gpkg(f"{dir_name}/whole_tartu/tartu_lanes.gpkg", {"lanes":gdf})
    
gdf.to_file(f'{dir_name}/whole_tartu/rngdet++_256_ft.shp')  