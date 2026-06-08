import time
from astropy.stats import SigmaClip #optional but great!
import json
import serial
#dont forget these libraries
import numpy as np
from PIL import Image, ImageEnhance
import os
from scipy.ndimage import gaussian_filter

class sky:
    def __init__(self, path, save_path, number, baudrate, port):
        self.path = path
        self.save_path = save_path
        self.number = number
        self.photos = []
        print("Connecting to Arduino and initializing control link...")
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2) 
        print("System Online.")

    def initialize(self):
        os.chdir(self.path)
        print(os.getcwd())
        if len(os.listdir(self.path)) >= self.number and os.getcwd() == self.path:
            return True 
        else:
            print("Not enough photos in the directory.")
            return False
    
    def transfer(self, mobile_path):
         os.system("adb pull " + mobile_path + " " + self.path) #this might vary
         print("Successfully transfered the files!")
    
    def click(self):
         os.system("adb shell input keyevent 27")
         print("Clicked!")

    def serial_w(self, state):
        payload = {
            's': state
        }
        json_string = json.dumps(payload) + "\n"
        self.ser.write(json_string.encode('utf-8'))
        print(f"--> Command Dispatched: {json_string.strip()}")
        return payload
    def close(self):
        self.ser.close()
        print("Serial connection closed.")
        
    def stack(self, contrast_factor=1.2, chunk_rows=500):
        if self.initialize():
            files = [f for f in os.listdir(self.path)
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))][:self.number]
            if len(files) < self.number:
                print(f"Warning: Found only {len(files)} images, but expected {self.number}.")
                return
            fip = os.path.join(self.path, files[0])
            with Image.open(fip) as fipp:
                width, height = fipp.size
                channels = len(fipp.getbands())
            stacked_array = np.zeros((height, width, channels), dtype=np.float32)
            num_frames = len(files)
            print(f"Starting memory-safe sigma-stacking across {num_frames} frames...")

            for y_start in range(0, height, chunk_rows):
                y_end = min(y_start + chunk_rows, height)
                current_chunk_height = y_end - y_start

                chunk_cube = np.zeros(
                    (num_frames, current_chunk_height, width, channels),
                    dtype=np.float32
                )

                for idx, file in enumerate(files):
                    full_file_path = os.path.join(self.path, file)
                    with Image.open(full_file_path) as img:
                        cropped_slice = img.crop((0, y_start, width, y_end))
                        chunk_cube[idx] = np.array(cropped_slice.convert("RGB"), dtype=np.float32)
                chunk_medi = np.median(chunk_cube, axis=0)
                chunk_deviation = np.std(chunk_cube, axis=0)
                chunk_deviation[chunk_deviation == 0] = 1.0
                mask = np.abs(chunk_cube - chunk_medi) < (4 * chunk_deviation)
                cleaned_chunk = np.where(mask, chunk_cube, np.nan)
                final_chunk_mean = np.nanmean(cleaned_chunk, axis=0)
                nan_mask = np.isnan(final_chunk_mean)
                final_chunk_mean[nan_mask] = chunk_medi[nan_mask]
                stacked_array[y_start:y_end, :, :] = final_chunk_mean
                del chunk_cube, chunk_medi, chunk_deviation, mask, cleaned_chunk, final_chunk_mean
            res = stacked_array
            bg = gaussian_filter(res, sigma=(80, 80, 0))
            res = res - bg
            res = np.clip(res, 0, None)
            res = np.arcsinh(res * 3)
            res = res / (res.max() + 1e-6) * 255
            result = Image.fromarray(res.astype(np.uint8))
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(contrast_factor)
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)

            save_file_path = os.path.join(self.save_path, "stacked_enhanced.jpg")
            result.save(save_file_path)

            print(f"Enhanced stacked image saved to: {save_file_path}")
image = sky(r"your_path", 
            r"your_path", 
            14, 9600, 'COM4')
image.serial_w(0)

while not image.initialize():
    image.serial_w(1)
    image.click()
    image.transfer("your_mobile_path")
    time.sleep(35) #adjust it according to your shutter speed Pro tip make this delay 3 seconds more than the shutter speed you are using

image.serial_w(0)  
image.close() 
image.stack()
