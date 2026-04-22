import streamlit as st
import openai
import os
from dotenv import load_dotenv

load_dotenv()

st.title("🩺 General Physician AI Doctor")
st.caption("Describe your symptoms. I'll help guide you — but always consult a real doctor for diagnosis.")

# ── Page config (must be first) ────────────────────────────────────────────────


# ── Minimal CSS: only what Streamlit can't do natively ────────────────────────
# (bottom-fixed input, hide Streamlit chrome, chat bubble colors)
st.markdown("""
<style>
/* Hide Streamlit default chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* Bottom-fixed input area — impossible without CSS in Streamlit */
[data-testid="stBottom"] {
    background: white;
    border-top: 1px solid #e5e5e5;
    padding: 4px 0 4px;
}

/* Chat message avatars and alignment */
[data-testid="stChatMessage"] {
    padding: 4px 0;
}

/* App background */
[data-testid="stAppViewContainer"] {
    background: #f9f9f9;
}

[data-testid="stBottomBlockContainer"] {
    padding: 16px 0;
}
</style>
""", unsafe_allow_html=True)


# ── OpenRouter client ──────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return openai.OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
    )

client = get_client()

# ── Models ─────────────────────────────────────────────────────────────────────
MODELS = {
    "🔬 Llama 3.3 70B  (Open)":       "meta-llama/llama-3.3-70b-instruct",
    "⚡ Gemini Flash 2.0  (Fast)":    "google/gemini-2.0-flash-001",
    "🧠 GPT-4o Mini  (Balanced)":     "openai/gpt-4o-mini",
    "🌟 Claude Haiku 3.5  (Smart)":   "anthropic/claude-haiku-3-5",
    
}

SYSTEM_PROMPT = """You are Dr. AI, a compassionate virtual general physician assistant.
- Greet the patient warmly on the very first message only
- Ask about symptoms, duration, severity, and relevant history
- Use plain simple language — no medical jargon
- Suggest possible causes and safe home remedies or OTC options where appropriate
- Be calm, empathetic; short paragraphs; bullets only when listing multiple items
EMERGENCY: For chest pain, difficulty breathing, stroke signs, severe bleeding → say:
⚠️ Please go to the emergency room or call emergency services right now.
Always end with: "Please consult a licensed physician for proper diagnosis and treatment." """

INITIAL_MESSAGE = (
    "👋 Hello! I'm **Dr. AI**, your virtual general physician.\n\n"
    "Please describe your symptoms or how you're feeling today, "
    "and I'll guide you as best I can."
)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": INITIAL_MESSAGE}
    ]
if "api_history" not in st.session_state:
    st.session_state.api_history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]


# ── Sidebar: model selector ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.divider()
    selected_model_label = st.selectbox(
        "Model",
        options=list(MODELS.keys()),
        index=0,
        help="Choose the AI model powering Dr. AI",
    )
    st.divider()
    st.caption("🔒 Your conversation is not stored after the session ends.")
    st.caption("⚠️ Dr. AI is not a licensed physician.")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": INITIAL_MESSAGE}
        ]
        st.session_state.api_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        st.rerun()

model_id = MODELS[selected_model_label]



st.divider()


# ── Chat history ───────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🩺" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])


# ── Input (st.chat_input renders fixed at bottom natively) ────────────────────
user_input = st.chat_input("Describe your symptoms...")

if user_input:
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.api_history.append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Stream AI response
    with st.chat_message("assistant", avatar="🩺"):
        placeholder = st.empty()
        full_reply = ""

        try:
            stream = client.chat.completions.create(
                model=model_id,
                messages=st.session_state.api_history,
                temperature=0.5,
                max_tokens=600,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_reply += delta
                placeholder.markdown(full_reply + "▌")  # typing cursor

            placeholder.markdown(full_reply)

        except Exception as e:
            full_reply = f"⚠️ Couldn't reach the AI service. Please try again.\n\n_{e}_"
            placeholder.markdown(full_reply)

    st.session_state.messages.append({"role": "assistant", "content": full_reply})
    st.session_state.api_history.append({"role": "assistant", "content": full_reply})