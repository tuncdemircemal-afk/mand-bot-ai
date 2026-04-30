import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os, uuid, hashlib
from audio_recorder_streamlit import audio_recorder

#Api key

if "GROQ_API_KEY" in st.secrets:
    API_KEY = st.secrets["GROQ_API_KEY"]
else:
    st.error("API Key bulunamadı! Lütfen secrets.toml dosyasını kontrol et.")
    st.stop()

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)
# 🧠 SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "B1"
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None
# 🎨 UI DESIGN
st.set_page_config(page_title="AIVA | AI Mentor", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stSidebar { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 15px; border-radius: 12px; border: 1px solid #3b82f6; margin-bottom: 10px;
    }
    .aiva-avatar {
        width: 60px; height: 60px; background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5); font-size: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

 #📊 SIDEBAR
with st.sidebar:
    st.markdown("<div class='aiva-avatar'>🌐</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>AIVA CORE</h3>", unsafe_allow_html=True)
    
    st.session_state.level = st.select_slider(
        "Target Level",
        options=["A1", "A2", "B1", "B2", "C1"],
        value=st.session_state.level
    )
    
    st.divider()
    st.markdown(f"""
    <div class="metric-card">
        📝 <b>Words:</b> {st.session_state.stats['total_words']}<br>
        ⚠️ <b>Mistakes:</b> {st.session_state.stats['mistakes']}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Reset Mission", use_container_width=True):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0}
        st.rerun()
#  CHAT DISPLAY
st.title("AIVA Intelligence")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None
#  INPUT AREA
st.divider()
c1, c2 = st.columns([1, 4])
with c1:
    audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="final_v_pro")
with c2:
    user_query = st.chat_input("Message AIVA...")

# --- LOGIC ---
final_text = None

if audio_bytes:
    h = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != h:
        st.session_state.last_audio_hash = h
        try:
            with open("t.wav","wb") as f: f.write(audio_bytes)
            with open("t.wav","rb") as f:
                # Sesi yazıya çevirirken 20 saniye bekleme süresi 
                trans = client.audio.transcriptions.create(
                    file=("t.wav", f.read()), 
                    model="whisper-large-v3", 
                    response_format="text"
                )
                if trans: final_text = trans
        except Exception as e:
            st.error("Microphone connection timed out. Try again!")

if user_query: final_text = user_query

if final_text:
    st.session_state.stats["total_words"] += len(final_text.split())
    st.session_state.messages.append({"role": "user", "content": final_text})
    
    try:
        # Groq API çağrısı - Timeout süresini 15 saniye
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"You are AIVA, a professional English mentor. Adapt to {st.session_state.level} level. Give natural and short answers without any special formatting."},
                {"role": "user", "content": final_text}
            ],
            timeout=15.0
        )
        ans = res.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        # TTS - Sesli yanıt üretme
        tts = gTTS(text=ans, lang='en')
        tts.save("s.mp3")
        with open("s.mp3","rb") as f: st.session_state.audio_queue = f.read()
        st.rerun() 
        
    except Exception as e:
        # Eğer hata rate limit ise (çok sık soruyorsan) farklı bir uyarı verir
        if "429" in str(e):
            st.warning("Whoa! Too many requests. Take a deep breath and try in 5 seconds.")
        else:
            st.error("Connection glitch. Let's try that one more time!")
