import os
import shutil
import geopandas as gpd
from PIL import Image
from pyproj import Transformer

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
data_dir = 'testset'

IMG_SIZE = 2048
RESCALE = 2 

create_directory(data_dir)
walklines = gpd.read_file("walkline2.shp")


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
            
            file_name += 1


