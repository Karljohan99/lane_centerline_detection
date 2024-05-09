CUDA_VISIBLE_DEVICES=0,1,2,3 torchrun --standalone --nproc_per_node=4 --max-restarts=0 main_train.py --savedir RNGDet\
 --dataroot ./data/ --data_dir dataset --batch_size 20 --ROI_SIZE 128 --nepochs 50 --multi_GPU --backbone resnet101 --eos_coef 0.2\
 --lr 1e-4 --lr_backbone 1e-4 --weight_decay 1e-5 --noise 8 --image_size 2048\
 --candidate_filter_threshold 30 --logit_threshold 0.75 --extract_candidate_threshold 0.55 --alignment_distance 5
