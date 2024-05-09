import os
import json
import geopandas as gpd
from shapely.geometry import LineString

dir_name = "RNGDet++_ft_multi_ins"

input_dir = f"{dir_name}/test/json"
tfw_file_dir = "../RNGDet/data/maaamet_extrc"

x_px = 0.2
y_px = -0.2

def get_point(geometry, interval):
    dist = 0
    while dist < geometry.length:
        point = geometry.interpolate(dist)
        dist += interval
        yield point


lanes = []
coords = []
walklines = gpd.read_file("../Tartu_HDmap/walkline2.shp")
points = get_point(walklines.iloc[0].geometry, 300)

while True:
    center_point = next(points, None)
    if center_point is None:
        break

    x_st = center_point.coords[0][0] - 204.8
    y_st = center_point.coords[0][1] + 204.8

    coords.append((x_st, y_st))

for file in os.scandir(input_dir):
    if file.name[-5:] != '.json':
        continue
    
    name = file.name[:-5]
    with open(f"{input_dir}/{name}.json",'r') as jf:
        lane_graph = json.load(jf)

    x_st, y_st = coords[int(name)]

    for e in lane_graph:
        edge = [(x_st+e[0][0]*x_px, y_st+e[0][1]*y_px), (x_st+e[1][0]*x_px, y_st+e[1][1]*y_px)]
        road = LineString(edge)
        lanes.append(road)


gdf = gpd.GeoDataFrame({'geometry': lanes}, crs="EPSG:3301")
    
gdf.to_file(f'{dir_name}/test/rngdet++_256_ft.shp')  