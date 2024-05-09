import os
import shutil
import json
import geopandas as gpd
from PIL import Image
from tqdm import tqdm
from pyproj import Transformer
import pickle

import mapdriver as md
import graph_ops as graphlib

from Tartu_ortho.create_sat import crop_image

Image.MAX_IMAGE_PIXELS = None
transformer = Transformer.from_crs(3301, 4326)

def create_directory(dir,delete=False):
    if os.path.isdir(dir) and delete:
        shutil.rmtree(dir)
    os.makedirs(dir,exist_ok=True)


def get_point(geometry, interval):
    dist = 0
    while dist < geometry.length:
        point = geometry.interpolate(dist)
        dist += interval
        yield point


map_file = 'tartu_large.gpkg'
data_dir = 'dataset'

IMG_SIZE = 2048
RESCALE = 2 

create_directory(data_dir)
create_directory("center")
walklines = gpd.read_file("walkline.shp")


file_name = 0

for year in ["2023", "2022"]:
    for _, walkline in walklines.iterrows():
        points = get_point(walkline.geometry, 300)

        while True:
            center_point = next(points, None)
            if center_point is None:
                break

            print(file_name)

            try:
                crop_image(center_point.coords[0], 
                        f"{data_dir}/region_{file_name}_sat.png",
                        IMG_SIZE, 0.1, year, RESCALE)
            except:
                continue

            x_st = center_point.coords[0][1] - RESCALE*IMG_SIZE/20
            y_st = center_point.coords[0][0] + RESCALE*IMG_SIZE/20
            
            x_ed = center_point.coords[0][1] + RESCALE*IMG_SIZE/20
            y_ed = center_point.coords[0][0] - RESCALE*IMG_SIZE/20

            lat_st, lon_st = transformer.transform(x_st, y_st)
            lat_ed, lon_ed = transformer.transform(x_ed, y_ed)

            lat_3, lon_3 = transformer.transform(x_ed, y_st)
            lat_4, lon_4 = transformer.transform(x_st, y_ed)

            region = [(y_st, x_st), (y_st, x_ed), (y_ed, x_ed), (y_ed, x_st)]
            region_lest = [y_ed, x_st, y_st, x_ed]

            geopackage_map = md.GeopackageMapLoader(region, map_file, "lanes")

            node_neighbor = {} # continuous

            for node_id, node_info in tqdm(geopackage_map.nodedict.items()):
                lat = node_info["lat"]
                lon = node_info["lon"]

                n1key = (lat,lon)

                neighbors = node_info["to"].keys() | node_info["from"].keys()

                for nid in neighbors:
                    n2key = (geopackage_map.nodedict[nid]["lat"],geopackage_map.nodedict[nid]["lon"])
                    graphlib.graphInsert(node_neighbor, n1key, n2key)

            
            graphlib.graphVis(node_neighbor,region_lest, IMG_SIZE, data_dir+f"/raw_{file_name}_gt.png")

            # interpolate the graph (20 meters interval)
            node_neighbor = graphlib.graphDensify(node_neighbor)
            node_neighbor_region = graphlib.graph2RegionCoordinate(node_neighbor, region_lest)

            graphlib.graphVis(node_neighbor,region_lest, IMG_SIZE, data_dir+f"/dense_{file_name}_gt.png")
            graphlib.graphVisSegmentation(node_neighbor, region_lest, data_dir+f"/region_{file_name}_gt.png")

            prop_graph = data_dir+f"/region_{file_name}_graph_gt.pickle"
            pickle.dump(node_neighbor_region, open(prop_graph, "wb"))

            node_neighbor_refine, sample_points = graphlib.graphGroundTruthPreProcess(node_neighbor_region)

            refine_graph = data_dir+f"/region_{file_name}_refine_gt_graph.p"
            pickle.dump(node_neighbor_refine, open(refine_graph, "wb"))
            json.dump(sample_points, open(data_dir+f"/region_{file_name}_refine_gt_graph_samplepoints.json", "w"), indent=2)


            #blend sat and graph
            raw_im = Image.open(data_dir+f"/raw_{file_name}_gt.png")
            sat_im = Image.open(data_dir+f"/region_{file_name}_sat.png")
            blended = Image.blend(raw_im, sat_im, alpha=0.5)
            blended.save(f"{data_dir}/blended_{file_name}_gt.png")

            #with open(f"loc/{file_name}.txt",'w') as f:
            #    f.write(f"{x_st} {y_st}")

            with open(f"center/center_{file_name}_sat.txt", "w") as f:
                f.write(f"{center_point.coords[0][1]}\n{center_point.coords[0][0]}")

            file_name += 1


