# before running bash script make sure your input images are in the input/images folder

# run colmap to get a sparse reconstruction on the input images
colmap automatic_reconstructor \
    --workspace_path ./input \
    --image_path ./input \
    --dense 0 \
    --single_camera 1

# run gsplat
CUDA_VISIBLE_DEVICES=0 python simple_trainer.py default \
    --data_dir input/ --data_factor 4 \
    --result_dir results/