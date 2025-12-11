from PIL import Image
import os
import re

# get the size of an image in our input
dir = os.path.join('input', 'images')
image_list = os.listdir(dir)
last_id = max([int(re.search(r'\d+', image_list[x]).group(0)) for x in range(len(image_list))])
ref = image_list[0]
ref = os.path.join(dir, ref)
reference = Image.open(ref)
size = reference.size

# resize all the cleaned frames to the reference image's size
dir2 = os.path.join('results_nano_banana', 'cleaned_frames_nbpro')
for subdir in os.listdir(dir2):
    path = os.path.join(dir2, subdir, subdir+'_cleaned.png')
    cleaned_image = Image.open(path)
    resized = cleaned_image.resize(size)
    last_id += 1
    resized.save(os.path.join(dir, f'image{last_id}.png'))