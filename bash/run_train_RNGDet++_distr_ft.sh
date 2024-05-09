CUDA_VISIBLE_DEVICES=0,1,2,3 torchrun --standalone --nproc_per_node=4 --max-restarts=0 main_train.py --savedir RNGDet++_ft \
 --dataroot ../data/lanes256 --data_dir dataset --batch_size 10 --ROI_SIZE 256 --nepochs 50 --multi_GPU --backbone resnet101 --eos_coef 0.2\
 --lr 1e-5 --lr_backbone 1e-5 --weight_decay 1e-5 --noise 8 --image_size 2048\
  --candidate_filter_threshold 30 --logit_threshold 0.75 --extract_candidate_threshold 0.55 --alignment_distance 5\
  --clip_max_norm 0.5 --instance_seg --multi_scale --pretrained ../RNGDet++_multi_ins/checkpoints/RNGDetNet_best.pt
