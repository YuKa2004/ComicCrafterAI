# 🎨 ComicCrafter  : A Next-Gen AI-Powered Comic Generation Tool 

# 1.Description

ComicCrafter is an AI-powered tool that helps users generate comics using text prompts and AI-generated illustrations.  
It combines Mistral for text processing and Flux.1 for image generation, wrapped in a Streamlit web app.

# 2.Features

Highlight key functionalities:

🖌 AI-generated comic panels

⚡ Fast and interactive web-based UI (built with Streamlit)

# 3.Installation

Step-by-step instructions:

Clone the repository
git clone https://github.com/yourusername/comiccrafter.git
cd comiccrafter

Dependencies
 1. [Python 3.8+](https://www.python.org/downloads/)

 2. pip

 3. Streamlit : ```pip install streamlit```

 4. [Ollama](https://ollama.com/) 

 5. [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
        [Custom GGUF node](https://github.com/city96/ComfyUI-GGUF)
        [Model name: flux1-dev-Q4_0.gguf](https://huggingface.co/city96/FLUX.1-dev-gguf/tree/main)
        [Encoder 1 :clipl](https://huggingface.co/comfyanonymous/flux_text_encoders/tree/main)
        [Encoder 2 :t5 encoder](https://huggingface.co/city96/t5-v1_1-xxl-encoder-gguf/tree/main)
        [VAE file](https://huggingface.co/black-forest-labs/FLUX.1-schnell/blob/main/ae.safetensors)
 6. Mistral model (for local text processing)
    - Download the Mistral model in ollama using the following command
    ```ollama run mistral```
 7. Flux.1 Dev GGUF model (for image generation)

Run the app
```streamlit run app.py```

# 4.Output
output for the prompt : world war 2 enemies turned to friends
![Screenshot 2025-04-02 230158](https://github.com/user-attachments/assets/73d2b9b6-0599-43d9-ac7e-f9bf1ad2274e)

# Video demonstration of the project: [youtube link](https://youtu.be/FxCLyE5Y0KA)



# 5.Architecture

![image](https://github.com/user-attachments/assets/e592eddb-20ac-4eeb-8446-652ea750acbd)


Frontend: Streamlit

AI Models: Mistral, Flux.1

Backend: Python

Deployment: Completely Local









