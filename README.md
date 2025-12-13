# Using Diffusion Models for Sparse 3D Gaussian Splatting (3DGS)

## Introduction

3D Gaussian Splatting [(Kerbl et. al.)](https://arxiv.org/abs/2308.04079) has quickly become a leading approach for real-time rendering by representing scenes as collections of anisotropic Gaussians with learnable geometric and appearance attributes, enabling high-quality view synthesis without the heavy volumetric integration required by implicit radiance fields [(Mildenhall et. al.)](https://arxiv.org/abs/2003.08934). However, despite its efficiency and strong performance under dense, well-covered input views, the method faces significant challenges when applied to a set of sparse input views common in mobile captures from the average user. With limited viewpoints, photometric and geometric cues become insufficiently constrained, leading to depth ambiguities, unstable optimization, floating artifacts, and overfitting to the few available views. These issues highlight an important gap between controlled experimental conditions and real-world data acquisition, motivating ongoing research into structural priors, depth cues, and hybrid representations that aim to make Gaussian Splatting more robust and reliable under sparse input.

## What We Accomplished

Our team thought of many approaches on improving the quality of rendered views despite having having sparse input views. These approaches include making API calls to Nano Banana Pro to clean up badly-rendered 3DGS views, ...

## Approach 1: Cleaning Badly-Rendered 3DGS Views with Nano Banana Pro

### Prerequisite
Create a Conda environment and then install [Pytorch](https://pytorch.org/get-started/locally/)

### Setting up Conda environment
```
cd pipeline
pip install -r requirements.txt
pip install gsplat
conda install conda-forge::colmap
```

### Pipeline details

This approach is implemented in the pipeline subdirectory of this repository, and it focuses on improving the render quality of NerfStudio's 3DGS model [Gsplat](https://github.com/nerfstudio-project/gsplat) when given a sparse set of views. To improve the render quality of the Gsplat model when trained on a sparse set of images, we first filter out geometrically inconsistent views through [Colmap's](https://colmap.github.io/) sparse reconstruction. We then train the model for 30 thousand iterations before freezing it. We then use the frozen model to render a mp4 video of the captured scene that takes on an ellipsoidal camera path trajectory. The mp4 video is then split into individual frames and each frame is cleaned using 2 API calls to Nano Banana Pro. The first API call creates a colored depth map of the frame. The second API call then uses a downsampled version of the original frame together with the previously generated colored depth map to reconstruct a clean, distortion-free frame. The cleaned frames are then resized and concatenated to the sparse set of views, and the whole process is repeated another two times. 

### Dataset used for testing
We tested this approach on both 15% and 25% of the images (randomly sampled) within the bicycle dataset of Mip-NeRF 360. 

You can download this dataset with the following command:
```
python pipeline/datasets/download_dataset.py
```
You can then simulate a sparse dataset by doing the following:
```
python pipeline/datasets/sparse_dataset.py --input-path <path to images directory> --output-path <output directory> --sample-ratio <0-1 exclusive>
```

### Nano Banana Pro Results

Most 3DGS rendered frames for a model trained on just 25% of the original bicycle dataset were successfully cleaned and reconstructed by Nano Banana Pro as shown below for frame 16 under the /results_nano_banana_bikesparse48 directory.

3DGS Rendered Frame 16             |  Downsampled          |Colored Depth Map             |  Cleaned Frame 16
:-------------------------:|:-------------------------:|:-------------------------:|:-------------------------:
![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame16/frame16.png)   | ![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame16/frame16_low_res.png) | ![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame16/frame16_depth_map.png)  |  ![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame16/frame16_cleaned.png)

However some reconstructed frames had clear hallucinations, usually in the background, as shown below in frame 4 under the /results_nano_banana_bikesparse48 directory.
3DGS Rendered Frame 4             |  Downsampled          |Colored Depth Map             |  Cleaned Frame 4
:-------------------------:|:-------------------------:|:-------------------------:|:-------------------------:
![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame4/frame4.png)   | ![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame4/frame4_low_res.png) | ![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame4/frame4_depth_map.png)  |  ![](pipeline/results_nano_banana_bikesparse48/cleaned_frames_nbpro/frame4/frame4_cleaned.png)

Nano Banana Pro performed significantly worse on just 15% of the original bicycle dataset. We hypothesize this is due to the poor quality of the 3DGS renders. It is likely that Nano Banana Pro could not determine what was captured in the 3DGS rendered frames, so it hallucinated entirely different scenes. After the third iteration of our pipeline, all 3DGS frames were heavily distorted by the accumulated hallucinations. We show the Nano Banana Pro results for frame 14 under the /results_nano_banana_bikesparse29 directory as an example below.

3DGS Rendered Frame 14             |  Downsampled          |Colored Depth Map             |  Cleaned Frame 14
:-------------------------:|:-------------------------:|:-------------------------:|:-------------------------:
![](pipeline/results_nano_banana_bikesparse29/cleaned_frames_nbpro/frame14/frame14.png)   | ![](pipeline/results_nano_banana_bikesparse29/cleaned_frames_nbpro/frame14/frame14_low_res.png) | ![](pipeline/results_nano_banana_bikesparse29/cleaned_frames_nbpro/frame14/frame14_depth_map.png)  |  ![](pipeline/results_nano_banana_bikesparse29/cleaned_frames_nbpro/frame14/frame14_cleaned.png)

### Overall Results
This approach performed worse on all benchmarks when compared to just using 3DGS. We think this is due to the accumulated hallucinations introduced in the background of the 3DGS rendered frames as well as geometric inconsistencies that were not pruned by Colmap.

#### 25% of bicycle dataset from Mip-NeRF 360:
| Implementation | PSNR  | SSIM | LPIPS |
|----------------|-------|------|-------|
|    baseline    | 16.98 | 0.44 | 0.38  |
|      ours      | 16.76 | 0.35 | 0.41  |

#### 15% of bicycle dataset from Mip-NeRF 360:
| Implementation | PSNR  | SSIM | LPIPS |
|----------------|-------|------|-------|
|    baseline    | 12.72 | 0.31 | 0.52  |
|      ours      | 12.15 | 0.17 | 0.61  |

### Proposed Further Improvements
* Pass in all 3DGS rendered frames and original input simultaneously to a video diffusion model to get structural priors
* Add an additional filtering pipeline to remove cleaned frames that are geometrically inconsistent with the input

### Training your own sparse set of images using this approach
1. Make a directory for you input named input/images and place your images in that directory.
    ```
    cd pipeline
    mkdir -p input/images
    ```
2. Activate your conda environment from following steps in [prerequisite](#prerequisite) and [setup](#setting-up-conda-environment).
3. Run the pipeline!
    ```
    bash pipeline.sh
    ```
