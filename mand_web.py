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
# 🧠 SESSION STATE
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "B1"
if "last_fix" not in st.session_state: st.session_state.last_fix = ""
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ==========================================
# 🎨 UI DESIGN (Clean & Mobile Friendly)
# ==========================================
st.set_page_config(page_title="AIVA AI", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .metric-card {
        background: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #3b82f6;
    }
    .aiva-header { text-align: center; padding: 10px; }
    /* Mobilde mikrofonun kaybolmaması için sabit alan */
    .mic-box { display: flex; justify-content: center; padding: 10px; background: #111827; border-radius: 50px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🛠️ CORE FUNCTIONS
# ==========================================
def get_audio_bytes(text):
    if not text or len(text) < 2: return None
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
        f"You are AIVA, a helpful English Mentor. Level: {st.session_state.level}. "
        "IMPORTANT: Talk naturally. Format: Mood: [mood] | [Your Answer] | [Correction or None]"
    )
    try:
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant", temperature=0.5
        )
        content = response.choices[0].message.content
        if "|" in content:
            parts = content.split("|")
            ans = parts[1].strip().replace("[Answer]", "").replace("[", "").replace("]", "")
            fix = parts[2].strip().replace("[Fix:", "").replace("]", "")
            return ans, fix
        return content, "None"
    except Exception as e:
        return f"System busy, please try again. ({str(e)[:20]})", "None"

# ==========================================
# 📱 INTERFACE
# ==========================================
with st.sidebar:
    st.markdown("### 🤖 AIVA STATS")
    st.markdown(f'<div class="metric-card">Words: {st.session_state.stats["total_words"]}<br>Mistakes: {st.session_state.stats["mistakes"]}</div>', unsafe_allow_html=True)
    st.session_state.level = st.select_slider("Coaching Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    if st.button("Reset Session"):
        st.session_state.messages = []; st.session_state.stats = {"total_words": 0, "mistakes": 0}; st.rerun()

st.markdown('<div class="aiva-header"><h1>🌐 AIVA</h1><p>AI Flight Instructor</p></div>', unsafe_allow_html=True)

# Chat Area
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# ==========================================
# 🎙️ INPUT AREA (Fixed Connection Logic)
# ==========================================
st.divider()
col_mic, col_text = st.columns([1, 4])

with col_mic:
    # Key ekleyerek Streamlit'in butonu kaybetmesini engelliyoruz
    audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="aiva_mic_stable")

with col_text:
    user_query = st.chat_input("Say something to AIVA...")

# --- PROCESSING ---
input_to_process = None

if audio_bytes:
    new_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != new_hash:
        st.session_state.last_audio_hash = new_hash
        try:
            with open("temp.wav", "wb") as f: f.write(audio_bytes)
            with open("temp.wav", "rb") as f:
                transcription = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3", response_format="text")
            if transcription and len(transcription) > 1:
                input_to_process = transcription
        except Exception as e:
            st.error("Check Mic Permissions!")

if user_query:
    input_to_process = user_query

if input_to_process:
    st.session_state.stats["total_words"] += len(input_to_process.split())
    st.session_state.messages.append({"role": "user", "content": input_to_process})
    
    answer, correction = fetch_response(input_to_process)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_fix = correction
    if correction and "None" not in correction: st.session_state.stats["mistakes"] += 1
    
    st.session_state.audio_queue = get_audio_bytes(answer)
    st.rerun()

if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.info(f"💡 Mentor: {st.session_state.last_fix}")
