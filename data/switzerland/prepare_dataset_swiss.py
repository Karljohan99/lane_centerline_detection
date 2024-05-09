import os
import shutil
import json
from PIL import Image
from PIL.TiffTags import TAGS
from tqdm import tqdm
from pyproj import Transformer
import pickle

import mapdriver as md
import graph_ops as graphlib 

Image.MAX_IMAGE_PIXELS = None
transformer = Transformer.from_crs(2056, 4326)

def create_directory(dir,delete=False):
    if os.path.isdir(dir) and delete:
        shutil.rmtree(dir)
    os.makedirs(dir,exist_ok=True)

extrc_dir = f'tif'
data_dir = 'data'

IMG_SIZE = 2048

create_directory(data_dir)
create_directory('tmp')

for file in os.scandir(extrc_dir):
    if file.name[-4:] != '.tif':
        continue
    
    file_name = file.name[:-4]
    file_name = file_name.split("_")[2]


    print(file_name)

    im = Image.open(file.path)
    resize_im = im.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
    resize_im.save(f"{data_dir}/region_{file_name}_sat.png","PNG")

    meta_dict = {TAGS[key] : im.tag[key] for key in im.tag.keys()}

    x_st, y_st = float(meta_dict["ModelTiepointTag"][3]), float(meta_dict["ModelTiepointTag"][4])
    x_px, y_px = 0.1, -0.1
    x_ed, y_ed = x_st + x_px*im.size[0], y_st + y_px*im.size[1]

    lat_st, lon_st = transformer.transform(x_st, y_st)
    lat_ed, lon_ed = transformer.transform(x_ed, y_ed)

    region = [lat_ed, lon_st, lat_st, lon_ed]
    region_2056 = [y_ed, x_st, y_st, x_ed]

    OSMMap = md.OSMLoader(region, False, includeServiceRoad = False)

    node_neighbor = {} # continuous

    for node_id, node_info in tqdm(OSMMap.nodedict.items()):
        lat = node_info["lat"]
        lon = node_info["lon"]

        n1key = (lat,lon)

        neighbors = node_info["to"].keys() | node_info["from"].keys()

        for nid in neighbors:
            n2key = (OSMMap.nodedict[nid]["lat"],OSMMap.nodedict[nid]["lon"])
            graphlib.graphInsert(node_neighbor, n1key, n2key)

    
    graphlib.graphVis(node_neighbor,region_2056, IMG_SIZE, data_dir+f"/raw_{file_name}_gt.png")

    # interpolate the graph (20 meters interval)
    node_neighbor = graphlib.graphDensify(node_neighbor)
    node_neighbor_region = graphlib.graph2RegionCoordinate(node_neighbor, region_2056)

    graphlib.graphVis(node_neighbor,region_2056, IMG_SIZE, data_dir+f"/dense_{file_name}_gt.png")
    graphlib.graphVisSegmentation(node_neighbor, region_2056, data_dir+f"/region_{file_name}_gt.png")

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

    

