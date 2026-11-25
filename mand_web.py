import hashlib
import io
import os
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
from openai import OpenAI
import streamlit as st

# --- CONFIG ---
API_KEY = (
    st.secrets.get("GROQ_API_KEY")
    or os.getenv("GROQ_API_KEY")
    or "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"
)

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stats" not in st.session_state:
    st.session_state.stats = {"total_words": 0, "mistakes": 0}
if "level" not in st.session_state:
    st.session_state.level = "B1"
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# --- UI DESIGN ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<div class='aiva-avatar'>🌐</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>AIVA CORE</h3>", unsafe_allow_html=True)

    st.session_state.level = st.select_slider(
        "Target Level",
        options=["A1", "A2", "B1", "B2", "C1"],
        value=st.session_state.level,
    )

    st.divider()
    st.markdown(f"""
    <div class="metric-card">
        📝 Words: {st.session_state.stats['total_words']}<br>
        ⚠️ Mistakes: {st.session_state.stats['mistakes']}
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Reset Mission", use_container_width=True):
        st.session_state.messages = []
        st.session_state.stats = {"total_words": 0, "mistakes": 0}
        st.session_state.audio_queue = None
        st.session_state.last_audio_hash = None
        st.rerun()

# --- CHAT DISPLAY ---
st.title("AIVA Intelligence")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if st.session_state.audio_queue:
    st.audio(st.session_state.audio_queue, format="audio/mp3", autoplay=True)
    st.session_state.audio_queue = None

# --- INPUT AREA ---
st.divider()
st.caption("Sesle konuşmak için mikrofonu kullan veya aşağıdan yaz:")
audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="final_v_pro")
user_query = st.chat_input("Message AIVA...")

final_text = None

if audio_bytes:
    h = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != h:
        st.session_state.last_audio_hash = h
        try:
            trans = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3",
                response_format="text",
                timeout=20.0,
            )
            if isinstance(trans, str) and trans.strip():
                final_text = trans.strip()
        except Exception as e:
            st.error(f"Ses yazıya çevrilemedi: {e}")

if user_query and user_query.strip():
    final_text = user_query.strip()

if final_text:
    st.session_state.stats["total_words"] += len(final_text.split())
    st.session_state.messages.append({"role": "user", "content": final_text})

    system_prompt = (
        f"You are AIVA, a professional English mentor. Adapt to {st.session_state.level} level. "
        "Give natural and short answers without any special formatting. "
        "If the user makes grammar/word mistakes, gently correct them briefly, "
        "and end your response with [MISTAKES: N] where N is the count of mistakes in the user's message (0 if none)."
    )

    api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages[-10:]

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=api_messages,
            timeout=15.0,
        )
        raw_ans = res.choices[0].message.content or ""

        mistake_count = 0
        ans = raw_ans
        if "[MISTAKES:" in raw_ans:
            start = raw_ans.rfind("[MISTAKES:")
            end = raw_ans.find("]", start)
            if end != -1:
                tag = raw_ans[start:end + 1]
                num_part = "".join(ch for ch in tag if ch.isdigit())
                if num_part:
                    mistake_count = int(num_part)
                ans = (raw_ans[:start] + raw_ans[end + 1:]).strip()

        st.session_state.stats["mistakes"] += mistake_count
        st.session_state.messages.append({"role": "assistant", "content": ans})

        if ans:
            mp3_fp = io.BytesIO()
            tts = gTTS(text=ans, lang="en")
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            st.session_state.audio_queue = mp3_fp.read()

        st.rerun()

    except Exception as e:
        if "429" in str(e):
            st.warning("Whoa! Too many requests. Take a deep breath and try in 5 seconds.")
        else:
            st.error(f"Connection glitch: {e}")
