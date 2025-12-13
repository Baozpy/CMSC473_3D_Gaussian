from PIL import Image
import os
import tyro

'''
resize_input() takes in a directory path input_dir and resizes
all images stored in that directory to have a height close to
1248. This reduces the computational workload of running
Colmap, 3D Gaussian Splatting, and our Nano Banana API call
pipeline.
'''

def resize_input(input_dir : str):

    # raise exception if input_dir is not a directory
    if not os.path.isdir(input_dir):
        raise ValueError("input_dir is not a directory!")

    # get the size of an image in our input
    image_list = os.listdir(input_dir)
    ref = image_list[0]
    ref = os.path.join(input_dir, ref)
    reference = Image.open(ref)
    size = reference.size

    # calculate new size
    factor = size[0]/1248 # we want the height of the resized image to be around 1248
    new_size = (round(size[0]/factor), round(size[1]/factor))

    # resize all input to the new calculated size
    for i, name in enumerate(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        image = Image.open(path)
        resized = image.resize(new_size)
        os.remove(path)
        resized.save(os.path.join(input_dir, f'image{i}.png'))

if __name__ == '__main__':
    tyro.cli(resize_input)