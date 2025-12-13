from PIL import Image
import os
import re
import tyro

'''
concatenate_images() takes in a path to a directory reference_dir
and a path to a directory target_dir. The function looks up the 
dimension of the images stored in reference_dir and resizes
the images stored in target_dir to match that of reference_dir.
Each resized image in target_dir is then renamed and added to
the reference_dir. 
'''

def concatenate_images(reference_dir : str, target_dir : str):

    # raise exception if reference_dir is not a directory
    if not os.path.isdir(reference_dir):
        raise ValueError("reference_dir is not a directory!")

    # raise exception if target_dir is not a directory
    if not os.path.isdir(target_dir):
        raise ValueError("target_dir is not a directory!")

    # get the images stored in reference_dir
    dir = os.path.join('input', 'images')
    image_list = os.listdir(reference_dir)

    # store the last image id ordered from least to greatest
    last_id = max([int(re.search(r'\d+', image_list[x]).group(0)) for x in range(len(image_list))])

    # get the dimensions of the reference images
    ref = image_list[0]
    ref = os.path.join(reference_dir, ref)
    reference = Image.open(ref)
    size = reference.size

    # resize all the cleaned frames to the reference image's size
    dir2 = os.path.join('results_nano_banana', 'cleaned_frames_nbpro')
    for subdir in os.listdir(target_dir):
        path = os.path.join(target_dir, subdir, subdir+'_cleaned.png')
        cleaned_image = Image.open(path)
        resized = cleaned_image.resize(size)
        last_id += 1
        resized.save(os.path.join(reference_dir, f'image{last_id}.png'))

if __name__ == '__main__':
    tyro.cli(concatenate_images)