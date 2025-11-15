# app.py - Clean Fixed Version with Modern UI (Streamlit 1.32+)

import streamlit as st
import os

from logic import (
    initialize_session,
    handle_user_message,
    EXIT_KEYWORDS,
    save_submission_if_complete,
)
from utils import load_env_defaults

# ---------------------------------------------------------
# INITIAL SETUP
# ---------------------------------------------------------
load_env_defaults()
st.set_page_config(
    page_title="TalentScout — Hiring Assistant",
    page_icon="🤖",
    layout="wide",
)

initialize_session()

# ---------------------------------------------------------
# HEADER UI + STYLE
# ---------------------------------------------------------
st.markdown("""
<style>
.chat-bubble-user {
    background-color: #DCF8C6;
    padding: 10px 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    max-width: 80%;
}
.chat-bubble-assistant {
    background-color: #F1F0F0;
    padding: 10px 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    max-width: 80%;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 TalentScout — Hiring Assistant")
st.caption("Smart AI interviewer for first-round candidate screening.")

# ---------------------------------------------------------
# LAYOUT (CHAT LEFT, INFO RIGHT)
# ---------------------------------------------------------
col_chat, col_info = st.columns([3, 1])

# ---------------------------------------------------------
# RIGHT COLUMN — INFO PANEL
# ---------------------------------------------------------
with col_info:
    st.markdown("### ⚙️ Session Info")
    mode = "LIVE (OpenAI)" if st.session_state['live_mode'] else "MOCK"
    st.write(f"**Mode:** {mode}")
    st.write(f"**Exit words:** {', '.join(EXIT_KEYWORDS)}")

    if st.button("🔄 Reset Conversation"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        initialize_session()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📦 Storage")
    st.write(f"Saving to: `{os.environ.get('STORAGE_FILE','data/submissions.json')}`")

    st.markdown("---")
    st.markdown("### 🚀 Deployment Tips")
    st.markdown("""
- Set `OPENAI_API_KEY`  
- Run with: `streamlit run app.py`
    """)

# ---------------------------------------------------------
# LEFT COLUMN — CHAT
# ---------------------------------------------------------
with col_chat:
    st.markdown("### 💬 Conversation")

    chat_area = st.container()

    # Chat Renderer
    with chat_area:
        for msg in st.session_state["history"]:
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='chat-bubble-user'><b>You:</b><br>{msg['content']}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='chat-bubble-assistant'><b>Assistant:</b><br>{msg['content']}</div>",
                    unsafe_allow_html=True,
                )

    # ---------------------------------------------------------
    # INPUT AREA (BOTTOM CHAT BOX)
    # ---------------------------------------------------------
    user_text = st.chat_input("Type your message here...")

    if user_text:
        with st.spinner("Thinking..."):
            reply, finished = handle_user_message(user_text)

        st.rerun()  # re-render interface

        if finished:
            status = save_submission_if_complete()
            if status:
                st.success("✔ Submission saved successfully!")
            else:
                st.warning("ℹ Submission incomplete — not saved.")

    st.markdown("---")

    st.markdown("### ⚡ Quick Commands")
    c1, c2, c3 = st.columns(3)
    if c1.button("Start"):
        handle_user_message("/start")
        st.rerun()
    if c2.button("Sample Stack"):
        handle_user_message("Python, Django, React, PostgreSQL, Docker")
        st.rerun()
    if c3.button("Exit"):
        handle_user_message("bye")
        st.rerun()
