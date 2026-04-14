import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
import uuid
from streamlit_mic_recorder import mic_recorder

# ==========================================
# ⚙️ CONFIGURATION & SECURITY
# ==========================================

# Kanka, buradaki anahtarı kontrol et. Eğer hata alırsan tırnak içine kendi anahtarını yaz.
API_KEY = "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"

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY
)

# ==========================================
# 🧠 SESSION MANAGEMENT (Kişiye Özel Hafıza)
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []
if "user_name" not in st.session_state: st.session_state.user_name = "Guest"
if "stats" not in st.session_state: st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state: st.session_state.level = "A1"
if "mood" not in st.session_state: st.session_state.mood = "neutral"
if "last_fix" not in st.session_state: st.session_state.last_fix = ""
if "audio_queue" not in st.session_state: st.session_state.audio_queue = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

# ==========================================
# 🎨 UI DESIGN (Executive Dark Theme)
# ==========================================
st.set_page_config(page_title="AIVA | Intelligence", page_icon="🌐", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0b0f19; color: #e2e8f0; }}
    .stSidebar {{ background-color: #111827 !important; border-right: 1px solid #1f2937; }}
    
    /* Stats Cards */
    .metric-card {{
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px;
    }}
    
    /* Aiva Professional Avatar */
    .aiva-avatar {{
        width: 80px; height: 80px;
        background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 50%; margin: 0 auto 10px;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); border: 2px solid #60a5fa;
        font-size: 40px; color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🎙️ AUDIO & AI LOGIC
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

def fetch_response(user_input):
    if "my name is" in user_input.lower():
        st.session_state.user_name = user_input.lower().split("is")[-1].strip().capitalize()

    st.session_state.stats["total_words"] += len(user_input.split())
    
    # --- PROFESYONEL MENTOR TALİMATI ---
    sys_msg = (
        f"You are AIVA, a professional and sophisticated English Language Mentor. "
        f"User: {st.session_state.user_name}. Level: {st.session_state.level}. "
        "STRICT GUIDELINES: "
        "1. In the [Answer] part, act as a high-end personal coach. Use encouraging and elegant language. "
        "2. DO NOT use slang like 'kanka', 'bro', 'dude', or 'mermi'. Be professional. "
        "3. NEVER lecture the user in the [Answer] part. No 'you should say this'. Only conversation. "
        "4. Put ALL corrections and learning tips STRICTLY in the [Fix] part. "
        "5. If asked 'How are you?', respond like a poised professional ready for the session. "
        "Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
    )

    try:
        # Son 10 mesajlık hafıza
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": user_input}],
            model="llama-3.1-8b-instant"
        )
        content = response.choices[0].message.content
        
        mood, ans, fix = "neutral", content, ""
        if "|" in content:
            parts = content.split("|")
            mood = parts[0].replace("[Mood:", "").replace("]", "").strip().lower()
            ans = parts[1].strip() if len(parts) > 1 else content
            fix = parts[2].replace("[Fix:", "").replace("]", "").strip() if len(parts) > 2 else ""
        
        st.session_state.mood = mood
        return ans, fix
    except Exception as e:
        return f"System check required: {str(e)}", ""

# ==========================================
# 📊 SIDEBAR (DASHBOARD)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>AIVA CORE</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="metric-card">
            <small style='color: #94a3b8;'>SESSION ANALYTICS</small><br>
            <span style='font-size: 1.1em;'>📝 {st.session_state.stats['total_words']} Words</span><br>
            <span style='font-size: 1.1em; color: #fbbf24;'>⚠️ {st.session_state.stats['mistakes']} Feedback Points</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.session_state.level = st.select_slider("Coaching Level", options=["A1", "A2", "B1", "B2"], value=st.session_state.level)
    
    if st.button("Initialize New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0}
        st.rerun()

# ==========================================
# 💬 MAIN CHAT INTERFACE
# ==========================================
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <div class="aiva-avatar">🌐</div>
        <h3 style='margin-bottom: 0;'>AIVA Intelligence</h3>
        <small style='color: #10b981;'>• Mentor Connected</small>
    </div>
    """, unsafe_allow_html=True)

# Otomatik Ses Tetikleyici
if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# Chat Akışı
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Giriş Bölümü
st.divider()
input_col, mic_col = st.columns([5, 1])

with mic_col:
    audio_data = mic_recorder(start_prompt="Speak", stop_prompt="Process", key='voice_input')

with input_col:
    user_query = st.chat_input("Compose your message to AIVA...")

# İşleme Mantığı
final_text = None
if audio_data and st.session_state.last_audio_id != audio_data['id']:
    st.session_state.last_audio_id = audio_data['id']
    with st.spinner("Analyzing audio..."):
        with open("raw.wav", "wb") as f: f.write(audio_data['bytes'])
        with open("raw.wav", "rb") as f:
            transcription = client.audio.transcriptions.create(file=("raw.wav", f.read()), model="whisper-large-v3", response_format="text")
        final_text = transcription
elif user_query:
    final_text = user_query

if final_text:
    st.session_state.messages.append({"role": "user", "content": final_text})
    with st.chat_message("user"): st.markdown(final_text)
    
    with st.chat_message("assistant"):
        answer, correction = fetch_response(final_text)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_fix = correction
        if correction and "None" not in correction:
            st.session_state.stats["mistakes"] += 1
        st.session_state.audio_queue = get_audio_bytes(answer)
    st.rerun()

# --- ANALİZ PANELİ (Dersi buraya hapsediyoruz) ---
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px dashed #eab308; margin-top: 10px;'>
            <p style='color: #fbbf24; margin-bottom: 5px;'><b>📊 Mentor's Learning Note:</b></p>
            <p style='font-style: italic; color: #cbd5e1;'>{st.session_state.last_fix}</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Listen to Analysis"):
        st.session_state.audio_queue = get_audio_bytes(st.session_state.last_fix)
        st.rerun()
