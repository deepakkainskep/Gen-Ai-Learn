import streamlit as st
import requests
import json
from datetime import datetime


API_URL = "http://127.0.0.1:8000/chatbot"

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

# -------------------------------
# Custom CSS
# -------------------------------
st.markdown("""
<style>
.timestamp {
    font-size: 0.7rem;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.title("⚙️ Settings")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []

    st.divider()
    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=2)
        st.success("Backend Connected")
    except:
        st.error("Backend Offline")

# -------------------------------
# Session State
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# Chat History
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        st.markdown(
            f"<div class='timestamp'>{msg['time']}</div>",
            unsafe_allow_html=True
        )

# -------------------------------
# Streaming API Call
# -------------------------------
def stream_fastapi(user_input: str):
    with requests.post(
        API_URL,
        json={"user_input": user_input},
        stream=True,
        timeout=60
    ) as response:
        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    data = json.loads(line)
                    yield data.get("response", "")
                except json.JSONDecodeError:
                    yield line

# -------------------------------
# User Input
# -------------------------------
user_input = st.chat_input("Type your message...")

if user_input:
    now = datetime.now().strftime("%H:%M")

    # ✅ Show user message instantly
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

    # ✅ Stream assistant
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        for chunk in stream_fastapi(user_input):
            full_response += chunk
            placeholder.markdown(full_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "time": now
    })




