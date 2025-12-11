import os
import tyro
import random
import shutil

def sparsify(input_path : str, output_path : str, sample_ratio : float):
    # delete output directory if it already exists
    if os.path.isdir(output_path):
        shutil.rmtree(output_path)

    image_folders = [] # list of image directories
    for dir in os.listdir(input_path):
        if 'images' in dir and 'png' not in dir:
            image_folders.append(dir)
    
    chosen_images = os.listdir(input_path + '/' + image_folders[0])
    sample_number = int(len(chosen_images) * sample_ratio)
    chosen_images = random.sample(chosen_images, sample_number)
    print('number of images: ', len(chosen_images))

    # create the new directory if it does not already exist
    os.makedirs(output_path, exist_ok=True)
    for folder in image_folders:
        os.makedirs(os.path.join(output_path, folder), exist_ok=True)

    for folder in image_folders:
        for image in chosen_images:
            file_name = os.path.join(folder, image)
            source = os.path.join(input_path, file_name)
            destination = os.path.join(output_path, file_name)
            shutil.copy(source, destination)

if __name__ == '__main__':
    tyro.cli(sparsify)