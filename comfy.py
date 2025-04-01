import subprocess
import time
import requests
import json
import streamlit as st
import os
import base64
from io import BytesIO
import threading

# ComfyUI Configuration
COMFYUI_PATH = "C:\ComfyUI_windows_portable\ComfyUI"  # Update with your ComfyUI directory
API_URL = "http://127.0.0.1:8188/prompt"
HISTORY_URL = "http://127.0.0.1:8188/history/"
UPLOAD_URL = "http://127.0.0.1:8188/upload/image"
CLIENT_ID = str(time.time())
POLL_INTERVAL = 0.5  # Seconds between status checks

# Default models for Flux.1
DEFAULT_MODEL = "flux1-dev-Q4_0.gguf"
T5_ENCODER = "t5-gguf-encoder"  # Update with your actual T5 encoder name
CLIP_ENCODER = "clip-l-encoder"  # Update with your actual CLIP-L encoder name

# ComfyUI server status
comfyui_process = None
server_running = False

def load_custom_workflow(file_path=None):
    """Load custom workflow from a JSON file or return the default workflow."""
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Failed to load workflow: {e}")
            return None
    else:
        # Default workflow optimized for Flux.1 with both encoders
        return {
            "1": {
                "class_type": "Load Checkpoint",
                "inputs": {
                    "ckpt_name": DEFAULT_MODEL
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "A beautiful landscape",
                    "clip": ["1", 1]  # CLIP-L encoder output from checkpoint
                }
            },
            "3": {
                "class_type": "T5TextEncode",
                "inputs": {
                    "text": "A beautiful landscape",
                    "t5": ["1", 3]  # T5 encoder output from checkpoint
                }
            },
            "4": {
                "class_type": "Empty Latent Image",
                "inputs": {
                    "width": 768,
                    "height": 768,
                    "batch_size": 1
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["7", 0],
                    "latent_image": ["4", 0],
                    "seed": 0,
                    "steps": 30,
                    "cfg": 7.5,
                    "sampler_name": "euler_a",
                    "scheduler": "normal",
                    "denoise": 1.0
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "ugly, bad quality, blurry, distorted",
                    "clip": ["1", 1]
                }
            },
            "8": {
                "class_type": "Save Image",
                "inputs": {
                    "filename_prefix": "flux1_",
                    "images": ["6", 0]
                }
            }
        }

def start_comfyui():
    """Starts ComfyUI in a subprocess."""
    global comfyui_process, server_running
    
    if server_running:
        st.info("ComfyUI is already running.")
        return
    
    try:
        if os.name == 'nt':  # Windows
            comfyui_process = subprocess.Popen(["python", "main.py"], cwd=COMFYUI_PATH)
        else:  # Linux or Mac
            comfyui_process = subprocess.Popen(["python3", "main.py"], cwd=COMFYUI_PATH)
        
        # Check if server is up
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 second timeout
            try:
                requests.get("http://127.0.0.1:8188/", timeout=1)
                server_running = True
                st.success("ComfyUI started successfully!")
                return
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        st.warning("ComfyUI started but may not be fully initialized. Proceed with caution.")
        server_running = True
    except Exception as e:
        st.error(f"Failed to start ComfyUI: {e}")

def stop_comfyui():
    """Stops the ComfyUI subprocess."""
    global comfyui_process, server_running
    if comfyui_process:
        comfyui_process.terminate()
        try:
            comfyui_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            comfyui_process.kill()
        comfyui_process = None
        server_running = False
        st.success("ComfyUI has been shut down.")
    else:
        st.info("No ComfyUI process to stop.")

def check_server_status():
    """Checks if the ComfyUI server is running."""
    try:
        response = requests.get("http://127.0.0.1:8188/", timeout=1)
        return response.status_code == 200
    except:
        return False

def queue_prompt(prompt):
    """Queues a prompt to the ComfyUI API."""
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    try:
        req = requests.post(url=API_URL, data=data)
        return json.loads(req.text)
    except requests.exceptions.RequestException as e:
        st.error(f"API error: {e}")
        return None

def upload_image(image_data):
    """Uploads an image to ComfyUI."""
    try:
        response = requests.post(
            UPLOAD_URL,
            files={"image": image_data},
            data={"overwrite": "true"}
        )
        return json.loads(response.content)
    except Exception as e:
        st.error(f"Failed to upload image: {e}")
        return None

def get_image(prompt_id):
    """Retrieves the generated image from the ComfyUI API."""
    output_images = []
    start_time = time.time()
    timeout = 3600  # 5 minutes timeout
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while time.time() - start_time < timeout:
        try:
            history = requests.get(url=HISTORY_URL + prompt_id, timeout=5).json()
            
            # Update progress if available
            if prompt_id in history and "outputs" in history[prompt_id]:
                if "progress" in history[prompt_id]:
                    progress = history[prompt_id]["progress"]
                    progress_bar.progress(progress)
                    status_text.text(f"Generation progress: {progress*100:.1f}%")
                
                # Check if generation is complete
                for node_id in history[prompt_id]['outputs']:
                    if "images" in history[prompt_id]['outputs'][node_id]:
                        for image in history[prompt_id]['outputs'][node_id]['images']:
                            image_url = f"http://127.0.0.1:8188/view?filename={image['filename']}&subfolder={image['subfolder']}&type={image['type']}"
                            try:
                                image_data = requests.get(url=image_url, timeout=5).content
                                output_images.append({
                                    "data": image_data,
                                    "filename": image['filename'],
                                    "subfolder": image.get('subfolder', ''),
                                    "type": image.get('type', '')
                                })
                            except requests.exceptions.RequestException:
                                continue
                        
                        progress_bar.progress(1.0)
                        status_text.text("Generation complete!")
                        return output_images
            
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            st.warning(f"Error checking generation status: {e}")
            time.sleep(POLL_INTERVAL * 2)  # Back off on errors
    
    status_text.text("Generation timed out!")
    return output_images

def update_workflow_with_prompt(workflow, positive_prompt, negative_prompt=""):
    """Updates the workflow with the provided prompts."""
    # Make a deep copy to avoid modifying the original
    updated_workflow = json.loads(json.dumps(workflow))
    
    # Find and update CLIP text encode nodes
    for node_id, node in updated_workflow.items():
        if node["class_type"] == "CLIPTextEncode":
            # Check if this is likely a positive or negative prompt node
            if "negative" not in node_id.lower() and "neg" not in node_id.lower():
                if "ugly" not in node["inputs"].get("text", "").lower():  # Heuristic for positive prompt
                    node["inputs"]["text"] = positive_prompt
            else:  # Likely negative prompt
                if negative_prompt:
                    node["inputs"]["text"] = negative_prompt
        
        # Also update T5 encoders if present
        elif node["class_type"] == "T5TextEncode":
            node["inputs"]["text"] = positive_prompt
    
    return updated_workflow

def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="Flux.1 ComfyUI Interface", layout="wide")
    
    # Sidebar for configuration
    with st.sidebar:
        st.title("ComfyUI Controls")
        
        # Server control
        server_status = check_server_status()
        if server_status:
            st.success("ComfyUI server is running")
            if st.button("Stop ComfyUI"):
                stop_comfyui()
        else:
            st.error("ComfyUI server is not running")
            if st.button("Start ComfyUI"):
                start_thread = threading.Thread(target=start_comfyui)
                start_thread.start()
        
        st.divider()
        
        # Model configuration
        st.subheader("Model Configuration")
        model_path = st.text_input("Model Path", DEFAULT_MODEL)
        width = st.slider("Width", 256, 1024, 768, 64)
        height = st.slider("Height", 256, 1024, 768, 64)
        
        st.divider()
        
        # Sampling parameters
        st.subheader("Sampling Parameters")
        steps = st.slider("Steps", 10, 100, 30)
        cfg = st.slider("CFG Scale", 1.0, 20.0, 7.5, 0.5)
        seed = st.number_input("Seed (0 for random)", 0, 999999999, 0)
        sampler = st.selectbox("Sampler", ["euler_a", "euler", "dpm++_2m", "dpm++_sde", "ddim", "heun"])
        scheduler = st.selectbox("Scheduler", ["normal", "karras", "exponential", "sgm_uniform"])
        
        st.divider()
        
        # Workflow upload
        st.subheader("Custom Workflow")
        uploaded_workflow = st.file_uploader("Upload Custom Workflow (JSON)", type=["json"])
        
    # Main area
    st.title("Flux.1 Image Generator")
    
    # Prompt inputs
    col1, col2 = st.columns([3, 1])
    with col1:
        positive_prompt = st.text_area("Positive Prompt", "A beautiful landscape, detailed, high quality, 4k, cinematic lighting")
    with col2:
        negative_prompt = st.text_area("Negative Prompt", "ugly, bad quality, blurry, distorted, deformed")
    
    # Image input for img2img (optional)
    st.subheader("Input Image (Optional)")
    input_image = st.file_uploader("Upload an image for img2img", type=["png", "jpg", "jpeg"])
    
    if st.button("Generate Image", use_container_width=True):
        if not check_server_status():
            st.error("ComfyUI server is not running. Please start it first.")
            return
            
        # Load workflow
        if uploaded_workflow:
            try:
                workflow_json = json.load(uploaded_workflow)
                st.success("Custom workflow loaded successfully")
            except Exception as e:
                st.error(f"Failed to load workflow: {e}")
                workflow_json = load_custom_workflow()
        else:
            workflow_json = load_custom_workflow()
        
        if not workflow_json:
            st.error("No workflow available. Please upload a valid workflow or fix the default workflow.")
            return
            
        # Update workflow with parameters
        for node_id, node in workflow_json.items():
            # Update Empty Latent Image dimensions
            if node["class_type"] == "Empty Latent Image":
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height
                
            # Update KSampler parameters
            elif node["class_type"] == "KSampler":
                node["inputs"]["steps"] = steps
                node["inputs"]["cfg"] = cfg
                node["inputs"]["seed"] = seed
                node["inputs"]["sampler_name"] = sampler
                node["inputs"]["scheduler"] = scheduler
                
            # Update Load Checkpoint
            elif node["class_type"] == "Load Checkpoint":
                node["inputs"]["ckpt_name"] = model_path
        
        # Update prompts in workflow
        workflow_json = update_workflow_with_prompt(workflow_json, positive_prompt, negative_prompt)
        
        # Upload input image if provided (for img2img)
        if input_image:
            upload_result = upload_image(input_image.getvalue())
            if upload_result and "name" in upload_result:
                # Find potential img2img nodes and update them
                for node_id, node in workflow_json.items():
                    if node["class_type"] == "LoadImage":
                        node["inputs"]["image"] = upload_result["name"]
        
        # Queue the prompt
        with st.spinner("Submitting generation request..."):
            result = queue_prompt(workflow_json)
            if not result or "prompt_id" not in result:
                st.error("Failed to queue prompt. Check server connection.")
                return
                
            prompt_id = result["prompt_id"]
            st.info(f"Generation started with ID: {prompt_id}")
            
            # Get generated images
            output_images = get_image(prompt_id)
            
            if output_images:
                st.subheader("Generated Images")
                for idx, img in enumerate(output_images):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.image(img["data"], caption=f"Image {idx+1}: {img['filename']}")
                    with col2:
                        st.download_button(
                            f"Download Image {idx+1}",
                            data=img["data"],
                            file_name=img["filename"],
                            mime=f"image/{img['type']}" if img['type'] != 'jpeg' else "image/jpg"
                        )
            else:
                st.error("No images were generated. Check the ComfyUI logs for errors.")

if __name__ == "__main__":
    main()
