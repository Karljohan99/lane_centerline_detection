import numpy as np
from PIL import Image

corners = [478655, 478662, 469655, 469662]

x_range = corners[1] - corners[0]
y_range = corners[0] - corners[2]

arrays = []

for i in range(x_range+1):
    arrs = []
    for j in range((y_range//1000)+1):
        index = corners[0]+i-j*1000
        name = f"extracted/{index}.tif"
        im = Image.open(name)
        arr = np.asarray(im, dtype=np.uint8)
        arrs.append(arr)


    cat_arr = np.concatenate(arrs, axis=1)
    arrays.append(cat_arr)

large = np.concatenate(arrays, axis=0)



            



