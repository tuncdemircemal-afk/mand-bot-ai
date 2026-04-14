import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
import uuid
from streamlit_mic_recorder import mic_recorder

# ==========================================
# ⚙️ GÜVENLİK VE YAPILANDIRMA
# ==========================================
# API anahtarını güvenli sistemden çekiyoruz
API_KEY = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else "BURAYA_ANAHTARI_YAZABİLİRSİN"

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY
)

# ==========================================
# 🧠 OTURUM YÖNETİMİ (SESSION STATE)
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "user_name" not in st.session_state: st.session_state.user_name = "Friend"
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "A1"
if "mood" not in st.session_state: st.session_state.mood = "neutral"
if "last_fix" not in st.session_state: st.session_state.last_fix = ""
if "audio_to_play" not in st.session_state: st.session_state.audio_to_play = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

# ==========================================
# 🎨 PROFESYONEL UI TASARIMI (CSS)
# ==========================================
st.set_page_config(page_title="AIVA AI | Intelligent Coach", page_icon="🌐", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0b0f19; color: #e2e8f0; }}
    .stSidebar {{ background-color: #111827 !important; border-right: 1px solid #1f2937; }}
    
    /* İstatistik Kartı */
    .metric-card {{
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px;
    }}
    
    /* Modern Avatar */
    .aiva-avatar {{
        width: 80px; height: 80px;
        background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%; margin: 0 auto 10px;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); border: 2px solid #60a5fa;
        font-size: 40px;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🎙️ YARDIMCI FONKSİYONLAR
# ==========================================
def get_audio_bytes(text):
    if text:
        try:
            tts = gTTS(text=text, lang='en')
            filename = f"s_{uuid.uuid4().hex}.mp3"
            tts.save(filename)
            with open(filename, "rb") as f: data = f.read()
            os.remove(filename)
            return data
        except: return None
    return None

def ask_aiva(prompt):
    if "my name is" in prompt.lower():
        st.session_state.user_name = prompt.lower().split("is")[-1].strip().capitalize()

    st.session_state.stats["total_words"] += len(prompt.split())
    
    # --- KRİTİK TALİMAT: ÖĞRETMENLİK YAPMA, KANKA OL ---
    sys_msg = (
        f"You are AIVA, a legendary English Coach and a close friend. User: {st.session_state.user_name}. Level: {st.session_state.level}. "
        "STRICT RULES: "
        "1. In the [Answer] part, ONLY talk like a cool human friend. NO grammar tips, NO 'you should say', NO lecturing. "
        "2. If asked 'How are you?', answer like a human (e.g., 'Mermi gibiyim kanka, ready to crush it!'). "
        "3. Put ALL grammar corrections, suggestions, or lessons STRICTLY in the [Fix] part. "
        "4. Never mention you are an AI. "
        "Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
    )

    try:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]
        res = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": prompt}],
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
    except: return "Connection lost kanka...", ""

# ==========================================
# 📊 SIDEBAR (DASHBOARD)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>AIVA CORE</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="metric-card">
            <small style='color: #94a3b8;'>USER ANALYTICS</small><br>
            <span style='font-size: 1.1em;'>📝 {st.session_state.stats['total_words']} Words</span><br>
            <span style='font-size: 1.1em; color: #fbbf24;'>⚠️ {st.session_state.stats['mistakes']} Points</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.session_state.level = st.select_slider("Proficiency", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    
    if st.button("Initialize New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0}
        st.rerun()

# ==========================================
# 💬 ANA EKRAN
# ==========================================
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <div class="aiva-avatar">🌐</div>
        <h3 style='margin-bottom: 0;'>AIVA Intelligence</h3>
        <small style='color: #10b981;'>• System Operational</small>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.audio_to_play:
    st.audio(st.session_state.audio_to_play, format="audio/mp3", autoplay=True)
    st.session_state.audio_to_play = None

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- GİRİŞ ALANI ---
st.divider()
input_col, mic_col = st.columns([5, 1])

with mic_col:
    audio_data = mic_recorder(start_prompt="Speak", stop_prompt="Process", key='recorder')

with input_col:
    user_text = st.chat_input("Message Aiva Bot...")

final_input = None
if audio_data and (not st.session_state.last_audio_id or st.session_state.last_audio_id != audio_data['id']):
    st.session_state.last_audio_id = audio_data['id']
    with st.spinner("Analyzing..."):
        with open("raw.wav", "wb") as f: f.write(audio_data['bytes'])
        with open("raw.wav", "rb") as f:
            transcript = client.audio.transcriptions.create(file=("raw.wav", f.read()), model="whisper-large-v3", response_format="text")
        final_input = transcript
elif user_text:
    final_input = user_text

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)
    with st.chat_message("assistant"):
        ans, fix = ask_aiva(final_input)
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.session_state.last_fix = fix
        if fix and "None" not in fix:
            st.session_state.stats["mistakes"] += 1
        st.session_state.audio_to_play = get_audio_bytes(ans)
    st.rerun()

# --- ANALİZ ALANI ---
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px dashed #eab308; margin-top: 10px;'>
            <p style='color: #fbbf24; margin-bottom: 5px;'><b>💡 Coach's Analysis:</b></p>
            <p style='font-style: italic;'>{st.session_state.last_fix}</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Play Analysis Audio"):
        st.session_state.audio_to_play = get_audio_bytes(st.session_state.last_fix)
        st.rerun()
