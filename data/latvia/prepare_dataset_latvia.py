import os
import shutil
import json
from itertools import product
from PIL import Image
from tqdm import tqdm
from pyproj import Transformer
import pickle

import mapdriver as md
import graph_ops as graphlib 

Image.MAX_IMAGE_PIXELS = None
transformer = Transformer.from_crs(3059, 4326)

def create_directory(dir,delete=False):
    if os.path.isdir(dir) and delete:
        shutil.rmtree(dir)
    os.makedirs(dir,exist_ok=True)

extrc_dir = f'raw_data'
data_dir = 'data'

IMG_SIZE = 2048
TILE_SIZE = 4000

create_directory(data_dir)
create_directory('tmp')


for file in os.scandir(extrc_dir):
    if file.name[-4:] != '.tif':
        continue
    
    file_name_l = file.name[:-4]

    crop_box = (1000,1000,9000,9000)
    large_im = Image.open(file.path).crop(crop_box)
    w, h = large_im.size

    tfw_file = open(f"{extrc_dir}/{file_name_l}.tfw", "r")
    tfw_lines = tfw_file.readlines()
    x_c, y_c = float(tfw_lines[4].strip())+250, float(tfw_lines[5].strip())-250
    x_px, y_px = float(tfw_lines[0].strip()), float(tfw_lines[3].strip())
    
    grid = product(range(0, h-h%TILE_SIZE, TILE_SIZE), range(0, w-w%TILE_SIZE, TILE_SIZE))
    for i, j in grid:
        box = (j, i, j+TILE_SIZE, i+TILE_SIZE)
        im = large_im.crop(box)
        resize_im = im.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)

        file_name = f"{file_name_l}_{j//TILE_SIZE}_{i//TILE_SIZE}"

        x_st, y_st = x_c + x_px*j, y_c + y_px*i
        x_ed, y_ed = x_c + x_px*(j+TILE_SIZE), y_c + y_px*(i+TILE_SIZE)

        lat_st, lon_st = transformer.transform(y_st, x_st)
        lat_ed, lon_ed = transformer.transform(y_ed, x_ed)

        region = [lat_ed,lon_st,lat_st,lon_ed]
        region_lest = [y_ed, x_st, y_st, x_ed]

        print("==================")
        OSMMap = md.OSMLoader(region, False, includeServiceRoad = False)
        if len(OSMMap.nodedict) < 5000:
            continue

        print(file_name)

        resize_im.save(f"{data_dir}/region_{file_name}_sat.png","PNG")

        node_neighbor = {} # continuous

        for node_id, node_info in tqdm(OSMMap.nodedict.items()):
            lat = node_info["lat"]
            lon = node_info["lon"]

            n1key = (lat,lon)

            neighbors = node_info["to"].keys() | node_info["from"].keys()

            for nid in neighbors:
                n2key = (OSMMap.nodedict[nid]["lat"],OSMMap.nodedict[nid]["lon"])
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

    


    

