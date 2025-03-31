import subprocess
import time
import requests
import json
import streamlit as st
import os

# ComfyUI Configuration
COMFYUI_PATH = "C:\ComfyUI_windows_portable\ComfyUI"  # Replace with your ComfyUI directory
API_URL = "http://127.0.0.1:8188/prompt"  # Default ComfyUI API endpoint
HISTORY_URL = "http://127.0.0.1:8188/history/"
UPLOAD_URL = "http://127.0.0.1:8188/upload/image"
CLIENT_ID = str(time.time())

# Workflow (Replace with your actual workflow JSON)
# Example Workflow (simple text to image, adjust to your flux.1 workflow)
WORKFLOW = {
    "3": {
        "inputs": {
            "text": "A beautiful landscape",
            "clip": ["4", 1],
        },
        "class_type": "CLIPTextEncode",
    },
    "4": {
        "inputs": {
            "ckpt_name": "flux1-dev-Q4_0.gguf", #Ensure correct model name
        },
        "class_type": "Load Checkpoint",
    },
    "6": {
        "inputs": {
            "samples": ["5", 0],
            "vae": ["4", 2],
        },
        "class_type": "VAEDecode",
    },
    "5": {
        "inputs": {
            "latent_image": ["10", 0],
            "samples": 1,
            "steps": 20,
            "cfg": 8,
            "seed": 0,
            "sampler_name": "euler_a",
            "scheduler": "normal",
            "denoise": 1,
        },
        "class_type": "KSampler",
    },
    "10": {
        "inputs": {
            "width": 512,
            "height": 512,
            "batch_size": 1,
        },
        "class_type": "Empty Latent Image",
    },
    "11": {
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": ["6", 0],
        },
        "class_type": "Save Image",
    },
}

def start_comfyui():
    """Starts ComfyUI in a subprocess."""
    try:
        if os.name == 'nt': #windows
            subprocess.Popen(["python", "main.py"], cwd=COMFYUI_PATH)
        else: #linux or mac
            subprocess.Popen(["python3", "main.py"], cwd=COMFYUI_PATH)

        time.sleep(5)  # Give ComfyUI time to start
        st.success("ComfyUI started successfully!")
    except Exception as e:
        st.error(f"Failed to start ComfyUI: {e}")

def queue_prompt(prompt):
    """Queues a prompt to the ComfyUI API."""
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = requests.post(url=API_URL, data=data)
    return json.loads(req.text)

def get_image(prompt_id):
    """Retrieves the generated image from the ComfyUI API."""
    output_images = []
    while True:
        history = requests.get(url=HISTORY_URL + prompt_id).json()
        if prompt_id in history:
            for node_id in history[prompt_id]['outputs']:
                if "images" in history[prompt_id]['outputs'][node_id]:
                    for image in history[prompt_id]['outputs'][node_id]['images']:
                        image_data = requests.get(url=f"http://127.0.0.1:8188/view?filename={image['filename']}&subfolder={image['subfolder']}&type={image['type']}").content
                        output_images.append(image_data)
            break
        time.sleep(1)
    return output_images

def main():
    """Main Streamlit application."""
    st.title("ComfyUI Streamlit Interface")

    if st.button("Start ComfyUI"):
        start_comfyui()

    prompt_text = st.text_area("Enter your prompt:", "A beautiful landscape")

    if st.button("Generate Image"):
        with st.spinner("Generating image..."):
            WORKFLOW["3"]["inputs"]["text"] = prompt_text #update prompt
            prompt_id = queue_prompt(WORKFLOW)['prompt_id']
            output_images = get_image(prompt_id)
            if output_images:
                for img_data in output_images:
                    st.image(img_data, caption="Generated Image")
            else:
                st.error("Failed to generate image.")

if __name__ == "__main__":
    main()