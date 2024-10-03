import os
import time
import cv2
import pytesseract
from flask import Flask, request, abort
from waitress import serve

app = Flask(__name__)
print('Running Tesseract Service')

'''
1. Run the service
2. Open PostMan and hit the url path with POST ( For Manual check )
3. Pass an image and observe the results
4. For Automation, Design methods that consumes the URL, pass canvas and fetch the response 
'''

CONFIG_ERROR_MESSAGE = 'Error in configuration settings. Accepted values: PSM 0-12 & OEM 0-3'


@app.route('/api/v1/get_img_coordinates', methods=["POST"])
def image_service(page_segmentation_modes: int = 11, ocr_engine: int = 3):
    # Validate input parameters
    if not (1 <= page_segmentation_modes <= 12 and 0 <= ocr_engine <= 3):
        print(CONFIG_ERROR_MESSAGE)
        abort(404, description=CONFIG_ERROR_MESSAGE)

    file_name = f'images/image{int(time.time())}.png'

    try:
        # Save and read the image
        request.files['img'].save(file_name)
        input_image = cv2.imread(file_name)

        # Extracting OCR data using pytesseract
        config = f'--psm {page_segmentation_modes} --oem {ocr_engine} wordstrbox'
        pytesseract_data = pytesseract.image_to_boxes(input_image, config=config).encode("utf-8").decode().split('\n')

        # Filter lines containing 'WordStr' and extract coordinates
        coordinates_data = [line.split('0 #')[0][8:] for line in pytesseract_data if 'WordStr' in line]
        key_list = [line.split('0 #')[1] for line in pytesseract_data if 'WordStr' in line]

        # Parse coordinates and generate bounding box info
        coordinates = {
            key_list[i]: {
                'middle': {
                    'x': (int(coord.split()[0]) + int(coord.split()[2])) // 2,
                    'y': (int(coord.split()[1]) + int(coord.split()[3])) // 2,
                },
                'top_left': {'x': int(coord.split()[0]), 'y': int(coord.split()[1])},
                'top_right': {'x': int(coord.split()[2]), 'y': int(coord.split()[1])},
                'bottom_left': {'x': int(coord.split()[0]), 'y': int(coord.split()[3])},
                'bottom_right': {'x': int(coord.split()[2]), 'y': int(coord.split()[3])},
            }
            for i, coord in enumerate(coordinates_data)
        }

        return coordinates

    except Exception as e:
        print(f'Error processing image: {e}')
        abort(404, description=f"File not found: {e}")

    finally:
        # Clean up the image file
        if os.path.exists(file_name):
            os.remove(file_name)


serve(app, host='0.0.0.0', port=8088)
