import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import uuid
import hashlib
from audio_recorder_streamlit import audio_recorder

# ==========================================
# ⚙️ GÜVENLİ YAPILANDIRMA (Secrets)
# ==========================================
# Not: Streamlit Cloud üzerinde Settings > Secrets kısmına 
# GROQ_API_KEY = "senin_anahtarın" şeklinde eklemelisin.
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    # Eğer lokaldeysen ve secrets yoksa hata vermemesi için geçici çözüm
    API_KEY = "BURAYA_GECICI_KEY_YAZABILIRSIN_AMA_YAYINLARKEN_SIL"

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# ==========================================
# 🧠 SESSION STATE (Hafıza Yönetimi)
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "B1"
if "last_fix" not in st.session_state: st.session_state.last_fix = ""
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ==========================================
# 🎨 UI & TASARIM (Profesyonel Görünüm)
# ==========================================
st.set_page_config(page_title="AIVA AI Mentor", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .metric-card {
        background: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #3b82f6;
    }
    .aiva-header { text-align: center; padding: 20px; }
    .aiva-logo { font-size: 50px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🛠️ FONKSİYONLAR
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
        f"You are AIVA, a helpful English Mentor. User Level: {st.session_state.level}. "
        "Talk naturally. Format: Mood: [mood] | [Your Answer] | [Correction or None]"
    )
    try:
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant", 
            temperature=0.6,
            timeout=15.0 # Bağlantı hatasını önlemek için bekleme süresi
        )
        content = response.choices[0].message.content
        if "|" in content:
            parts = content.split("|")
            ans = parts[1].strip().replace("[Answer]", "").replace("[", "").replace("]", "")
            fix = parts[2].strip().replace("[Fix:", "").replace("]", "")
            return ans, fix
        return content, "None"
    except Exception as e:
        return "I'm having a slight connection issue. Could you repeat that?", "None"

# ==========================================
# 📱 ARAYÜZ (INTERFACE)
# ==========================================
with st.sidebar:
    st.markdown("### 📊 SESSION STATS")
    st.markdown(f'<div class="metric-card">Words Spoken: {st.session_state.stats["total_words"]}<br>Mistakes Noted: {st.session_state.stats["mistakes"]}</div>', unsafe_allow_html=True)
    st.session_state.level = st.select_slider("Target Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    if st.button("Reset Mission", use_container_width=True):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

st.markdown('<div class="aiva-header"><div class="aiva-logo">🌐</div><h1>AIVA INTELLIGENCE</h1><p>Your Personal Flight Instructor for English</p></div>', unsafe_allow_html=True)

# Chat Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Ses Çalma (Otomatik)
if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# ==========================================
# 🎙️ GİRİŞ ALANI (INPUT)
# ==========================================
st.divider()
col_mic, col_text = st.columns([1, 5])

with col_mic:
    # Sabit key ("presentation_mic") mikrofonun kaybolmasını engeller
    audio_bytes = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="presentation_mic", neutral_color="#60a5fa")

with col_text:
    user_query = st.chat_input("Type your message here...")

# --- İŞLEME (PROCESSING) ---
input_text = None

if audio_bytes:
    h = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != h:
        st.session_state.last_audio_hash = h
        with st.spinner("AIVA is listening..."):
            try:
                with open("temp.wav", "wb") as f: f.write(audio_bytes)
                with open("temp.wav", "rb") as f:
                    transcription = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3", response_format="text")
                if transcription and len(transcription.strip()) > 1:
                    input_text = transcription
            except:
                st.error("Connection lost. Please try again or use text input.")

if user_query:
    input_text = user_query

if input_text:
    # Kelime sayacı
    st.session_state.stats["total_words"] += len(input_text.split())
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    # Yanıt alma
    with st.spinner("AIVA is thinking..."):
        answer, correction = fetch_response(input_text)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_fix = correction
        if correction and "None" not in correction: 
            st.session_state.stats["mistakes"] += 1
        
        # Ses dosyası oluşturma
        st.session_state.audio_queue = get_audio_bytes(answer)
    
    st.rerun()

# Mentor Notu
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.info(f"🎓 **Mentor's Note:** {st.session_state.last_fix}")
