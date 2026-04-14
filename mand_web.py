import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
import uuid
from streamlit_mic_recorder import mic_recorder

# ==========================================
# ⚙️ KONFİGÜRASYON VE GÜVENLİK
# ==========================================

# API Anahtarını Streamlit Secrets üzerinden alıyoruz (Kod içinde gizli)
# Not: Eğer lokalde hata alırsan bu satırı geçici olarak eski haline getirebilirsin
# Ama sunum için en profesyoneli st.secrets kullanmaktır.
API_KEY = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else "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"

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY
)

# ==========================================
# 🧠 OTURUM YÖNETİMİ (SESSION STATE)
# ==========================================
def initialize_session():
    """Uygulama başladığında gerekli hafıza alanlarını hazırlar."""
    defaults = {
        "messages": [],
        "user_name": "Friend",
        "stats": {"total_words": 0, "mistakes": 0},
        "level": "A1",
        "mood": "neutral",
        "last_fix": "",
        "audio_queue": None,
        "last_audio_id": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session()

# ==========================================
# 🎨 GÖRSEL TASARIM (MINIMALIST UI)
# ==========================================
st.set_page_config(page_title="AIVA | Intelligent Language Coach", page_icon="🌐", layout="wide")

# Modern ve profesyonel bir arayüz için özel CSS
st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    
    /* Yan Panel Tasarımı */
    .stSidebar { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    
    /* İstatistik Kartları */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    
    /* Aiva Avatar Tasarımı (Emoji yerine modern bir görsel yapı) */
    .aiva-avatar {
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%;
        margin: 0 auto 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        border: 2px solid #60a5fa;
    }
    
    .status-dot {
        height: 10px; width: 10px; background-color: #10b981;
        border-radius: 50%; display: inline-block; margin-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🎙️ SES VE YAZILIM MANTIĞI
# ==========================================
def process_audio(text):
    """Metni ses dosyasına dönüştürür."""
    if text:
        try:
            tts = gTTS(text=text, lang='en')
            temp_file = f"speech_{uuid.uuid4().hex}.mp3"
            tts.save(temp_file)
            with open(temp_file, "rb") as f:
                data = f.read()
            os.remove(temp_file)
            return data
        except: return None
    return None

def fetch_response(user_input):
    """Aiva AI modelinden yanıt çeker."""
    if "my name is" in user_input.lower():
        st.session_state.user_name = user_input.lower().split("is")[-1].strip().capitalize()

    st.session_state.stats["total_words"] += len(user_input.split())
    
    # Profesyonel Koç Talimatı
    instruction = (
        f"Act as AIVA, a high-end personal language coach. User: {st.session_state.user_name}. "
        f"Level: {st.session_state.level}. Tone: Encouraging, professional, yet friendly. "
        "Strictly avoid robotic phrases. If asked about status, respond as a mentor. "
        "Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
    )

    try:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": instruction}] + history + [{"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant"
        )
        content = response.choices[0].message.content
        
        # Yanıtı ayrıştırma
        mood, ans, fix = "neutral", content, ""
        if "|" in content:
            parts = content.split("|")
            mood = parts[0].replace("[Mood:", "").replace("]", "").strip().lower()
            ans = parts[1].strip() if len(parts) > 1 else content
            fix = parts[2].replace("[Fix:", "").replace("]", "").strip() if len(parts) > 2 else ""
        
        st.session_state.mood = mood
        return ans, fix
    except: return "AIVA connection interrupted. Please try again.", ""

# ==========================================
# 📊 YAN PANEL (DASHBOARD)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>AIVA CORE</h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="metric-card">
            <small style='color: #94a3b8;'>PROGRESS TRACKER</small><br>
            <span style='font-size: 1.2em;'>📝 {st.session_state.stats['total_words']} Words</span><br>
            <span style='font-size: 1.2em; color: #fbbf24;'>⚠️ {st.session_state.stats['mistakes']} Points</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.session_state.level = st.select_slider("Select Proficiency", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    
    if st.button("Initialize New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0}
        st.rerun()

# ==========================================
# 💬 ANA SOHBET EKRANI
# ==========================================
st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <div class="aiva-avatar">🌐</div>
        <h3 style='margin-bottom: 5px;'>AIVA Intelligence</h3>
        <small style='color: #10b981;'><span class="status-dot"></span> System Operational</small>
    </div>
    """, unsafe_allow_html=True)

# Otomatik Ses Oynatma
if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# Mesaj Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Giriş Alanı (Minimalist)
st.divider()
input_col, mic_col = st.columns([5, 1])

with mic_col:
    audio_stream = mic_recorder(start_prompt="Speak", stop_prompt="Process", key='voice_input')

with input_col:
    user_query = st.chat_input("Enter your message...")

# Girişleri Yakalama
final_text = None
if audio_stream and st.session_state.last_audio_id != audio_stream['id']:
    st.session_state.last_audio_id = audio_stream['id']
    with st.spinner("Analyzing audio..."):
        with open("raw.wav", "wb") as f: f.write(audio_stream['bytes'])
        with open("raw.wav", "rb") as f:
            transcription = client.audio.transcriptions.create(file=("raw.wav", f.read()), model="whisper-large-v3", response_format="text")
        final_text = transcription
elif user_query:
    final_text = user_query

# İşleme Süreci
if final_text:
    st.session_state.messages.append({"role": "user", "content": final_text})
    with st.chat_message("user"): st.markdown(final_text)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, correction = fetch_response(final_text)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.last_fix = correction
            if correction and "None" not in correction:
                st.session_state.stats["mistakes"] += 1
            st.session_state.audio_queue = process_audio(answer)
    st.rerun()

# Analiz Paneli
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px dashed #eab308; margin-top: 10px;'>
            <p style='color: #fbbf24; margin-bottom: 5px;'><b>💡 Coach's Analysis:</b></p>
            <p style='font-style: italic;'>{st.session_state.last_fix}</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Listen to Correction"):
        st.session_state.audio_queue = process_audio(st.session_state.last_fix)
        st.rerun()
