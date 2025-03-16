# Intel Unnati Industrial Training Program  
## Documentation for ComicCrafter.AI  

**Overview**  
ComicCrafter AI is a generative AI-based comic generator that runs locally on edge devices. It generates a comic-style story based on input prompts given by the user.  

**Documented by:**  
G. Yuvraj Kashyap  

---

## Phases of Production  

### **Phase 1: LLM Story Generation using Prompting**  
**Requirements:**  
- Develop a module that uses Large Language Models (LLMs) to generate a coherent story based on the user’s prompt.  
- The story should be divided into four distinct parts: **Introduction**, **Storyline**, **Climax**, and **Moral**.  

**Proposed Plan:**  
- Use **DeepSeek R1 LLM** to generate a structured story divided into the four defined parts.  

**Skills Required:**  
- Running the DeepSeek model locally.  
- Fine-tuning the LLM for story generation in this specific format.  

---

### **Phase 2: Image Generation**  
**Requirements:**  
- Create a module that generates images corresponding to each part of the story using AI-based image generation tools.  
- Ensure that the images align with the narrative.  

**Proposed Plan:**  
- Use **Stable Diffusion** to generate images for each section of the story.  

**Skills Required:**  
- Running the Stable Diffusion model locally.  
- Fine-tuning Stable Diffusion to align with the generated story.  

---

### **Phase 3: Merging Story Prompts and Images**  
**Requirements:**  
- Develop a system to merge the generated text and images into a cohesive comic book format.  
- Ensure that the text and images are appropriately aligned and formatted.  

**Proposed Plan:**  
- Use the **Streamlit framework** to integrate text and images into a comic book format.  

**Skills Required:**  
- Streamlit development.  
- Basics of web design and Python programming.  

---

### **Phase 4: Integration into an App**  
**Requirements:**  
- Integrate the story generation, image generation, and merging modules into a single web application.  
- Ensure the app is user-friendly and can run efficiently on edge devices.  

**Comments:**  
- This phase will be implemented using **Streamlit**.  

**Knowledge Needed:**  
- Git basics  
- Python programming  
- Web design basics  
- Prompt engineering  

---

## Grading Parameters  
To be defined based on project evaluation criteria.  

---

## Implementation Plans  

### **Phase 1 Implementation**  
**Requirements:**  
- Develop a module that uses LLMs to generate a coherent story based on the user’s prompt.  
- The story should be divided into four distinct parts: **Introduction**, **Storyline**, **Climax**, and **Moral**.  

**Proposed Plan:**  
- Use **DeepSeek R1 LLM** to generate a story divided into **Introduction**, **Storyline**, **Climax**, and **Moral**.  

**Skills Required:**  
- Know-how to run the DeepSeek model locally.  
- Fine-tuning the LLM for story generation in this specific format.  

---

### **Phase 2: Image Generation**  
**Requirements:**  
- Create a module that generates images corresponding to each part of the story using AI-based image generation tools.  
- Ensure that the images align with the narrative.  

**Proposed Plan:**  
- Use **Stable Diffusion** to generate images.  

**Skills Required:**  
- Know-how to run the Stable Diffusion model locally.  
- Fine-tuning the LLM for story generation in this specific format.  

---

### **Phase 3: Merging Story Prompts and Images**  
**Requirements:**  
- Develop a system to merge the generated text and images into a cohesive comic book format.  
- Ensure that the text and images are appropriately aligned and formatted.  

**Proposed Plan:**  
- Use the **Streamlit framework** to integrate image and text.  

**Skills Required:**  
- Streamlit development.  
- Basics of web design and Python programming.  

---

### **Phase 4: Integration into an App**  
**Requirements:**  
- Integrate the story generation, image generation, and merging modules into a single web application.  
- Ensure the app is user-friendly and can run efficiently on edge devices.  

**Comments:**  
- Will be taken care of by **Streamlit**.  

**Knowledge Needed:**  
- Git basics  
- Python  
- Web design basics  
- Prompt engineering  

---

## Grading Parameters  
To be defined based on project evaluation criteria.  
