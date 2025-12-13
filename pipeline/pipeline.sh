# before running bash script make sure your input images are in the input/images folder

MAX_ITERATIONS=3
API_KEY=    # place your api key here

# resize input images to have a height of 1248
python resize_input.py \
    --input_dir input/images

for i in $(seq 1 $MAX_ITERATIONS);
do
    # run colmap to get a sparse reconstruction on the input images
    colmap automatic_reconstructor \
        --workspace_path ./input \
        --image_path ./input \
        --dense 0 \
        --single_camera 1

    # run gsplat
    CUDA_VISIBLE_DEVICES=0 python simple_trainer.py default \
        --data_dir input/ --data_factor 1 \
        --result_dir results_nano_banana/ \
        --disable_viewer \
        --render_traj_path ellipse \
        # --max_steps 1_000 \
        # --ckpt results_nano_banana/ckpts/ckpt_999_rank0.pt

    mkdir -p results_nano_banana/frames
    ffmpeg -i results_nano_banana/videos/traj_29999.mp4 -r 5 results_nano_banana/frames/frame%d.png

    # api call to nano banana to clean up frames
    python api_call.py \
        --key $API_KEY \
        --input_dir results_nano_banana/frames \
        --results_dir results_nano_banana/cleaned_frames_nbpro

    # resize and add frames to original batch of input images
    python resize_images.py \
        --reference_dir input/images \
        --target_dir results_nano_banana/cleaned_frames_nbpro

    if [ "$i" -ne "$MAX_ITERATIONS" ]; then
        # remove sparse folder
        rm -rf input/sparse

        # remove results folder
        rm -rf results_nano_banana
    fi

done