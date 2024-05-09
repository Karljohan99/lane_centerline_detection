import numpy as np
from PIL import Image

#img_size = 2048
#pixel_len = 0.1
#coords = (659622.99, 6474077.16)
#coords = (658973.31, 6473036.97)

def crop_image(center_coords, crop_name, img_size, pixel_len, year, scale):
    extrc_dir = f'Tartu_ortho/extracted/{year}'
    corners = [478655, 478662, 469655, 469662]

    x_c, y_c = center_coords
    x1 = round(x_c - scale*img_size//2*pixel_len, 1)
    y1 = round(y_c + scale*img_size//2*pixel_len, 1)

    tfw_file = open(f"{extrc_dir}/{corners[0]}.tfw", "r")
    tfw_lines = tfw_file.readlines()

    x_st, y_st = float(tfw_lines[4].strip()), float(tfw_lines[5].strip())

    tfw_file.close()

    i = int((x1-x_st)//1000)
    j = int((y_st-y1)//1000)

    index1 = corners[0]+i-j*1000
    im1 = Image.open(f"Tartu_ortho/extracted/{year}/{index1}.tif")
    arr1 = np.asarray(im1, dtype=np.uint8)

    index2 = corners[0]+i+1-j*1000
    im2 = Image.open(f"Tartu_ortho/extracted/{year}/{index2}.tif")
    arr2 = np.asarray(im2, dtype=np.uint8)

    index3 = corners[0]+i-(j+1)*1000
    im3 = Image.open(f"Tartu_ortho/extracted/{year}/{index3}.tif")
    arr3 = np.asarray(im3, dtype=np.uint8)

    index4 = corners[0]+i+1-(j+1)*1000
    im4 = Image.open(f"Tartu_ortho/extracted/{year}/{index4}.tif")
    arr4 = np.asarray(im4, dtype=np.uint8)

    cat_arr1 = np.concatenate([arr1, arr2], axis=1)
    cat_arr2 = np.concatenate([arr3, arr4], axis=1)

    large = np.concatenate([cat_arr1, cat_arr2], axis=0)

    tfw_file = open(f"{extrc_dir}/{index1}.tfw", "r")
    tfw_lines = tfw_file.readlines()

    x_l, y_l = float(tfw_lines[4].strip()), float(tfw_lines[5].strip())
    x1_c = round((x1 - x_l)/pixel_len)
    y1_c = round((y_l - y1)/pixel_len)

    x2_c = x1_c + scale*img_size
    y2_c = y1_c + scale*img_size

    tfw_file.close()

    crop = large[y1_c:y2_c, x1_c:x2_c]

    crop_im = Image.fromarray(crop)
    if scale != 1:
        crop_im = crop_im.resize((img_size, img_size), Image.LANCZOS)
    crop_im.save(crop_name)




