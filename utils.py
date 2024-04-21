"""
    To resize the images and change formats to .jpg
"""

import os
from PIL import Image

def resize_images(input_folder, output_folder, target_size):
    for root, dirs, files in os.walk(input_folder):
        rel_path = os.path.relpath(root, input_folder)
        output_subfolder = os.path.join(output_folder, rel_path)
        
        if not os.path.exists(output_subfolder):
            os.makedirs(output_subfolder)
        
        for file in files:
            input_path = os.path.join(root, file)
            output_path = os.path.join(output_subfolder, file)                
            img = Image.open(input_path)
            img = img.resize(target_size)
            img.save(output_path)

input_folder = "./Dataset"
output_folder = "./Dataset2"
target_size = (500, 500)  # Set your desired target size here

#resize_images(input_folder, output_folder, target_size)

