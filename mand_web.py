import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os, hashlib, io
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ CONFIG (API KEY GÜVENLİ)
# ==========================================
if "GROQ_API_KEY" in st.secrets:
    API_KEY = st.secrets["GROQ_API_KEY"]
else:
    st.error("API Key bulunamadı! Lütfen secrets.toml dosyasını kontrol et.")
    st.stop()

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# ==========================================
# 🧠 SESSION STATE
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "B1"
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ... (UI DESIGN KISMI AYNI KALIYOR) ...

# ==========================================
# 🎙️ INPUT AREA & LOGIC
# ==========================================
final_text = None

# Audio recorder input
audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="final_v_pro")
user_query = st.chat_input("Message AIVA...")

if audio_bytes:
    h = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != h:
        st.session_state.last_audio_hash = h
        try:
            # Dosyaya yazmadan direkt bellek üzerinden (BytesIO) gönderiyoruz
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "input.wav" # Whisper isim bekleyebilir
            
            trans = client.audio.transcriptions.create(
                file=audio_file, 
                model="whisper-large-v3", 
                response_format="text"
            )
            if trans: final_text = trans
        except Exception as e:
            st.error(f"Aiva couldn't hear you clearly: {e}")

if user_query: final_text = user_query

if final_text:
    st.session_state.stats["total_words"] += len(final_text.split())
    st.session_state.messages.append({"role": "user", "content": final_text})
    
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"You are AIVA, a professional English mentor. Adapt to {st.session_state.level} level. Give natural and short answers."},
                {"role": "user", "content": final_text}
            ],
            timeout=15.0
        )
        ans = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        # TTS - Sesli yanıt üretme
        tts = gTTS(text=ans, lang='en')
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        st.session_state.audio_queue = audio_fp.getvalue()
        
        st.rerun() 
        
    except Exception as e:
        st.error("Connection glitch. Let's try that one more time!")
