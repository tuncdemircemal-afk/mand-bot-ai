import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
import base64
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
if "last_processed_audio_id" not in st.session_state:
    st.session_state.last_processed_audio_id = None
# KRİTİK: Sesin tekrar etmesini engelleyen takipçi
if "last_spoken_text" not in st.session_state:
    st.session_state.last_spoken_text = ""

# --- 3. TASARIM ---
st.set_page_config(page_title="MAND Bot AI", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: white; }
    .stSidebar { background-color: #1e293b !important; }
    .stats-box { background-color: #334155; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; }
    .mood-indicator { font-size: 60px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. YARDIMCI FONKSİYONLAR ---

def speak(text):
    """Sadece metin yeniyse ses çalmasını sağlar"""
    if text and text != st.session_state.last_spoken_text:
        try:
            tts = gTTS(text=text, lang='en')
            tts.save("temp.mp3")
            with open("temp.mp3", "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                # Autoplay ve tarayıcı dostu HTML5 Audio
                audio_html = f"""
                    <audio autoplay="true">
                        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
            st.session_state.last_spoken_text = text # Sesin çalındığını kaydet
            os.remove("temp.mp3")
        except:
            pass

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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🤖 MAND DASHBOARD")
    st.markdown(f"""<div class="stats-box">📝 <b>Words:</b> {st.session_state.stats['total_words']}<br>
    <span style='color:#fbbf24;'>⚠️ <b>Mistakes:</b> {st.session_state.stats['mistakes']}</span></div>""", unsafe_allow_html=True)
    st.divider()
    st.session_state.level = st.selectbox("LEVEL", ["A1", "A2", "B1", "B2"], 
                                         index=["A1", "A2", "B1", "B2"].index(st.session_state.level))
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.session_state.last_spoken_text = ""
        st.rerun()

# --- 6. ANA EKRAN ---
col1, col2 = st.columns([1, 5])
with col1:
    mood_emoji = "😊" if "happy" in st.session_state.mood else "😐"
    if "angry" in st.session_state.mood or "sad" in st.session_state.mood: mood_emoji = "😡"
    st.markdown(f"<div class='mood-indicator'>{mood_emoji}</div>", unsafe_allow_html=True)
with col2:
    st.title("MAND Bot v8.3 Web")

# Mesaj Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 7. GİRİŞ KONTROLÜ ---
st.divider()
audio_data = mic_recorder(start_prompt="🎤 CLICK TO SPEAK", stop_prompt="🛑 STOP", key='recorder')
user_text = st.chat_input("Or type here...")

final_prompt = None

if audio_data:
    if st.session_state.last_processed_audio_id != audio_data['id']:
        st.session_state.last_processed_audio_id = audio_data['id']
        with st.spinner("MAND is listening..."):
            with open("temp.wav", "wb") as f: f.write(audio_data['bytes'])
            with open("temp.wav", "rb") as f:
                transcript = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3", response_format="text")
            final_prompt = transcript
            if os.path.exists("temp.wav"): os.remove("temp.wav")

if user_text:
    final_prompt = user_text

# --- 8. İŞLEME VE CEVAP ---
if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user"): st.markdown(final_prompt)

    with st.chat_message("assistant"):
        ans, fix = ask_mand(final_prompt)
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.session_state.last_fix = fix
        if fix and "None" not in fix:
            st.session_state.stats["mistakes"] += 1
            st.session_state.stats["mistake_list"].append(fix)
        
        # CEVABI BURADA ÇALDIRIYORUZ
        speak(ans)
    st.rerun()

# DÜZELTME BUTONU ANALİZİ
if st.session_state.last_fix and "None" not in st.session_state.last_fix:
    if st.button("⚠️ SHOW ANALYSIS"):
        st.warning(f"Fix: {st.session_state.last_fix}")
        # Analizi de çal ama "last_spoken_text" kontrolünü geçici olarak devre dışı bırakalım
        st.session_state.last_spoken_text = "" 
        speak(st.session_state.last_fix)
        st.session_state.last_fix = ""
