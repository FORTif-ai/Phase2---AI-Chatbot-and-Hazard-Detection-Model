# 🛡️ Hazard Detection & AI Chatbot  

This project combines **computer vision** and **AI voice assistance** into a single web app.  
It’s designed to help detect hazards from images or video and let users issue commands using speech.  

---

## 🌟 What It Does  
- **Hazard Detection (YOLOv8)**  
  - Upload an image or use a webcam/video  
  - Hazards are automatically detected and highlighted  

- **Voice Commands (Whisper)**  
  - Speak commands (e.g., schedule an event, trigger hazard detection)  
  - Speech is transcribed and processed by the chatbot pipeline  

- **Smart Chatbot**  
  - Delegates conversations to the right persona (e.g., based on user profile)  
  - Can connect to external tools like **Google Calendar** to create events  

- **Web Interface (Flask)**  
  - Simple homepage with navigation  
  - Upload images/audio directly from your browser  

---

## 🖼️ Demo Flow  
1. Go to the homepage  
2. Upload an image → see hazards marked  
3. Upload an audio file → get transcription & action (e.g., “Add doctor’s appointment tomorrow”)  
4. (Optional) Run in CLI mode to control via microphone  

---

## 📂 Tech Stack  
- **Flask** – web framework  
- **YOLOv8** – hazard detection (computer vision)  
- **Whisper** – speech-to-text  
- **Qdrant + LLMs** – persona-aware chatbot & delegation  
- **Google Calendar API** – event creation  

---

## 🚧 Status  
- Core features (hazard detection & voice transcription) are working  
- Chatbot pipeline and Google Calendar integration are functional but still experimental  
- Web templates are minimal (UI is very basic for now)  

---

## 🤝 Contributors  
Core Members and TPMs of the FORTif.ai: Assistant For Independent and Safe Senior Living.  
