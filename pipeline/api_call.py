from google import genai
from google.genai import types
from PIL import Image
import os
import tyro

'''
api_call.py is a python script takes in an API key for 
running Gemini models, a directory input_dir containing 
3DGS renders that you wish to clean/reconstruct with 
Nano Banana Pro, and a directory results_dir for storing
the cleaned renders.
'''

def clean_frames(key : str, input_dir : str, results_dir : str):
    
    # raise exception if input_dir is not a directory
    if not os.path.isdir(input_dir):
        raise ValueError("input_dir is not a directory!")
    
    # raise exception if results_dir is not a directory
    if not os.path.isdir(results_dir):
        raise ValueError("results_dir is not a directory!")

    # set up client for calling Gemini models
    client = genai.Client(api_key=key)

    # create the results directory for storing outputs
    os.makedirs(results_dir, exist_ok=True)

    # clean each frame through api calls to Nano Banana Pro
    for frame in os.listdir(input_dir):
        print(frame)

        # get the frame
        image = Image.open(os.path.join(input_dir, frame))

        # downsample the frame
        low_res_image = image.resize((1248//10, 832//10))
        low_res_image = low_res_image.resize((1248, 832))

        # copy the original frame and save the downsampled version
        os.makedirs(os.path.join(results_dir, frame[:-4]), exist_ok=True)
        image.save(os.path.join(results_dir, frame[:-4], frame))
        low_res_image.save(os.path.join(results_dir, frame[:-4], frame[:-4]+'_low_res.png'))
        
        # list of prompts for cleaning frames
        prompt1 = (
            f"Create a colored depth map of this image. Do not change the contour lines. Do not introduce glares. Do not alter the scene.",
        )
        prompt2 = (
            f"aspect_ratio=\"3:2\". Recover the original image in natural light with high resolution. Do not introduce glares. Do not alter the scene.",
        )

        # create a colored depth map
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt1, image],
        )

        # save the colored depth map
        for part in response.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                depth_map = part.as_image()
                depth_map.save(os.path.join(results_dir, frame[:-4], frame[:-4]+'_depth_map.png'))
        depth_map = Image.open(os.path.join(results_dir, frame[:-4], frame[:-4]+'_depth_map.png'))

        # reconstruct the frame using the colored depth map and downsampled image
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt2, low_res_image, depth_map],
        )

        # save the reconstructed frame
        for part in response.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                cleaned_image = part.as_image()
                cleaned_image.save(os.path.join(results_dir, frame[:-4], frame[:-4]+'_cleaned.png'))

if __name__ == '__main__':
    tyro.cli(clean_frames)