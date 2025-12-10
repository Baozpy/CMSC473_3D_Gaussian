from PIL import Image
import os

# get the size of an image in our input
dir = os.path.join('input', 'images')
image_list = os.listdir(dir)
ref = image_list[0]
ref = os.path.join(dir, ref)
reference = Image.open(ref)
size = reference.size

# calculate new size
factor = size[0]/1248 # we want the height of the resized image to be around 1248
new_size = (round(size[0]/factor), round(size[1]/factor))

# resize all input to the new calculated size
for i, name in enumerate(os.listdir(dir)):
    path = os.path.join(dir, name)
    image = Image.open(path)
    resized = image.resize(new_size)
    os.remove(path)
    resized.save(os.path.join(dir, f'image{i}.png'))