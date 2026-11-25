"""AETHER AI — a neon-styled Streamlit chatbot powered by OpenRouter.

Run with:  streamlit run app.py
Needs:     .streamlit/secrets.toml  ->  OPENROUTER_API_KEY = "sk-or-..."
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterator

import openai
import streamlit as st
from openai import OpenAI

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
AI_NAME = "AETHER AI"
DEFAULT_MODEL = "openrouter/free"
OPENROUTER_URL = "https://openrouter.ai/api/v1"

MODES: dict[str, str] = {
    "⚡ Balanced Assistant": (
        f"You are {AI_NAME}, a sharp, helpful, modern AI assistant. "
        "Be accurate and concise, and use Markdown when it improves clarity."
    ),
    "💻 Code Architect": (
        f"You are {AI_NAME}, a senior software engineer. Give clean, correct, "
        "well-structured code in fenced code blocks, then a short explanation of "
        "how it works and any edge cases. Ask for missing details instead of guessing."
    ),
    "🎓 Exam & Study Tutor": (
        f"You are {AI_NAME}, an expert teacher. Break hard concepts into simple "
        "steps, use analogies and small examples, and finish with a quick "
        "self-check question."
    ),
    "✍️ Creative Writer": (
        f"You are {AI_NAME}, an imaginative writing partner. Write vivid, original "
        "text, match the requested tone, and offer one idea to take it further."
    ),
}

DEMO_PROMPTS: list[tuple[str, str]] = [
    ("Explain AI simply", "Explain how open-source AI models work in 3 simple bullet points."),
    ("Python Fibonacci", "Write a clean Python function for the Fibonacci sequence."),
    ("Study Plan", "Give me a 3-step trick to memorize complex topics fast."),
]

st.set_page_config(page_title=AI_NAME, page_icon="💠", layout="centered")

# ----------------------------------------------------------------------------
# STYLING  (plain string, so CSS braces don't need escaping)
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(168, 85, 247, 0.14) 0%, transparent 45%),
        radial-gradient(circle at 85% 0%, rgba(0, 240, 255, 0.12) 0%, transparent 45%),
        #050811;
    color: #e2e8f0;
}

/* Hide default Streamlit chrome but keep the sidebar toggle */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

section[data-testid="stSidebar"] {
    background: rgba(8, 12, 24, 0.95);
    border-right: 1px solid rgba(0, 240, 255, 0.2);
}

/* Banner */
.neon-banner {
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 240, 255, 0.4);
    box-shadow: 0 0 25px rgba(0, 240, 255, 0.15), inset 0 0 15px rgba(168, 85, 247, 0.1);
    border-radius: 16px;
    padding: 1.6rem 1.2rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.neon-title {
    font-size: 2.3rem;
    font-weight: 700;
    letter-spacing: 2px;
    margin: 0;
    background: linear-gradient(90deg, #00f0ff, #a855f7, #00f0ff);
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: sheen 6s linear infinite;
}
@keyframes sheen { to { background-position: 200% center; } }
@media (prefers-reduced-motion: reduce) { .neon-title { animation: none; } }
.neon-sub { color: #94a3b8; font-size: 0.92rem; margin-top: 0.35rem; }
.neon-pill {
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
}

/* Chat bubbles: assistant = green glow, user = cyan glow */
[data-testid="stChatMessage"] {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(0, 255, 136, 0.28);
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-color: rgba(0, 240, 255, 0.35);
    background: rgba(12, 22, 44, 0.9);
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li { color: #d9f99d; font-size: 1.02rem; line-height: 1.6; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p { color: #bae6fd; }
[data-testid="stChatMessage"] code { color: #00f0ff; }
[data-testid="stChatMessage"] pre {
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 10px;
}

/* Chat input: dark field, readable light text */
[data-testid="stChatInput"] {
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 14px;
}
[data-testid="stChatInput"] textarea { color: #e2e8f0 !important; }
[data-testid="stChatInput"] textarea::placeholder { color: #64748b !important; }
[data-testid="stChatInput"]:focus-within {
    border-color: #a855f7;
    box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
    background: rgba(15, 23, 42, 0.9);
    color: #00f0ff;
    border: 1px solid rgba(0, 240, 255, 0.45);
    border-radius: 10px;
    transition: all 0.2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #a855f7;
    color: #ffffff;
    box-shadow: 0 0 15px rgba(168, 85, 247, 0.45);
}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
    outline: 2px solid #00ff88;
    outline-offset: 2px;
}
</style>
"""

BANNER = f"""
<div class="neon-banner">
    <div class="neon-title">💠 {AI_NAME}</div>
    <div class="neon-sub">Next-Gen Neural Assistant</div>
    <span class="neon-pill">⚡ YOUR PERSONAL ASSISTANT</span>
</div>
"""

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(BANNER, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def get_api_key() -> str | None:
    """Read the key from Streamlit secrets, falling back to an env variable."""
    try:
        key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:  # missing secrets file or missing key
        key = os.environ.get("OPENROUTER_API_KEY")
    return key or None


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> OpenAI:
    """One shared client instead of rebuilding it on every rerun."""
    return OpenAI(
        base_url=OPENROUTER_URL,
        api_key=api_key,
        timeout=60.0,
        max_retries=2,
        default_headers={"X-Title": AI_NAME},
    )


def stream_reply(
    client: OpenAI,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Iterator[str]:
    """Yield text chunks from the model as they arrive."""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def friendly_error(exc: Exception) -> str:
    """Turn API exceptions into messages a user can act on."""
    if isinstance(exc, openai.AuthenticationError):
        return "Your API key was rejected. Check `OPENROUTER_API_KEY` in your secrets."
    if isinstance(exc, openai.RateLimitError):
        return "Rate limit reached (free models are limited). Wait a moment and try again."
    if isinstance(exc, openai.APIConnectionError):
        return "Could not reach OpenRouter. Check your internet connection."
    if isinstance(exc, openai.APITimeoutError):
        return "The model took too long to respond. Try again."
    if isinstance(exc, openai.NotFoundError):
        return "That model ID was not found. Check the model name in Advanced settings."
    if isinstance(exc, openai.APIStatusError):
        return f"The API returned an error ({exc.status_code}). Try again or pick another model."
    return f"Something went wrong: {exc}"


def queue_prompt(text: str) -> None:
    """Button callback: remember which demo prompt was clicked."""
    st.session_state.pending_prompt = text


def wipe_chat() -> None:
    st.session_state.messages = []


def regenerate() -> None:
    """Drop the last assistant reply so it gets generated again."""
    msgs = st.session_state.messages
    if msgs and msgs[-1]["role"] == "assistant":
        msgs.pop()
        st.session_state.regen = True


def chat_as_markdown(messages: list[dict[str, str]]) -> str:
    lines = [f"# {AI_NAME} chat — {datetime.now():%Y-%m-%d %H:%M}", ""]
    for m in messages:
        who = "You" if m["role"] == "user" else AI_NAME
        lines += [f"**{who}:**", "", m["content"], ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# STATE
# ----------------------------------------------------------------------------
st.session_state.setdefault("messages", [])

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 💠 {AI_NAME} SYSTEM")
    mode = st.selectbox("Neural Mode", list(MODES))

    with st.expander("Advanced settings"):
        model_name = st.text_input(
            "Model ID",
            value=DEFAULT_MODEL,
            help="Any model ID from openrouter.ai/models, e.g. 'openrouter/free'.",
        ).strip() or DEFAULT_MODEL
        temperature = st.slider(
            "Creativity", 0.0, 1.5, 0.7, 0.05,
            help="Lower is more precise, higher is more creative.",
        )
        max_tokens = st.slider("Max reply length (tokens)", 256, 4096, 1500, 128)
        history_limit = st.slider(
            "Messages remembered", 4, 40, 20, 2,
            help="Only the most recent messages are sent to the model.",
        )

    st.caption(f"**Active model:** `{model_name}`")
    st.caption(f"**Messages in chat:** {len(st.session_state.messages)}")
    st.divider()

    has_reply = bool(st.session_state.messages) and st.session_state.messages[-1]["role"] == "assistant"
    st.button("🔄 Regenerate reply", on_click=regenerate, disabled=not has_reply, use_container_width=True)
    st.download_button(
        "💾 Download chat",
        data=chat_as_markdown(st.session_state.messages),
        file_name="aether-chat.md",
        mime="text/markdown",
        disabled=not st.session_state.messages,
        use_container_width=True,
    )
    st.button("🗑️ Wipe Memory", on_click=wipe_chat, use_container_width=True)

# ----------------------------------------------------------------------------
# API CLIENT
# ----------------------------------------------------------------------------
api_key = get_api_key()
if not api_key:
    st.error(
        "No API key found. Add `OPENROUTER_API_KEY = \"sk-or-...\"` to "
        "`.streamlit/secrets.toml` (or set it as an environment variable), then reload."
    )
    st.stop()
client = get_client(api_key)

# ----------------------------------------------------------------------------
# DEMO PROMPTS (only on an empty chat)
# ----------------------------------------------------------------------------
if not st.session_state.messages:
    st.caption("✨ **Quick demo prompts — click to test:**")
    for col, (label, text) in zip(st.columns(len(DEMO_PROMPTS)), DEMO_PROMPTS):
        with col:
            st.button(label, on_click=queue_prompt, args=(text,), use_container_width=True)

# ----------------------------------------------------------------------------
# INPUT  (handled before rendering so history is always up to date)
# ----------------------------------------------------------------------------
typed = st.chat_input(f"Transmit a prompt to {AI_NAME}...")
prompt = st.session_state.pop("pending_prompt", None) or typed
regen_requested = st.session_state.pop("regen", False)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

# ----------------------------------------------------------------------------
# RENDER HISTORY
# ----------------------------------------------------------------------------
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "💠"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------------------------------------------------------------------
# GENERATE REPLY
# ----------------------------------------------------------------------------
messages = st.session_state.messages
if (prompt or regen_requested) and messages and messages[-1]["role"] == "user":
    recent = messages[-history_limit:]
    api_messages = [{"role": "system", "content": MODES[mode]}, *recent]

    with st.chat_message("assistant", avatar="💠"):
        try:
            reply = st.write_stream(
                stream_reply(client, model_name, api_messages, temperature, max_tokens)
            )
        except Exception as exc:  # noqa: BLE001 - show any failure to the user
            st.error(friendly_error(exc))
            reply = None

    if reply:
        messages.append({"role": "assistant", "content": reply})
        st.rerun()  # refresh sidebar buttons and message count
    else:
        # Remove the unanswered prompt so the user can simply resend it.
        if prompt:
            messages.pop()

       
        
