import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os, uuid, hashlib
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ CONFIG (API KEY GÖMÜLÜ)
# ==========================================
API_KEY = "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"
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

if "messages" not in st.session_state: st.session_state.messages = []
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

st.set_page_config(page_title="AIVA AI", layout="wide")
st.markdown("<style>.stApp{background:#0b0f19;color:#eceff4;}</style>", unsafe_allow_html=True)

# SIDEBAR (Sadece Reset Dursun, Kafa Karıştırmasın)
with st.sidebar:
    st.title("🤖 AIVA")
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.rerun()

st.title("🌐 AIVA Intelligence")

# CHAT GEÇMİŞİ
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# SES ÇALMA
if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

st.divider()
col1, col2 = st.columns([1, 5])
with col1:
    # 3 saniye kuralı burada
    audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="final_v10")
with col2:
    user_query = st.chat_input("Type here if mic fails...")

# --- ANA MANTIK ---
final_text = None

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
            st.error("Mic Connection Error!")

if user_query: final_text = user_query

if final_text:
    st.session_state.messages.append({"role":"user","content":final_text})
    
    try:
        # Hata payını sıfıra indiren basit prompt
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"You are AIVA, a professional English mentor. Give short and natural answers. Do not use any special formatting or brackets."},
                {"role":"user","content":final_text}
            ]
        )
        # PARSE YOK, DİREKT CEVAP
        ans = res.choices[0].message.content
        st.session_state.messages.append({"role":"assistant","content":ans})
        
        # SES ÜRETİMİ
        tts = gTTS(text=ans, lang='en')
        tts.save("s.mp3")
        with open("s.mp3","rb") as f: st.session_state.audio_queue = f.read()
        
        st.rerun()
    except Exception as e:
        st.error(f"AI Error: {e}")
