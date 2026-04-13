import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import uuid
import base64

# --- API VE SESSION AYARLARI ---
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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" 
)

# Web sitesi yenilense de verileri kaybetmemek için Session State kullanıyoruz
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = "Friend"
if "stats" not in st.session_state:
    st.session_state.stats = {"words": 0, "mistakes": 0, "history": []}
if "last_fix" not in st.session_state:
    st.session_state.last_fix = ""

# --- SAYFA TASARIMI ---
st.set_page_config(page_title="MAND Bot AI", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: white; }
    .stChatMessage { border-radius: 15px; background-color: #1e293b !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (İSTATİSTİKLER) ---
with st.sidebar:
    st.title("🤖 MAND DASHBOARD")
    level = st.selectbox("English Level", ["A1", "A2", "B1", "B2"])
    st.divider()
    st.subheader("📊 Session Stats")
    st.write(f"📝 Words: {st.session_state.stats['words']}")
    st.write(f"⚠️ Mistakes: {st.session_state.stats['mistakes']}")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.session_state.stats = {"words": 0, "mistakes": 0, "history": []}
        st.rerun()

# --- SES OYNATICI (TARAYICI DOSTU) ---
def play_audio(text):
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    os.remove("temp.mp3")

# --- AI MANTIĞI ---
def ask_mand(prompt):
    if "my name is" in prompt.lower():
        st.session_state.user_name = prompt.lower().split("is")[-1].strip().capitalize()

    st.session_state.stats["words"] += len(prompt.split())
    
    sys_msg = (f"You are MAND Bot. Level: {level}. User: {st.session_state.user_name}. "
               "Answer naturally in English. Always end with a follow-up question. "
               "If nonsense, answer: INVALID_INPUT_DETECTED. "
               "Format: [Mood] | [Answer] | [Fix: correction or None]")

    try:
        res = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + 
                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages] +
                     [{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        raw = res.choices[0].message.content
        parts = raw.split("|")
        ans = parts[1].strip() if len(parts) > 1 else raw
        fix = parts[2].replace("[Fix:", "").replace("]", "").strip() if len(parts) > 2 else ""
        return ans, fix
    except: return "Connection error!", ""

# --- ANA EKRAN ---
st.title("MAND Bot: Legendary Coach 🚀")
st.write(f"Status: **{level}** | User: **{st.session_state.user_name}**")

# Mesaj Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Düzeltme Butonu (Tkinter'daki analiz butonu)
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    if st.button("⚠️ SHOW MY MISTAKE"):
        st.info(f"💡 Correction: {st.session_state.last_fix}")
        play_audio(st.session_state.last_fix)
        st.session_state.last_fix = ""

# Giriş Alanı
user_input = st.chat_input("Practice your English...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        ans, fix = ask_mand(user_input)
        if "INVALID_INPUT_DETECTED" in ans:
            st.error("I didn't quite get that. Can you repeat clearly?")
        else:
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.session_state.last_fix = fix
            if fix and "None" not in fix:
                st.session_state.stats["mistakes"] += 1
                st.session_state.stats["history"].append(fix)
            play_audio(ans)
            st.rerun()
