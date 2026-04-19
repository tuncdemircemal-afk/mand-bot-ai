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
# 🧠 SESSION MANAGEMENT
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "user_name" not in st.session_state: st.session_state.user_name = "User"
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "B1"
if "last_fix" not in st.session_state: st.session_state.last_fix = ""
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ==========================================
# 🎨 UI DESIGN (CLASSIC VERSION)
# ==========================================
st.set_page_config(page_title="AIVA | AI Mentor", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stSidebar { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px;
        border: 1px solid #3b82f6;
    }
    
    .aiva-avatar {
        width: 100px; height: 100px;
        background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%; margin: 0 auto 15px;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); border: 2px solid #60a5fa;
        font-size: 50px; color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🎙️ AUDIO CORE
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
        f"You are AIVA, a professional English Mentor. User: {st.session_state.user_name}. Level: {st.session_state.level}. "
        "STRICT: Keep [Answer] concise (1-2 sentences). Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
    )
    try:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant", temperature=0.1 
        )
        content = response.choices[0].message.content
        ans, fix = content, "None"
        if "|" in content:
            parts = content.split("|")
            ans = parts[1].strip() if len(parts) > 1 else content
            fix = parts[2].replace("[Fix:", "").replace("]", "").strip() if len(parts) > 2 else "None"
        return ans, fix
    except: return "Connection error.", "None"

# ==========================================
# 📊 SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🤖 AIVA CORE</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="metric-card">
            <small style='color: #94a3b8;'>📊 SESSION ANALYTICS</small><br>
            <span style='font-size: 1.1em;'>📝 {st.session_state.stats['total_words']} Words</span><br>
            <span style='font-size: 1.1em; color: #fbbf24;'>⚠️ {st.session_state.stats['mistakes']} Mistakes</span>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.level = st.select_slider("Coaching Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.messages = []; st.session_state.stats = {"total_words": 0, "mistakes": 0}; st.session_state.last_fix = ""; st.rerun()

# ==========================================
# 🌐 INTERFACE
# ==========================================
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <div class="aiva-avatar">🌐</div>
        <h3 style='margin-bottom: 0;'>AIVA Intelligence</h3>
        <small style='color: #10b981;'>● System Online</small>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

st.divider()

# ==========================================
# 🎙️ HANDS-FREE INPUT (3s THRESHOLD)
# ==========================================
st.write("🎙️ Voice Input: Click to speak and wait 3 seconds of silence.")
audio_bytes = audio_recorder(
    text="Click to start",
    recording_color="#e24a4a",
    neutral_color="#60a5fa",
    icon_size="2x",
    pause_threshold=3.0
)
user_query = st.chat_input("Or type here...")

# --- PROCESSING ---
final_text = None 
if audio_bytes:
    current_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != current_hash:
        st.session_state.last_audio_hash = current_hash
        with st.spinner("Analyzing audio..."):
            try:
                with open("temp.wav", "wb") as f: f.write(audio_bytes)
                with open("temp.wav", "rb") as f:
                    transcription = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3", response_format="text")
                final_text = transcription
            except: st.error("Mic error.")
elif user_query:
    final_text = user_query

if final_text:
    st.session_state.stats["total_words"] += len(final_text.split())
    st.session_state.messages.append({"role": "user", "content": final_text})
    with st.chat_message("user"): st.markdown(final_text)
    with st.chat_message("assistant"):
        answer, correction = fetch_response(final_text)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_fix = correction
        if correction and "None" not in correction: st.session_state.stats["mistakes"] += 1
        st.session_state.audio_queue = get_audio_bytes(answer)
    st.rerun()

if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.markdown(f"<div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px dashed #eab308; margin-top: 10px; color: #fbbf24;'><b>📊 Mentor's Note:</b><br>{st.session_state.last_fix}</div>", unsafe_allow_html=True)
