import os
import numpy as np
from PIL import Image
os.chdir("E:/Rajendra sir backup/Old PC/Backup 2025-1-13/Desktop/Mine/Others/Scripts/sky/unchanged")
images = [f for f in os.listdir() if f.lower().endswith(('.jpg', '.jpeg', '.png'))][:14]
photos = []
for image in images:
    img = Image.open(image)
    photos.append(np.array(img.convert("RGB")))
b = np.array(photos)
c=np.median(b, axis=0)
print(np.std(c))