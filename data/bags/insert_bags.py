import os
import geopandas as gpd
from tqdm import tqdm
from PIL import Image, ImageDraw

BAGS_SHAPEFILE = "../Bagfiles/bag_lanes_2023_2024.shp"
IMAGES = "../data/lanes256_large/dataset"
#IMAGES = "./whole_tartu"

OPACITY = 20

trajectories = gpd.read_file(BAGS_SHAPEFILE)
opacity = lambda transparency: (int(255 * (transparency/100)),)
color = (0, 0, 0) + opacity(OPACITY)

for k, file in enumerate(tqdm(os.scandir(IMAGES))):
    if file.name[-7:] != "sat.png":
        continue
    
    _, n, _ = file.name.split("_")
    img = Image.open(f"{IMAGES}/{file.name}")
    img = img.convert("RGBA")

    overlay = Image.new('RGBA', img.size, color[:3]+opacity(0))
    for trajectory in trajectories.geometry:
        overlay_temp = Image.new('RGBA', img.size, color[:3]+opacity(0))
        draw_temp = ImageDraw.Draw(overlay_temp)
        for i in range(len(trajectory.coords)-1):
            with open(f"center_dataset/center_{n}_sat.txt") as f:
                coords = f.readlines()

            x_st = float(coords[1].strip()) - 204.8
            y_st = float(coords[0].strip()) + 204.8

            x0 = (trajectory.coords[i][0] - x_st)*5
            y0 = (y_st - trajectory.coords[i][1])*5
            x1 = (trajectory.coords[i+1][0] - x_st)*5
            y1 = (y_st - trajectory.coords[i+1][1])*5
            
            draw_temp.line([(x0, y0), (x1, y1)],width=2,fill=color)
        overlay = Image.alpha_composite(overlay, overlay_temp)

    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(f"lanes_bags/{file.name}")
