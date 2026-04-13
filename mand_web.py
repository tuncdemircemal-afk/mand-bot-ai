import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
from streamlit_mic_recorder import mic_recorder

# --- 1. API AYARI ---
# Kanka senin son verdiğin API Key'i buraya çaktım
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

# --- 3. SAYFA TASARIMI (CSS) ---
st.set_page_config(page_title="MAND Bot v8.3 Web", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: white; }
    .stSidebar { background-color: #1e293b !important; }
    .stats-box { background-color: #334155; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 10px; }
    .mood-indicator { font-size: 60px; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. YARDIMCI FONKSİYONLAR (SES VE AI) ---

def speak(text):
    """Botun konuşmasını sağlar (Base64 ile tarayıcıya gömer)"""
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("temp.mp3")
        with open("temp.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            # Otomatik çalması için autoplay ekledik, görünmesi için controls ekledik
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay="true"></audio>', unsafe_allow_html=True)
        os.remove("temp.mp3")
    except Exception as e:
        st.error(f"TTS Error: {e}")

def ask_mand(prompt):
    """AI mantığını çalıştırır ve cevabı parçalar"""
    # İsim yakalama
    if "my name is" in prompt.lower():
        st.session_state.user_name = prompt.lower().split("is")[-1].strip().capitalize()

    st.session_state.stats["total_words"] += len(prompt.split())
    
    sys_msg = (f"You are MAND Bot. Level: {st.session_state.level}. User: {st.session_state.user_name}. "
               "1. Answer briefly and naturally in English. "
               "2. End with a short follow-up question related to the topic. "
               "3. If input is nonsense (like 'brather'), answer ONLY: 'INVALID_INPUT_DETECTED'. "
               "Format: [Mood: mood] | [Answer] | [Fix: correction or None]")

    try:
        res = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_msg}] + 
                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]] +
                     [{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        raw = res.choices[0].message.content
        
        # Parçalama (Ayrıştırma)
        mood, ans, fix = "neutral", raw, ""
        if "|" in raw:
            parts = raw.split("|")
            mood = parts[0].replace("[Mood:", "").replace("]", "").strip().lower()
            if len(parts) >= 2: ans = parts[1].strip()
            if len(parts) >= 3: fix = parts[2].replace("[Fix:", "").replace("]", "").strip()
        
        st.session_state.mood = mood
        return ans, fix
    except Exception as e:
        return f"Error: {e}", ""

# --- 5. SIDEBAR (DASHBOARD) ---
with st.sidebar:
    st.title("🤖 MAND DASHBOARD")
    st.markdown(f"""
    <div class="stats-box">
        <p style='margin:0;'>📝 <b>Words:</b> {st.session_state.stats['total_words']}</p>
        <p style='margin:0; color:#fbbf24;'>⚠️ <b>Mistakes:</b> {st.session_state.stats['mistakes']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔍 Mistake History"):
        if st.session_state.stats['mistake_list']:
            for m in st.session_state.stats['mistake_list'][-5:]:
                st.write(f"• {m}")
        else:
            st.write("No mistakes yet!")

    st.divider()
    st.session_state.level = st.selectbox("SET ENGLISH LEVEL", ["A1", "A2", "B1", "B2"], index=["A1", "A2", "B1", "B2"].index(st.session_state.level))
    
    if st.button("🗑️ Reset Session"):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0, "mistake_list": []}
        st.rerun()

# --- 6. ANA ARAYÜZ ---
col1, col2 = st.columns([1, 5])
with col1:
    mood_emoji = "🤖"
    if "happy" in st.session_state.mood: mood_emoji = "😊"
    elif "sad" in st.session_state.mood or "angry" in st.session_state.mood: mood_emoji = "😡"
    elif "neutral" in st.session_state.mood: mood_emoji = "😐"
    st.markdown(f"<div class='mood-indicator'>{mood_emoji}</div>", unsafe_allow_html=True)

with col2:
    st.title("MAND Bot: Legendary Web v8.3")
    st.write(f"Status: **Online** | Level: **{st.session_state.level}** | User: **{st.session_state.user_name}**")

# Mesaj Geçmişini Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. SESLİ VE YAZILI GİRİŞ ---
st.divider()
st.subheader("🎤 Transmit Your Voice or Type")

# MİKROFON BUTONU
audio_data = mic_recorder(
    start_prompt="🎤 CLICK TO SPEAK (KONUŞ)",
    stop_prompt="🛑 STOP (DURDUR)",
    key='recorder'
)

user_input = st.chat_input("Or type your message here...")

# Eğer Ses Kaydı Geldiyse Yazıya Çevir
if audio_data and not user_input:
    with st.spinner("MAND is translating your voice..."):
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_data['bytes'])
        
        with open("temp_audio.wav", "rb") as f:
            transcript = client.audio.transcriptions.create(
                file=("temp_audio.wav", f.read()),
                model="whisper-large-v3",
                response_format="text",
                language="en"
            )
        user_input = transcript
        os.remove("temp_audio.wav")

# Mesajı İşle
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ans, fix = ask_mand(user_input)
            
            if "INVALID_INPUT_DETECTED" in ans:
                st.error("⚠️ I didn't recognize that. Please speak or write clearly!")
            else:
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.session_state.last_fix = fix
                if fix and "None" not in fix:
                    st.session_state.stats["mistakes"] += 1
                    st.session_state.stats["mistake_list"].append(fix)
                speak(ans)
    st.rerun()

# Düzeltme Butonu (En altta görünür)
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    st.info("💡 Analysis Available")
    if st.button("⚠️ SHOW MY MISTAKE"):
        st.warning(f"Correction: {st.session_state.last_fix}")
        speak(st.session_state.last_fix)
        st.session_state.last_fix = ""
