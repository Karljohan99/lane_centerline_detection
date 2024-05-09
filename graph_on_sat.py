from PIL import Image, ImageDraw

SEGMENT_WIDTH = 3
savedir = "RNGDet++_intersect10_multi_ins/test"
datadir = "dataset"


def draw_graph_on_sat(road_graph, datadir, name, savedir):
    sat_im = Image.open(f"./data/{datadir}/region_{name}_sat.png")

    draw = ImageDraw.Draw(sat_im)

    for e in road_graph:
        draw.line([e[0][0],e[0][1],e[1][0],e[1][1]],width=SEGMENT_WIDTH,fill=(255,255,255))

    sat_im.save(f'{savedir}/sat+graph/{name}.png')


