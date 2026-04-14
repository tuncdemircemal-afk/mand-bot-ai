import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
import uuid
import json
from streamlit_mic_recorder import mic_recorder

# --- 1. API AYARI ---
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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" 
)

MEMORY_FILE = "mand_bot_web_data.json"

# --- 2. JSON VERİ YÖNETİMİ ---
def load_data():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"user_name": "Friend", "stats": {"total_words": 0, "mistakes": 0, "mistake_list": []}}

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 3. SESSION STATE ---
if "persistent_data" not in st.session_state:
    st.session_state.persistent_data = load_data()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "level" not in st.session_state:
    st.session_state.level = "A1"
if "mood" not in st.session_state:
    st.session_state.mood = "neutral"
if "last_fix" not in st.session_state:
    st.session_state.last_fix = ""
if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

# --- 4. TASARIM (Tkinter Twin) ---
st.set_page_config(page_title="MAND Bot v12", page_icon="🤖", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a; color: white; }}
    .stSidebar {{ background-color: #1e293b !important; }}
    .stats-card {{ background-color: #334155; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; }}
    .robot-box {{
        background-color: #1e293b; border: 4px solid #94a3b8; border-radius: 20px;
        padding: 40px; text-align: center; margin-bottom: 20px;
    }}
    .eye {{
        width: 30px; height: 30px;
        background-color: { "#22c55e" if "happy" in st.session_state.mood else "#ef4444" if "sad" in st.session_state.mood or "angry" in st.session_state.mood else "#3b82f6" };
        border-radius: 50%; display: inline-block; margin: 0 15px; box-shadow: 0 0 15px currentColor;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. YARDIMCI FONKSİYONLAR ---
def get_audio_bytes(text):
    try:
        tts = gTTS(text=text, lang='en')
        filename = f"temp_{uuid.uuid4().hex}.mp3"
        tts.save(filename)
        with open(filename, "rb") as f: data = f.read()
        os.remove(filename)
        return data
    except: return None

def ask_mand(prompt):
    if "my name is" in prompt.lower():
        name = prompt.lower().split("is")[-1].strip().capitalize()
        st.session_state.persistent_data["user_name"] = name
        save_data(st.session_state.persistent_data)

    st.session_state.persistent_data["stats"]["total_words"] += len(prompt.split())
    
    # --- BURASI KRİTİK: Robot gibi davranmasını engelleyen talimat ---
    sys_msg = (
        f"You are MAND Bot, a legendary English Coach and a close friend ('kanka'). "
        f"User name: {st.session_state.persistent_data['user_name']}. Level: {st.session_state.level}. "
        "IMPORTANT RULES: "
        "1. NEVER say 'I am an AI' or 'I am a robot' or 'I don't have feelings'. "
        "2. If asked 'How are you?', answer like a cool human coach (e.g., 'I'm feeling like a bullet! Ready to crush some English!'). "
        "3. Be energetic, friendly, and helpful. Use a natural 'bro' or 'coach' vibe. "
        "4. Always end with a natural follow-up question. "
        "Format: [Mood: mood] | [Answer] | [Fix: correction or None]"
    )

    try:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
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
    except: return "Connection error kanka!", ""

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("🤖 DASHBOARD")
    st.markdown(f"""<div class="stats-card">
    📝 <b>Words:</b> {st.session_state.persistent_data['stats']['total_words']}<br>
    <span style='color:#fbbf24;'>⚠️ <b>Mistakes:</b> {st.session_state.persistent_data['stats']['mistakes']}</span>
    </div>""", unsafe_allow_html=True)
    st.divider()
    st.session_state.level = st.radio("LEVEL", ["A1", "A2", "B1", "B2"], index=["A1", "A2", "B1", "B2"].index(st.session_state.level), horizontal=True)
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 7. ANA PANEL ---
st.markdown(f"""<div class="robot-box"><div class="eye"></div><div class="eye"></div>
<p style='margin-top:20px; font-family:Courier; font-weight:bold; color:#94a3b8;'>SYSTEM: {st.session_state.level} | ONLINE</p></div>""", unsafe_allow_html=True)

if st.session_state.audio_to_play:
    st.audio(st.session_state.audio_to_play, format="audio/mp3", autoplay=True)
    st.session_state.audio_to_play = None

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 8. GİRİŞ ---
st.divider()
col_mic, col_txt = st.columns([1, 4])
with col_mic:
    audio_data = mic_recorder(start_prompt="🎤 TRANSMIT", stop_prompt="🛑 STOP", key='recorder')
with col_txt:
    user_text = st.chat_input("Speak or type to your coach...")

final_input = None
if audio_data and (not st.session_state.get('last_audio_id') or st.session_state.last_audio_id != audio_data['id']):
    st.session_state.last_audio_id = audio_data['id']
    with st.spinner("MAND listening..."):
        with open("temp.wav", "wb") as f: f.write(audio_data['bytes'])
        with open("temp.wav", "rb") as f:
            transcript = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3", response_format="text")
        final_input = transcript
elif user_text:
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
            st.session_state.persistent_data["stats"]["mistakes"] += 1
            save_data(st.session_state.persistent_data)
        st.session_state.audio_to_play = get_audio_bytes(ans)
    st.rerun()

# --- 9. ANALİZ ---
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    if st.button("⚠️ SHOW ANALYSIS", use_container_width=True):
        st.warning(f"Correction: {st.session_state.last_fix}")
        st.session_state.audio_to_play = get_audio_bytes(st.session_state.last_fix)
        st.session_state.last_fix = ""
        st.rerun()
