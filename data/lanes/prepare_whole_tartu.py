import os
import shutil
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
data_dir = 'whole_tartu'

IMG_SIZE = 2048
RESCALE = 2
PIXEL_SIZE = 0.1

create_directory(data_dir)
create_directory(data_dir + "/center")

file_name = 0

start_x = 6476915.9
start_y = 655445.3


for i in range(18):
    for j in range(18):
        x = start_x - i*IMG_SIZE*PIXEL_SIZE*RESCALE
        y = start_y + j*IMG_SIZE*PIXEL_SIZE*RESCALE

        try:
            crop_image((y, x), 
                    f"{data_dir}/region_{i}_{j}_sat.png",
                    IMG_SIZE, PIXEL_SIZE, "2023", RESCALE)
        except:
            print("ERROR")
            continue

        with open(f"{data_dir}/center/center_{i}_{j}_sat.txt", "w") as f:
            f.write(f"{x}\n{y}")


        


