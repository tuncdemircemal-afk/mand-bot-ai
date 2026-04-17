import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import uuid
import hashlib # Yeni sesleri ayırt etmek için
from audio_recorder_streamlit import audio_recorder # Yeni kütüphane
from streamlit_mic_recorder import mic_recorder # Eskisi de kalsın ne olur ne olmaz
.
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
if "is_speaking" not in st.session_state: st.session_state.is_speaking = False
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ==========================================
# 🎨 UI & ROBOT ANIMATION
# ==========================================
st.set_page_config(page_title="AIVA | Intelligent Mentor", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stSidebar { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px;
    }
    .robot-container { display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 10px; }
    .robot-head {
        width: 140px; height: 140px; background: #1e293b; border: 4px solid #3b82f6;
        border-radius: 30px; position: relative; box-shadow: 0 0 25px rgba(59, 130, 246, 0.5);
    }
    .eye { width: 30px; height: 8px; background: #60a5fa; position: absolute; top: 45px; border-radius: 5px; box-shadow: 0 0 15px #60a5fa; }
    .eye.left { left: 25px; } .eye.right { right: 25px; }
    .mouth { width: 50px; height: 6px; background: #60a5fa; position: absolute; bottom: 35px; left: 45px; border-radius: 10px; transition: all 0.2s; }
    .talking { animation: speech 0.25s infinite alternate; }
    @keyframes speech { 0% { height: 6px; bottom: 35px; } 100% { height: 25px; bottom: 25px; } }
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
        f"You are AIVA, a professional English Mentor. User: {st.session_state.user_name}. Level: {st.session_state.level}. "
        "STRICT: Keep [Answer] BRIEF (1-2 sentences). Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
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
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>AIVA CORE</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="metric-card">
            <small style='color: #94a3b8;'>SESSION ANALYTICS</small><br>
            <span style='font-size: 1.1em;'>📝 {st.session_state.stats['total_words']} Words</span><br>
            <span style='font-size: 1.1em; color: #fbbf24;'>⚠️ {st.session_state.stats['mistakes']} Feedback Points</span>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.level = st.select_slider("Coaching Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    if st.button("Initialize New Session", use_container_width=True):
        st.session_state.messages = []; st.session_state.stats = {"total_words": 0, "mistakes": 0}; st.session_state.last_fix = ""; st.rerun()

# ==========================================
# 🤖 ROBOT DISPLAY
# ==========================================
talking_class = "talking" if st.session_state.is_speaking else ""
st.markdown(f"""
    <div class="robot-container">
        <div class="robot-head"><div class="eye left"></div><div class="eye right"></div><div class="mouth {talking_class}"></div></div>
        <h3 style='margin-top: 10px;'>AIVA Intelligence</h3>
        <small style='color: #10b981;'>• Hands-Free Mode Active</small>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None
    st.session_state.is_speaking = False

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

st.divider()

# ==========================================
# 🎙️ HANDS-FREE RECORDING (SUDE'NİN İSTEDİĞİ)
# ==========================================
st.write("Sude için Sahne Modu: Mikrofona bas, konuş ve bekle...")
audio_bytes = audio_recorder(
    text="Click to speak...",
    recording_color="#e24a4a",
    neutral_color="#60a5fa",
    icon_size="2x",
)

user_query = st.chat_input("Veya buraya yaz...")

# --- PROCESSING ---
final_text = None 

if audio_bytes:
    # Aynı sesi tekrar işlememek için hash kontrolü yapıyoruz
    current_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != current_hash:
        st.session_state.last_audio_hash = current_hash
        with st.spinner("AIVA is listening..."):
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
        st.session_state.is_speaking = True 
        st.session_state.audio_queue = get_audio_bytes(answer)
    st.rerun()

if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.markdown(f"<div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px dashed #eab308; margin-top: 10px; color: #fbbf24;'><b>📊 Mentor's Note:</b><br>{st.session_state.last_fix}</div>", unsafe_allow_html=True)
