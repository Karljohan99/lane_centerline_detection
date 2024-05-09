import os
import json
import geopandas as gpd
from shapely.geometry import LineString

dir_name = "RNGDet++_multi_ins"

input_dir = f"{dir_name}/test/json"
tfw_file_dir = "../RNGDet/data/dataset"

roads = []
for file in os.scandir(input_dir):
    if file.name[-5:] != '.json':
        continue
    
    name = file.name[:-5]
    with open(f"{input_dir}/{name}.json",'r') as jf:
        road_graph = json.load(jf)

    with open(f"{tfw_file_dir}/{name}.tfw", "r") as tfw:
        tfw_lines = tfw.readlines()

        x_st, y_st = float(tfw_lines[4].strip()), float(tfw_lines[5].strip())
        x_px, y_px = float(tfw_lines[0].strip()), float(tfw_lines[3].strip())

    x_px *= 10000/2048
    y_px *= 10000/2048

    for e in road_graph:
        edge = [(x_st+e[0][0]*x_px, y_st+e[0][1]*y_px), (x_st+e[1][0]*x_px, y_st+e[1][1]*y_px)]
        road = LineString(edge)
        roads.append(road)


gdf = gpd.GeoDataFrame({'geometry': roads}, crs="EPSG:3301")
    
gdf.to_file(f'{dir_name}/test/rngdet++.shp')  