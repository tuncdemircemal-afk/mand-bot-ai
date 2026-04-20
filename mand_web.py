import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import uuid
import hashlib
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ GÜVENLİ YAPILANDIRMA
# ==========================================
# Kanka API Key'i buradan çekecek, Streamlit Secrets'a eklemeyi unutma!
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    API_KEY = "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" # Yedek anahtar

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
# 🎨 UI DESIGN
# ==========================================
st.set_page_config(page_title="AIVA | AI Mentor", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .metric-card {
        background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #3b82f6; margin-bottom: 10px;
    }
    .aiva-avatar {
        width: 60px; height: 60px; background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5); font-size: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🛠️ FUNCTIONS
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
        f"You are AIVA, a professional English Mentor. Level: {st.session_state.level}. "
        "Talk naturally. Format: Mood: [mood] | [Your English Answer] | [Correction for user if any, else None]"
    )
    try:
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant", 
            temperature=0.6,
            timeout=10.0 # Bağlantı hatasını önlemek için 10 sn limit
        )
        content = response.choices[0].message.content
        if "|" in content:
            parts = content.split("|")
            ans = parts[1].strip().replace("[Answer]", "").strip("[] ")
            fix = parts[2].strip().replace("[Fix:", "").strip("[] ")
            return ans, fix
        return content.strip(), "None"
    except Exception as e:
        return "I'm having a little connection trouble. Can you say that again?", "None"

# ==========================================
# 📊 SIDEBAR & INTERFACE
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='text-align: center;'>🤖 AIVA CORE</h3>", unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card">📝 {st.session_state.stats["total_words"]} Words<br>⚠️ {st.session_state.stats["mistakes"]} Mistakes</div>', unsafe_allow_html=True)
    st.session_state.level = st.select_slider("Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    if st.button("🔄 Reset"):
        st.session_state.messages = []; st.session_state.stats = {"total_words": 0, "mistakes": 0}; st.rerun()

st.markdown("<div style='text-align: center;'><div class='aiva-avatar'>🌐</div><h3>AIVA Intelligence</h3></div>", unsafe_allow_html=True)

# Chat History
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# ==========================================
# 🎙️ INPUT AREA
# ==========================================
st.divider()
c1, c2 = st.columns([1, 4])
with c1:
    audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="stable_mic")
with c2:
    user_query = st.chat_input("Message AIVA...")

# Logic
final_text = None
if audio_bytes:
    current_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != current_hash:
        st.session_state.last_audio_hash = current_hash
        with st.spinner("AIVA is listening..."):
            try:
                with open("temp.wav", "wb") as f: f.write(audio_bytes)
                with open("temp.wav", "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        file=("temp.wav", f.read()), 
                        model="whisper-large-v3", 
                        response_format="text"
                    )
                final_text = transcription
            except Exception as e:
                st.error("Connection lost. Please check your internet or try text input.")
elif user_query:
    final_text = user_query

if final_text:
    st.session_state.stats["total_words"] += len(final_text.split())
    st.session_state.messages.append({"role": "user", "content": final_text})
    
    with st.spinner("Thinking..."):
        answer, correction = fetch_response(final_text)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_fix = correction
        if correction and "None" not in correction: 
            st.session_state.stats["mistakes"] += 1
        st.session_state.audio_queue = get_audio_bytes(answer)
    
    st.rerun()

if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.info(f"💡 {st.session_state.last_fix}")
