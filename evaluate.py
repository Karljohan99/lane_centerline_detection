import os
import json
import pickle
import shutil
import numpy as np
from tqdm import tqdm
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree

IMAGE_SIZE = 2048
SEGMENT_WIDTH = 3
THRESHOLD = 5
savedir = "RNGDet++_ft/test"
datadir = "./data/dataset"


def create_directory(dir,delete=False):
    if os.path.isdir(dir) and delete:
        shutil.rmtree(dir)
    os.makedirs(dir,exist_ok=True)


def draw_segment_img(road_graph, tile_index, savedir):
    global_mask = Image.fromarray(np.zeros((IMAGE_SIZE,IMAGE_SIZE))).convert('RGB')
    draw = ImageDraw.Draw(global_mask)

    for e in road_graph:
        draw.line([e[0][0],e[0][1],e[1][0],e[1][1]],width=SEGMENT_WIDTH,fill=(255,255,255))
                
    global_mask.save(f'{savedir}/segment/{tile_index}.png')


def calculate_scores(gt_points, pred_points, thr=3):
        gt_tree = cKDTree(gt_points)
        if len(pred_points):
            pred_tree = cKDTree(pred_points)
        else:
            return 0,0,0

        dis_gt2pred,_ = pred_tree.query(gt_points, k=1)
        dis_pred2gt,_ = gt_tree.query(pred_points, k=1)

        recall = len([x for x in dis_gt2pred if x<thr])/len(dis_gt2pred)
        acc = len([x for x in dis_pred2gt if x<thr])/len(dis_pred2gt)
        r_f = 0
        if acc*recall:
            r_f = 2*recall * acc / (acc+recall)
        return acc, recall, r_f


def pixel_eval_metric(pred_mask, gt_mask):
    def tuple2list(t):
        return [[t[0][x],t[1][x]] for x in range(len(t[0]))]

    gt_points = tuple2list(np.where(gt_mask!=0))
    pred_points = tuple2list(np.where(pred_mask!=0))

    return calculate_scores(gt_points, pred_points, THRESHOLD)


def intersection_eval_metric(pred_graph,gt_graph):
    def get_intersections_pred(graph):
        coord_counts = {}
        for e in graph:
            for p in e:
                p = tuple(p)
                if p in coord_counts:
                    coord_counts[p] += 1
                else:
                    coord_counts[p] = 1
        intersections = []
        for p, c in coord_counts.items():
            if c > 2:
                intersections.append([int(p[0]), int(p[1])])
        return intersections
    
    def get_intersections_gt(graph):
        intersections = []
        for p, v in graph.items():
            if len(v) > 2 or len(v) == 1:
                intersections.append([int(p[1]), int(p[0])])
        return intersections

    gt_points = get_intersections_gt(gt_graph)
    pred_points = get_intersections_pred(pred_graph)

    with open(f"{savedir}/json/{tile_index}.json",'r') as jf:
        pred_road_graph = json.load(jf)
        draw_segment_img(pred_road_graph, tile_index, savedir)

    return calculate_scores(gt_points, pred_points, THRESHOLD)


scores = []
scores_inter = []
text = ""
create_directory(f'./{savedir}/segment')
create_directory(f'./{savedir}/eval')
create_directory(f'./{savedir}/eval/diff')
create_directory(f'./{savedir}/eval/vis')
for name in tqdm(os.listdir(f'./{savedir}/json')):
    if name[-5:] != '.json':
        continue

    tile_index = name[:-5]

    with open(f"{savedir}/json/{tile_index}.json",'r') as jf:
        pred_road_graph = json.load(jf)
        draw_segment_img(pred_road_graph, tile_index, savedir)

    pred_graph_img = np.array(Image.open(f'./{savedir}/segment/{tile_index}.png'))

    inverted_pred = np.full(pred_graph_img.shape, 255) - pred_graph_img
    inverted_pred = inverted_pred.astype(np.uint8)
    inverted_pred_im = Image.fromarray(inverted_pred).convert('RGB')
    sat_im = Image.open(f"{datadir}/region_{tile_index}_sat.png")
    blended = Image.blend(inverted_pred_im, sat_im, alpha=0.5)
    blended.save(f"{savedir}/eval/vis/{tile_index}.png")
    
    gt_road_graph = pickle.load(open(f"{datadir}/region_{tile_index}_graph_gt.pickle",'rb'))

    gt_graph_img = np.array(Image.open(f'../RNGDetLarge/data/segment/{tile_index}.png'))
    score = pixel_eval_metric(pred_graph_img, gt_graph_img)
    scores.append(score)

    score_inter = intersection_eval_metric(pred_road_graph, gt_road_graph)
    scores_inter.append(score_inter)

    text += f"{tile_index}  {score}  {score_inter}\n"

    white = (255,255,255)
    blue = (0, 0, 255)
    red = (-255, 0, 0)

    pred_graph_img[(pred_graph_img == white).all(axis = -1)] = blue
    gt_graph_img[(gt_graph_img == white).all(axis = -1)] = red

    diffs = pred_graph_img - gt_graph_img

    diffs_im = Image.fromarray(np.abs(diffs)).convert('RGB')
    diffs_im.save(f'{savedir}/eval/diff/{tile_index}.png')



avg = np.mean(np.array(scores), axis=0)
avg_inter = np.mean(np.array(scores_inter), axis=0)
print(avg, avg_inter)

text += f"\nAverage pixel accuacy/recall/f1: {avg}"
text += f"\nAverage intersection accuacy/recall/f1: {avg_inter}"

with open(f"{savedir}/eval/eval.txt", "w") as rf:
    rf.write(text)