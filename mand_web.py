import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os, uuid, hashlib
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ HIZLI CONFIG
# ==========================================
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    API_KEY = "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"

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# Session State
if "messages" not in st.session_state: st.session_state.messages = []
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# UI
st.set_page_config(page_title="AIVA AI", layout="centered")
st.markdown("<style>.stApp{background:#0b0f19;color:#eceff4;}</style>", unsafe_allow_html=True)
st.title("🌐 AIVA: Talk to Me")

# Chat History
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Ses Çalma (Otomatik)
if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# ==========================================
# 🎙️ INPUT (HIZLANDIRILMIŞ)
# ==========================================
st.divider()
audio_bytes = audio_recorder(text="TAP & SPEAK", icon_size="3x", pause_threshold=2.0, key="mic_vfinal")

if audio_bytes:
    h = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != h:
        st.session_state.last_audio_hash = h
        
        try:
            # 1. Sesi Yazıya Çevir (Whisper)
            with open("t.wav","wb") as f: f.write(audio_bytes)
            with open("t.wav","rb") as f:
                user_text = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3", response_format="text")
            
            if user_text:
                st.session_state.messages.append({"role":"user","content":user_text})
                
                # 2. Yapay Zekadan Cevap Al (Llama 3)
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":"You are AIVA, a helpful English mentor. Give short, natural answers."},{"role":"user","content":user_text}],
                    temperature=0.7
                )
                answer = res.choices[0].message.content
                st.session_state.messages.append({"role":"assistant","content":answer})
                
                # 3. Cevabı Sese Çevir (gTTS)
                tts = gTTS(text=answer, lang='en')
                tts.save("s.mp3")
                with open("s.mp3","rb") as f: st.session_state.audio_queue = f.read()
                
                st.rerun()
        except Exception as e:
            st.error("Connection flickered. Try speaking again!")
