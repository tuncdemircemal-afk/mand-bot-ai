import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import uuid
import hashlib
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
API_KEY = "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"
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# ==========================================
# 🧠 SESSION STATE (Kritik Alan)
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "B1"
if "last_fix" not in st.session_state: st.session_state.last_fix = ""
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ==========================================
# 🎨 UI DESIGN
# ==========================================
st.set_page_config(page_title="AIVA | AI Mentor", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stSidebar { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #3b82f6; margin-bottom: 15px;
    }
    .aiva-avatar {
        width: 80px; height: 80px; background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5); font-size: 40px;
    }
    /* Mikrofon alanını sabitlemek için */
    .mic-container { background: #1e293b; padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🛠️ FUNCTIONS
# ==========================================
def get_audio_bytes(text):
    if not text: return None
    try:
        tts = gTTS(text=text, lang='en')
        filename = f"s_{uuid.uuid4().hex}.mp3"
        tts.save(filename)
        with open(filename, "rb") as f: data = f.read()
        os.remove(filename)
        return data
    except: return None

def fetch_response(user_input):
    sys_msg = (
        f"You are AIVA, a professional English Mentor. Level: {st.session_state.level}. "
        "Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
    )
    try:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant", temperature=0.1 
        )
        content = response.choices[0].message.content
        if "|" in content:
            parts = content.split("|")
            ans = parts[1].strip()
            fix = parts[2].replace("[Fix:", "").replace("]", "").strip()
            return ans, fix
        return content, "None"
    except: return "Connection error.", "None"

# ==========================================
# 📊 SIDEBAR & HEADER
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🤖 AIVA CORE</h2>", unsafe_allow_html=True)
    st.markdown(f"""<div class="metric-card">📝 {st.session_state.stats['total_words']} Words<br>⚠️ {st.session_state.stats['mistakes']} Mistakes</div>""", unsafe_allow_html=True)
    st.session_state.level = st.select_slider("Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    if st.button("🔄 Reset"):
        st.session_state.messages = []; st.session_state.stats = {"total_words": 0, "mistakes": 0}; st.rerun()

st.markdown("<div style='text-align: center;'><div class='aiva-avatar'>🌐</div><h3>AIVA Intelligence</h3></div>", unsafe_allow_html=True)

# ==========================================
# 💬 CHAT HISTORY
# ==========================================
chat_container = st.container()
with chat_container:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

# Ses kuyrukta bekliyorsa çal
if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# ==========================================
# 🎙️ INPUT AREA (Mikrofon Sabitleme)
# ==========================================
st.divider()
col1, col2 = st.columns([1, 4])

with col1:
    st.write("🎙️ Tap to Speak")
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e24a4a",
        neutral_color="#60a5fa",
        icon_size="2x",
        pause_threshold=3.0, # 3 Saniye Sessizlik Bekleme
        key="main_mic" # Sabit anahtar
    )

with col2:
    user_query = st.chat_input("Or type your message...")

# --- PROCESS LOGIC ---
final_text = None

if audio_bytes:
    current_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != current_hash:
        st.session_state.last_audio_hash = current_hash
        with st.spinner("Processing..."):
            try:
                with open("temp.wav", "wb") as f: f.write(audio_bytes)
                with open("temp.wav", "rb") as f:
                    transcription = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3", response_format="text")
                final_text = transcription
            except: st.error("Mic error!")

if user_query:
    final_text = user_query

if final_text:
    st.session_state.stats["total_words"] += len(final_text.split())
    st.session_state.messages.append({"role": "user", "content": final_text})
    
    answer, correction = fetch_response(final_text)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_fix = correction
    if correction and "None" not in correction: 
        st.session_state.stats["mistakes"] += 1
    
    st.session_state.audio_queue = get_audio_bytes(answer)
    st.rerun()

if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.warning(f"📊 Mentor's Note: {st.session_state.last_fix}")
