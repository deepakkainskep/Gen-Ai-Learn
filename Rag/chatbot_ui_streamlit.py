import streamlit as st
import requests
from datetime import datetime
import time

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
.timestamp {
    font-size: 0.7rem;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("⚙️ Settings")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- Session ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- Chat History ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        st.markdown(
            f"<div class='timestamp'>{msg['time']}</div>",
            unsafe_allow_html=True
        )

# ---------------- Backend Call ----------------
def call_backend(question: str) -> str:
    payload = {
        "question": question  # ✅ matches backend schema
    }

    response = requests.post(API_URL, json=payload, timeout=120)
    response.raise_for_status()

    return response.json()["answer"]

# ---------------- User Input ----------------
user_input = st.chat_input("Type your message...")

if user_input:
    now = datetime.now().strftime("%H:%M")

    # USER MESSAGE
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": now
    })

    with st.chat_message("user"):
        st.markdown(user_input)
        st.markdown(
            f"<div class='timestamp'>{now}</div>",
            unsafe_allow_html=True
        )

    # ASSISTANT (SIMULATED STREAMING)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        answer = call_backend(user_input)

        for word in answer.split():
            full_response += word + " "
            placeholder.markdown(full_response + "▌")
            time.sleep(0.05)  # typing effect

        placeholder.markdown(full_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "time": now
    })


