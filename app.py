import streamlit as st
import subprocess

# Startup prompt
STARTUP_PROMPT = "Hello! I'm your comic  generator. Give me a topic, and I'll create a fun 4-panel comic strip!"

# Streamlit UI
st.title("Comic Strip Generator 🎭")
st.write(STARTUP_PROMPT)

# User input
user_prompt = st.text_input("Enter a comic topic or scenario:")

# Function to generate comic script using Ollama CLI
def generate_comic(prompt):
    model = "comiccrafter"  # Use your custom model or "mistral"
    full_prompt = f"Generate a 4-panel comic strip script about: {prompt}"

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

# Generate and display comic script
if st.button("Generate Comic"):
    if user_prompt:
        comic_script = generate_comic(user_prompt)
        st.text_area("Generated Comic Script:", comic_script, height=200)
    else:
        st.warning("Please enter a topic to generate a comic!")
