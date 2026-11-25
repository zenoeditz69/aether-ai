import streamlit as st
from openai import OpenAI

# --- CONFIG ---
AI_NAME = "AETHER AI"
MODEL_NAME = "google/gemma-2-9b-it:free"

st.set_page_config(page_title=AI_NAME, page_icon="💠", layout="centered")

# --- NEON CYBERPUNK CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Space Grotesk', sans-serif;
    }}
    .stApp {{
        background: radial-gradient(circle at top, #0f172a 0%, #050811 70%);
        color: #e2e8f0;
    }}
    .neon-banner {{
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 240, 255, 0.4);
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.15), inset 0 0 15px rgba(168, 85, 247, 0.1);
        border-radius: 16px;
        padding: 1.6rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }}
    .neon-title {{
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00f0ff, #a855f7, #00f0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: 2px;
    }}
    .neon-sub {{
        color: #94a3b8;
        font-size: 0.92rem;
        margin-top: 0.35rem;
    }}
    .neon-pill {{
        display: inline-block;
        margin-top: 0.75rem;
        padding: 0.25rem 0.85rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #00ff88;
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.45);
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.25);
    }}
    [data-testid="stChatMessage"] {{
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(0, 255, 136, 0.25);
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }}
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{
        color: #00ff88 !important;
        font-size: 1.02rem;
    }}
    /* Fix chat input text color */
    [data-testid="stChatInput"] textarea {{
        color: #0f172a !important;
    }}
    .stButton > button {{
        background: rgba(15, 23, 42, 0.9);
        color: #00f0ff;
        border: 1px solid rgba(0, 240, 255, 0.45);
        border-radius: 10px;
        transition: all 0.2s ease;
    }}
    .stButton > button:hover {{
        border-color: #a855f7;
        color: #ffffff;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.45);
    }}
    </style>

    <div class="neon-banner">
        <div class="neon-title">💠 {AI_NAME}</div>
        <div class="neon-sub">Next-Gen Open-Source Neural Assistant</div>
        <span class="neon-pill">⚡ YOUR PERSONAL ASSISTANT</span>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 💠 {AI_NAME} SYSTEM")
    mode = st.selectbox(
        "Neural Mode",
        ["⚡ Balanced Assistant", "💻 Code Architect", "🎓 Exam & Study Tutor"]
    )
    st.caption(f"**Active Model:** `{MODEL_NAME}`")
    st.divider()
    if st.button("🗑️ Wipe Memory", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

system_prompts = {
    "⚡ Balanced Assistant": f"You are {AI_NAME}, a sharp, helpful, modern AI assistant.",
    "💻 Code Architect": f"You are {AI_NAME}, a senior software engineer. Give clean, bug-free code with clear explanations.",
    "🎓 Exam & Study Tutor": f"You are {AI_NAME}, an expert teacher who breaks down hard concepts into simple steps."
}

# --- CONNECT TO OPENROUTER ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- ONE-CLICK DEMO PROMPTS ---
selected_prompt = None
if not st.session_state.messages:
    st.caption("✨ **Quick Demo Prompts (Click to test):**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Explain AI simply", use_container_width=True):
            selected_prompt = "Explain how open-source AI models work in 3 simple bullet points."
    with col2:
        if st.button("Python Fibonacci", use_container_width=True):
            selected_prompt = "Write a clean Python function for the Fibonacci sequence."
    with col3:
        if st.button("Study Plan", use_container_width=True):
            selected_prompt = "Give me a 3-step trick to memorize complex topics fast."

# --- DISPLAY MESSAGES ---
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "💠"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- HANDLE INPUT ---
user_input = st.chat_input(f"Transmit a prompt to {AI_NAME}...")
prompt = selected_prompt or user_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    api_messages = [{"role": "system", "content": system_prompts[mode]}] + st.session_state.messages

    with st.chat_message("assistant", avatar="💠"):
        placeholder = st.empty()
        full_reply = ""
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=api_messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_reply += chunk.choices[0].delta.content
                placeholder.markdown(full_reply + " ▌")
        placeholder.markdown(full_reply)

    st.session_state.messages.append({"role": "assistant", "content": full_reply})
    if selected_prompt:
        st.rerun()
