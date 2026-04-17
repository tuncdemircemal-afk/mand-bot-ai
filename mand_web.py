import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
import uuid
from streamlit_mic_recorder import mic_recorder

# ==========================================
# ⚙️ CONFIGURATION & SECURITY
# ==========================================
API_KEY = "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"
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# ==========================================
# 🧠 SESSION MANAGEMENT
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "user_name" not in st.session_state: st.session_state.user_name = "Guest"
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "A1"
if "last_fix" not in st.session_state: st.session_state.last_fix = ""
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None
if "is_speaking" not in st.session_state: st.session_state.is_speaking = False

# ==========================================
# 🎨 UI & ROBOT ANIMATION (CSS)
# ==========================================
st.set_page_config(page_title="AIVA | Intelligent Mentor", page_icon="🤖", layout="wide")

# Robotun ağzını oynatan sihirli CSS burası kanka
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    
    /* Robot Kafa Konteynırı */
    .robot-container {
        display: flex; justify-content: center; align-items: center;
        flex-direction: column; padding: 20px;
    }
    
    .robot-head {
        width: 150px; height: 150px;
        background: #1e293b; border: 4px solid #3b82f6;
        border-radius: 30px; position: relative;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Gözler */
    .eye {
        width: 30px; height: 10px;
        background: #60a5fa; position: absolute; top: 50px;
        border-radius: 5px; box-shadow: 0 0 10px #60a5fa;
    }
    .eye.left { left: 25px; }
    .eye.right { right: 25px; }
    
    /* AĞIZ - Konuşma Animasyonu */
    .mouth {
        width: 60px; height: 8px;
        background: #60a5fa; position: absolute; bottom: 35px; left: 45px;
        border-radius: 10px; transition: all 0.2s;
    }
    
    /* Konuşma sırasında tetiklenen class */
    .talking {
        animation: speech 0.3s infinite alternate;
    }
    
    @keyframes speech {
        0% { height: 8px; bottom: 35px; }
        100% { height: 25px; bottom: 25px; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🎙️ AUDIO & AI LOGIC
# ==========================================
def get_audio_bytes(text):
    if text:
        try:
            tts = gTTS(text=text, lang='en')
            filename = f"s_{uuid.uuid4().hex}.mp3"
            tts.save(filename)
            with open(filename, "rb") as f: data = f.read()
            os.remove(filename)
            return data
        except: return None
    return None

def fetch_response(user_input):
    sys_msg = (
        f"You are AIVA, a professional English Language Mentor. "
        f"User: {st.session_state.user_name}. Level: {st.session_state.level}. "
        "STRICT GUIDELINES: Keep your [Answer] part very CONCISE (1-2 short sentences). "
        "Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
    )
    try:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant", temperature=0.1 
        )
        content = response.choices[0].message.content
        ans, fix = content, ""
        if "|" in content:
            parts = content.split("|")
            ans = parts[1].strip() if len(parts) > 1 else content
            fix = parts[2].replace("[Fix:", "").replace("]", "").strip() if len(parts) > 2 else ""
        return ans, fix
    except: return "I'm having trouble connecting.", ""

# ==========================================
# 🤖 ROBOT DISPLAY LOGIC
# ==========================================
# Eğer bot konuşuyorsa (audio_queue doluysa) 'talking' class'ını ekliyoruz
talking_class = "talking" if st.session_state.is_speaking else ""

st.markdown(f"""
    <div class="robot-container">
        <div class="robot-head">
            <div class="eye left"></div>
            <div class="eye right"></div>
            <div class="mouth {talking_class}"></div>
        </div>
        <h3 style='margin-top: 15px;'>AIVA Intelligence</h3>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 💬 CHAT INTERFACE
# ==========================================
with st.sidebar:
    st.title("AIVA CORE")
    st.session_state.level = st.select_slider("Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None
    st.session_state.is_speaking = False # Ses çalmaya başlayınca animasyon durmasın diye bunu manuel yönetebilirsin

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

input_col, mic_col = st.columns([5, 1])
with mic_col:
    audio_data = mic_recorder(start_prompt="Speak", stop_prompt="Process", key='voice_input')
with input_col:
    user_query = st.chat_input("Message AIVA...")

# --- PROCESSING ---
final_text = None 
if audio_data and st.session_state.last_audio_id != audio_data['id']:
    st.session_state.last_audio_id = audio_data['id']
    with st.spinner("Analyzing..."):
        try:
            with open("raw.wav", "wb") as f: f.write(audio_data['bytes'])
            with open("raw.wav", "rb") as f:
                transcription = client.audio.transcriptions.create(file=("raw.wav", f.read()), model="whisper-large-v3", response_format="text")
            final_text = transcription
        except: st.error("Audio error.")
elif user_query:
    final_text = user_query

if final_text:
    st.session_state.messages.append({"role": "user", "content": final_text})
    with st.chat_message("user"): st.markdown(final_text)
    
    with st.chat_message("assistant"):
        answer, correction = fetch_response(final_text)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_fix = correction
        
        # Animasyonu tetikle kanka
        st.session_state.is_speaking = True 
        st.session_state.audio_queue = get_audio_bytes(answer)
    st.rerun()

if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.info(f"📊 Mentor's Note: {st.session_state.last_fix}")
