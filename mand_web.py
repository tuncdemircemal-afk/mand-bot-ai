import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os, uuid, hashlib
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ ACİL DURUM YAPILANDIRMASI
# ==========================================
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    API_KEY = "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"

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# Session State Hazırlığı
for key in ["messages", "stats", "audio_queue", "last_audio_hash", "level"]:
    if key not in st.session_state:
        if key == "messages": st.session_state[key] = []
        elif key == "stats": st.session_state[key] = {"total_words": 0, "mistakes": 0}
        elif key == "level": st.session_state[key] = "B1"
        else: st.session_state[key] = None

# 🎨 UI
st.set_page_config(page_title="AIVA AI", page_icon="🌐")
st.markdown("<style>.stApp{background:#0b0f19;color:#eceff4;}</style>", unsafe_allow_html=True)

# 🛠️ GÜVENLİ FONKSİYONLAR
def fetch_safe_response(text):
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"system","content":f"Mentor. Level:{st.session_state.level}. Format: Mood|Answer|Fix"},{"role":"user","content":text}],
            timeout=8.0 # Çok bekleyip bağlantıyı koparmasın
        )
        return res.choices[0].message.content
    except:
        return "System | I'm here but connection is a bit slow. Can you repeat? | None"

# 📱 ARAYÜZ
st.title("🌐 AIVA AI")
chat_box = st.container()
with chat_box:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

st.divider()
c1, c2 = st.columns([1, 4])
with c1:
    # Key'i sabit tutarak çökmesini engelledik
    audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="final_mic_v3")
with c2:
    user_query = st.chat_input("Type here if mic fails...")

# --- MANTIK ---
input_text = None
if audio_bytes:
    h = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != h:
        st.session_state.last_audio_hash = h
        try:
            with open("t.wav","wb") as f: f.write(audio_bytes)
            with open("t.wav","rb") as f:
                input_text = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3", response_format="text")
        except:
            st.warning("Mic connection flickered. Try again or type.")

if user_query: input_text = user_query

if input_text:
    st.session_state.messages.append({"role":"user","content":input_text})
    raw = fetch_safe_response(input_text)
    
    # Parçalama
    parts = raw.split("|")
    ans = parts[1].strip() if len(parts) > 1 else raw
    fix = parts[2].strip() if len(parts) > 2 else "None"
    
    st.session_state.messages.append({"role":"assistant","content":ans})
    
    # Ses Oluşturma
    try:
        tts = gTTS(text=ans, lang='en')
        tts.save("s.mp3")
        with open("s.mp3","rb") as f: st.session_state.audio_queue = f.read()
    except: pass
    
    st.rerun()
