import os
import pydicom
from PIL import Image
import numpy as np

def dicom_to_jpg(dicom_file, output_file):
    try:
        # Read DICOM file
        dicom_data = pydicom.dcmread(dicom_file)
        
        # Extract pixel data and check if it's valid
        if 'PixelData' not in dicom_data:
            print(f"File {dicom_file} does not contain pixel data.")
            return
        
        # Convert pixel data to numpy array
        pixel_array = dicom_data.pixel_array
        
        # Normalize pixel data to range 0-255
        pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) * 255
        pixel_array = pixel_array.astype(np.uint8)
        
        # Convert to PIL image
        img = Image.fromarray(pixel_array)
        
        # Convert to RGB if it's grayscale (1-channel)
        if len(img.getbands()) == 1:
            img = img.convert("RGB")
        
        # Save as JPEG
        img.save(output_file, 'JPEG')
        print(f"Saved JPEG: {output_file}")
        
    except Exception as e:
        print(f"Error converting {dicom_file}: {e}")

def convert_dicom_dir_to_jpg(input_dir, output_dir):
    count = 0
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            
            dicom_file = os.path.join(root, file)
            
            ## Create corresponding output directory if it doesn't exist
            #relative_path = os.path.relpath(root, input_dir)
            #output_subdir = os.path.join(output_dir, relative_path)
            #os.makedirs(output_subdir, exist_ok=True)
            
            # Create output JPEG filename
            
            # output_file = os.path.join(output_subdir, f"{os.path.splitext(file)[0]}.jpg")
            if "1-10" in dicom_file:
                output_file = "prostate_jpeg/{}.jpg".format(count)
                count = count + 1
                dicom_to_jpg(dicom_file, output_file)
            # Convert DICOM to JPEG
            # dicom_to_jpg(dicom_file, output_file)

if __name__ == "__main__":
    # Set the input directory containing DICOM files and output directory for JPEGs
    input_directory = "/Users/andrew/Downloads/DICOM/manifest-1600116693422/PROSTATEx"
    output_directory = "/Users/andrew/Downloads/DICOM/JPG"
    
    # Convert all DICOM images in the directory to JPEG
    convert_dicom_dir_to_jpg(input_directory, output_directory)