import streamlit as st
import subprocess
import time
import requests
import json
import os
import threading
import re

# --- Ollama Comic Generator ---

# Startup prompt
STARTUP_PROMPT = "Hello! I'm your comic generator. Give me a topic, and I'll create a fun 4-panel comic strip!"

# Function to generate comic script using Ollama CLI
def generate_comic(prompt):
    model = "comiccrafter"  # Use your custom model or "mistral"
    full_prompt = f"Generate a 4-panel comic strip script about: {prompt}. Please format it as 'Panel 1: [description of visual scene] - [character dialogue/text]', and so on for all 4 panels. Make each panel concise and visual."

    # Call Ollama CLI using 'run' instead of 'chat'
    result = subprocess.run(
        ["ollama", "run", model],
        input=full_prompt,
        text=True,
        capture_output=True
    )

    if result.returncode == 0:
        return result.stdout.strip()
    else:
        error_msg = result.stderr if result.stderr else "Unknown error occurred."
        return f"Error generating comic: {error_msg}"

# Function to parse comic script into panels
def parse_comic_script(script):
    # Regular expression to find panel descriptions
    panels = []
    panel_regex = r"Panel (\d+):(.*?)(?=Panel \d+:|$)"
    matches = re.findall(panel_regex, script, re.DOTALL)
    
    for match in matches:
        panel_num, content = match
        # Split the content into visual description and dialogue if possible
        parts = content.split('-', 1)
        if len(parts) > 1:
            visual = parts[0].strip()
            dialogue = parts[1].strip()
        else:
            visual = content.strip()
            dialogue = ""
        
        panels.append({
            "number": int(panel_num),
            "visual": visual,
            "dialogue": dialogue,
            "prompt": visual  # Use visual description as image generation prompt
        })
    
    # If parsing failed or didn't find enough panels, fallback to simple splitting
    if len(panels) < 4:
        # Simple fallback: try to split by newlines and look for Panel keywords
        lines = script.split('\n')
        current_panel = None
        
        for line in lines:
            if line.strip():
                if line.lower().startswith("panel"):
                    try:
                        panel_num = int(re.search(r"Panel (\d+)", line, re.IGNORECASE).group(1))
                        content = line.split(':', 1)[1].strip() if ':' in line else ""
                        current_panel = {
                            "number": panel_num,
                            "visual": content,
                            "dialogue": "",
                            "prompt": content
                        }
                        panels.append(current_panel)
                    except:
                        # If we can't extract a panel number, just continue
                        pass
                elif current_panel and not line.startswith("Panel"):
                    # Append to current panel's content
                    current_panel["dialogue"] += " " + line.strip()
                    current_panel["prompt"] += " " + line.strip()
    
    # If we still don't have 4 panels, create empty ones
    while len(panels) < 4:
        panels.append({
            "number": len(panels) + 1,
            "visual": "Comic scene",
            "dialogue": "Missing panel content",
            "prompt": "Comic scene"
        })
    
    # Sort panels by number
    panels.sort(key=lambda x: x["number"])
    return panels[:4]  # Limit to 4 panels

# --- ComfyUI Image Generator ---

# ComfyUI Configuration
COMFYUI_PATH = "C:\\ComfyUI_windows_portable\\ComfyUI"  # Update with your ComfyUI directory
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

def get_image(prompt_id):
    """Retrieves the generated image from the ComfyUI API."""
    output_images = []
    start_time = time.time()
    timeout = 3600  # 1 hour timeout
    
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

# Function to generate a single panel image
def generate_panel_image(panel_prompt, workflow_json, config):
    """Generates an image for a single comic panel."""
    # Update workflow with panel-specific parameters
    for node_id, node in workflow_json.items():
        if node["class_type"] == "Empty Latent Image":
            node["inputs"]["width"] = config["width"]
            node["inputs"]["height"] = config["height"]
        elif node["class_type"] == "KSampler":
            node["inputs"]["steps"] = config["steps"]
            node["inputs"]["cfg"] = config["cfg"]
            node["inputs"]["seed"] = config["seed"] + int(panel_prompt["number"])  # Use different seed for each panel
            node["inputs"]["sampler_name"] = config["sampler"]
            node["inputs"]["scheduler"] = config["scheduler"]
        elif node["class_type"] == "Load Checkpoint":
            node["inputs"]["ckpt_name"] = config["model_path"]

    # Create comic-specific prompt
    comic_style_prompt = f"comic panel, cartoon style, {panel_prompt['prompt']}"
    
    # Update prompts in workflow
    updated_workflow = update_workflow_with_prompt(workflow_json, comic_style_prompt)
    
    # Queue the prompt
    result = queue_prompt(updated_workflow)
    if not result or "prompt_id" not in result:
        return None
    
    prompt_id = result["prompt_id"]
    
    # Get generated image
    output_images = get_image(prompt_id)
    if output_images:
        return output_images[0]  # Return first image
    return None

# --- Combined Streamlit App ---

def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="Comic Strip Generator", layout="wide")
    st.title("Comic Strip Generator 🎭")
    st.write(STARTUP_PROMPT)

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
        width = st.slider("Width", 256, 1024, 512, 64)  # Reduced default size for comic panels
        height = st.slider("Height", 256, 1024, 512, 64)  # Reduced default size for comic panels
        
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
        
        # Comic display options
        st.divider()
        st.subheader("Comic Display Options")
        text_height = st.slider("Text Box Height", 50, 200, 100)
        border_width = st.slider("Panel Border Width", 1, 10, 2)
        border_color = st.color_picker("Border Color", "#000000")

    # User input
    user_prompt = st.text_input("Enter a comic topic or scenario:")

    # Generate and display comic strip
    if st.button("Generate Comic Strip"):
        if user_prompt:
            # Generate comic script
            with st.spinner("Generating comic script..."):
                comic_script = generate_comic(user_prompt)
                
                # Parse script into panels
                panels = parse_comic_script(comic_script)
                
                # Display the full script in an expander
                with st.expander("Generated Comic Script"):
                    st.text_area("Full Script", comic_script, height=200)

            # Check if ComfyUI is running
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
            
            # Configuration for image generation
            config = {
                "model_path": model_path,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed if seed != 0 else int(time.time()),
                "sampler": sampler,
                "scheduler": scheduler
            }
            
            # Generate images for each panel
            generated_panels = []
            for panel in panels:
                with st.spinner(f"Generating panel {panel['number']}..."):
                    # Display placeholder while image is being generated
                    panel_placeholder = st.empty()
                    panel_placeholder.text(f"Generating panel {panel['number']}...")
                    
                    # Generate image for this panel
                    panel_image = generate_panel_image(panel, workflow_json, config)
                    if panel_image:
                        panel["image"] = panel_image
                        generated_panels.append(panel)
                        panel_placeholder.empty()
                    else:
                        st.error(f"Failed to generate image for panel {panel['number']}")
            
            # Display the comic strip in the desired format
            if generated_panels:
                st.subheader("Generated Comic Strip")
                
                # Use columns for panel layout
                cols = st.columns(min(4, len(generated_panels)))
                
                for i, panel in enumerate(generated_panels):
                    with cols[i % len(cols)]:
                        # Create panel container with border
                        st.markdown(f"""
                        <div style="border: {border_width}px solid {border_color}; margin: 5px; padding: 0;">
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display image
                        st.image(
                            panel["image"]["data"], 
                            caption=f"Panel {panel['number']}", 
                            use_column_width=True
                        )
                        
                        # Display text in a box below the image
                        st.markdown(f"""
                        <div style="
                            border: {border_width}px solid {border_color}; 
                            border-top: none;
                            padding: 10px; 
                            background-color: white; 
                            min-height: {text_height}px;
                            overflow-y: auto;
                            margin-bottom: 15px;
                            font-family: 'Comic Sans MS', cursive, sans-serif;
                        ">
                            {panel["dialogue"]}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Download button for the whole comic strip
                st.subheader("Download Options")
                # Here we would implement the download functionality
                st.info("Download functionality for complete comic will be implemented in future updates.")
                
                # Allow downloading individual panels
                for panel in generated_panels:
                    st.download_button(
                        f"Download Panel {panel['number']}",
                        data=panel["image"]["data"],
                        file_name=f"comic_panel_{panel['number']}_{panel['image']['filename']}",
                        mime=f"image/{panel['image']['type']}" if panel['image']['type'] != 'jpeg' else "image/jpg"
                    )
            else:
                st.error("Failed to generate any comic panels. Check the ComfyUI logs for errors.")
        else:
            st.warning("Please enter a topic to generate a comic!")

if __name__ == "__main__":
    main()