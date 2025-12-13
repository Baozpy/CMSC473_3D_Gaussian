import os
import tyro
import random
import shutil

'''
sparsify() takes in a path to a existing directory containing images. The function
also takes in a parameter for the sampling ratio which it uses to randomly select
a subset of images from the image directory. The subset is then saved in the 
directory path output_path. The sample_ratio parameter should range from 0 to 1 
exclusive. 

Example usage for randomly selecting 25% of images
python dataset/sparse_dataset.py --input-path input/images --output-path sparse_input/images --sample-ratio 0.25
'''
def sparsify(input_path : str, output_path : str, sample_ratio : float):

    # raise exception if sample_ratio is not between 0 and 1 exclusive
    if sample_ratio <= 0 or sample_ratio >= 1:
        raise ValueError("sample_ratio has to be between 0 and 1 exclusive!")
    
    # raise exception if input_path is not a directory
    if not os.path.isdir(input_path):
        raise ValueError("input_path is not a directory!")

    # delete output directory if it already exists
    if os.path.isdir(output_path):
        shutil.rmtree(output_path)
            
    chosen_images = os.listdir(input_path)
    sample_number = int(len(chosen_images) * sample_ratio)
    chosen_images = random.sample(chosen_images, sample_number)
    print('number of images: ', len(chosen_images))

    # create the new directory if it does not already exist
    os.makedirs(output_path, exist_ok=True)

    # copy the subset of images to the output path
    for image in chosen_images:
        source = os.path.join(input_path, image)
        destination = os.path.join(output_path, image)
        shutil.copy(source, destination)

if __name__ == '__main__':
    tyro.cli(sparsify)