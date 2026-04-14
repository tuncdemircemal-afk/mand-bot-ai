import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
import uuid
from streamlit_mic_recorder import mic_recorder

# --- 1. API AYARI ---
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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" 
)

# --- 2. HAFIZA (SESSION STATE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = "Friend"
if "stats" not in st.session_state:
    st.session_state.stats = {"total_words": 0, "mistakes": 0, "mistake_list": []}
if "level" not in st.session_state:
    st.session_state.level = "A1"
if "mood" not in st.session_state:
    st.session_state.mood = "neutral"
if "last_fix" not in st.session_state:
    st.session_state.last_fix = ""
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None
# SES İÇİN YENİ HAFIZA ALANI
if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

# --- 3. TASARIM (CSS) ---
st.set_page_config(page_title="MAND Bot v10.5", page_icon="🤖", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a; color: white; }}
    .stSidebar {{ background-color: #1e293b !important; }}
    .stats-card {{ background-color: #334155; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; }}
    .robot-box {{
        background-color: #1e293b;
        border: 4px solid #94a3b8;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        margin-bottom: 20px;
    }}
    .eye {{
        width: 30px; height: 30px;
        background-color: { "#22c55e" if "happy" in st.session_state.mood else "#ef4444" if "sad" in st.session_state.mood or "angry" in st.session_state.mood else "#3b82f6" };
        border-radius: 50%;
        display: inline-block;
        margin: 0 15px;
        box-shadow: 0 0 15px currentColor;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SES SİSTEMİ (EN GÜNCEL HALİ) ---
def get_audio_base64(text):
    if text:
        try:
            tts = gTTS(text=text, lang='en')
            filename = f"temp_{uuid.uuid4().hex}.mp3"
            tts.save(filename)
            with open(filename, "rb") as f:
                data = f.read()
            os.remove(filename)
            return data
        except: return None
    return None

# --- 5. AI MANTIĞI ---
def ask_mand(prompt):
    if "my name is" in prompt.lower():
        st.session_state.user_name = prompt.lower().split("is")[-1].strip().capitalize()
    
    st.session_state.stats["total_words"] += len(prompt.split())
    
    sys_msg = (f"You are MAND Bot. Level: {st.session_state.level}. User: {st.session_state.user_name}. "
               "Answer naturally in English. End with a short follow-up question. "
               "Format: [Mood: mood] | [Answer] | [Fix: correction or None]")

    try:
        res = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + 
                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]] +
                     [{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        raw = res.choices[0].message.content
        mood, ans, fix = "neutral", raw, ""
        if "|" in raw:
            parts = raw.split("|")
            mood = parts[0].replace("[Mood:", "").replace("]", "").strip().lower()
            ans = parts[1].strip() if len(parts) > 1 else raw
            fix = parts[2].replace("[Fix:", "").replace("]", "").strip() if len(parts) > 2 else ""
        st.session_state.mood = mood
        return ans, fix
    except: return "Connection error!", ""

# --- 6. SIDEBAR (DASHBOARD) ---
with st.sidebar:
    st.title("🤖 MAND DASHBOARD")
    st.markdown(f"""<div class="stats-card">📝 <b>Total Words:</b> {st.session_state.stats['total_words']}<br>
    <span style='color:#fbbf24;'>⚠️ <b>Mistakes:</b> {st.session_state.stats['mistakes']}</span></div>""", unsafe_allow_html=True)
    
    st.divider()
    st.session_state.level = st.radio("LEVEL", ["A1", "A2", "B1", "B2"], index=["A1", "A2", "B1", "B2"].index(st.session_state.level), horizontal=True)
    
    if st.button("🗑️ Reset Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0, "mistake_list": []}
        st.session_state.audio_to_play = None
        st.rerun()

# --- 7. ANA PANEL ---
st.markdown(f"""<div class="robot-box"><div class="eye"></div><div class="eye"></div>
<p style='margin-top:20px; font-family:Courier; font-weight:bold; color:#94a3b8;'>SYSTEM: {st.session_state.level} | ONLINE</p></div>""", unsafe_allow_html=True)

# SES OYNATICI (Sessizce pusuda bekler)
if st.session_state.audio_to_play:
    st.audio(st.session_state.audio_to_play, format="audio/mp3", autoplay=True)
    st.session_state.audio_to_play = None # Çaldıktan sonra temizle

# Sohbet Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 8. GİRİŞ VE SES KONTROLÜ ---
st.divider()
col_mic, col_txt = st.columns([1, 4])

with col_mic:
    audio_data = mic_recorder(start_prompt="🎤 TRANSMIT", stop_prompt="🛑 STOP", key='recorder')

with col_txt:
    user_text = st.chat_input("Practice your English...")

final_input = None

if audio_data:
    if st.session_state.last_audio_id != audio_data['id']:
        st.session_state.last_audio_id = audio_data['id']
        with st.spinner("MAND listening..."):
            with open("temp.wav", "wb") as f: f.write(audio_data['bytes'])
            with open("temp.wav", "rb") as f:
                transcript = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3", response_format="text")
            final_input = transcript
            if os.path.exists("temp.wav"): os.remove("temp.wav")

if user_text:
    final_input = user_text

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant"):
        ans, fix = ask_mand(final_input)
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.session_state.last_fix = fix
        if fix and "None" not in fix:
            st.session_state.stats["mistakes"] += 1
        
        # SESİ HAZIRLA VE SAYFAYI YENİLE (Oynatılması için)
        st.session_state.audio_to_play = get_audio_base64(ans)
    st.rerun()

# --- 9. DÜZELTME BUTONU ---
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    if st.button("⚠️ SHOW ANALYSIS", use_container_width=True):
        st.warning(f"Correction: {st.session_state.last_fix}")
        st.session_state.audio_to_play = get_audio_base64(st.session_state.last_fix)
        st.session_state.last_fix = ""
        st.rerun()
