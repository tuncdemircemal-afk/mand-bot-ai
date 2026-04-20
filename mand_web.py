import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os, uuid, hashlib
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ CONFIG
# ==========================================
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    API_KEY = "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"

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# ==========================================
# 🧠 SESSION STATE
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ==========================================
# 🎨 UI & SIDEBAR
# ==========================================
st.set_page_config(page_title="AIVA AI", layout="wide")
st.markdown("<style>.stApp{background:#0b0f19;color:#eceff4;}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📊 AIVA CORE")
    st.markdown(f"**Words:** {st.session_state.stats['total_words']}")
    st.markdown(f"**Mistakes:** {st.session_state.stats['mistakes']}")
    if st.button("Reset Mission"):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0}
        st.rerun()

st.title("🌐 AIVA Intelligence")

# Chat History
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Audio Playback
if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# ==========================================
# 🎙️ INPUT AREA (Yazı + Mikrofon Geri Geldi)
# ==========================================
st.divider()
col1, col2 = st.columns([1, 5])

with col1:
    # Mikrofon Butonu
    audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="final_stable_mic")

with col2:
    # Yazı Girişi (Geri Geldi)
    user_query = st.chat_input("Type your message here...")

# --- LOGIC ---
final_text = None

# Ses İşleme
if audio_bytes:
    h = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != h:
        st.session_state.last_audio_hash = h
        try:
            with open("t.wav","wb") as f: f.write(audio_bytes)
            with open("t.wav","rb") as f:
                trans = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3", response_format="text")
                if trans: final_text = trans
        except:
            st.error("Mic Connection Error. Please use the chat box!")

# Yazı İşleme
if user_query:
    final_text = user_query

# Yanıt Üretme
if final_text:
    st.session_state.stats["total_words"] += len(final_text.split())
    st.session_state.messages.append({"role":"user","content":final_text})
    
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"system","content":"You are AIVA, a professional English mentor. Speak naturally and briefly."},{"role":"user","content":final_text}]
        )
        ans = res.choices[0].message.content
        st.session_state.messages.append({"role":"assistant","content":ans})
        
        # TTS (Sese Çevirme)
        tts = gTTS(text=ans, lang='en')
        tts.save("s.mp3")
        with open("s.mp3","rb") as f: st.session_state.audio_queue = f.read()
    except:
        st.error("AI is busy, try again!")
    
    st.rerun()
