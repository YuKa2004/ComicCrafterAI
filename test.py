import subprocess
import os
import time
from PIL import Image

# Paths (Update these based on your setup)
COMFYUI_FOLDER = "C:\ComfyUI_windows_portable"  # Change this to your ComfyUI folder
COMFYUI_OUTPUT_FOLDER = "C:\ComfyUI_windows_portable\ComfyUI\output"

# Function to start ComfyUI
def start_comfyui():
    print("🚀 Starting ComfyUI...")
    subprocess.Popen(["python", "main.py"], cwd=COMFYUI_FOLDER, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10)  # Wait for ComfyUI to launch

# Function to get the latest image from the output folder
def get_latest_image(folder):
    files = [f for f in os.listdir(folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        return None
    files.sort(key=lambda x: os.path.getctime(os.path.join(folder, x)), reverse=True)
    return os.path.join(folder, files[0])  # Latest image

# Function to check if an image was generated
def check_comfyui_image():
    print("🔍 Waiting for generated images...")
    
    # Wait for up to 30 seconds for an image to appear
    for _ in range(30):
        img_path = get_latest_image(COMFYUI_OUTPUT_FOLDER)
        if img_path:
            print(f"✅ Image found: {img_path}")
            img = Image.open(img_path)
            img.show()  # Opens image
            return True
        time.sleep(1)

    print("❌ No image found. Check if ComfyUI is saving images in the correct folder.")
    return False

# Run Tests
print("🛠 Running ComfyUI Test...\n")
start_comfyui()  # Auto-start ComfyUI
check_comfyui_image()
print("\n✅ Testing Complete!")
