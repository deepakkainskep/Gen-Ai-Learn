<<<<<<< HEAD
import streamlit as st
import requests
from datetime import datetime

# -------------------------------
# Config
# -------------------------------
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
.chat-container {
    max-width: 720px;
    margin: auto;
}
.timestamp {
    font-size: 0.75rem;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("AI Chatbot UI powered by FastAPI")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Status")

    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=3)
        st.success("Backend Connected")
    except:
        st.error("Backend Offline")

# -------------------------------
# Title
# -------------------------------
st.title("🤖 AI Chatbot")
st.caption("Streamlit UI + FastAPI Backend")

# -------------------------------
# Session State
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# Show Chat History
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        st.markdown(
            f"<div class='timestamp'>{msg['time']}</div>",
            unsafe_allow_html=True
        )

# -------------------------------
# Backend Call
# -------------------------------
def call_fastapi(user_input: str) -> str:
    payload = {"user_input": user_input}

    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "No response from backend")
    except requests.exceptions.HTTPError as e:
        return f"❌ Backend error: {e.response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# -------------------------------
# User Input
# -------------------------------
user_input = st.chat_input("Type your message...")

if user_input:
    now = datetime.now().strftime("%H:%M")

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": now
    })

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            bot_reply = call_fastapi(user_input)
            st.markdown(bot_reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply,
        "time": now
    })

    st.rerun()
=======
import streamlit as st
import requests
from datetime import datetime

# -------------------------------
# Config
# -------------------------------
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
.chat-container {
    max-width: 720px;
    margin: auto;
}
.timestamp {
    font-size: 0.75rem;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("AI Chatbot UI powered by FastAPI")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Status")

    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=3)
        st.success("Backend Connected")
    except:
        st.error("Backend Offline")

# -------------------------------
# Title
# -------------------------------
st.title("🤖 AI Chatbot")
st.caption("Streamlit UI + FastAPI Backend")

# -------------------------------
# Session State
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# Show Chat History
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        st.markdown(
            f"<div class='timestamp'>{msg['time']}</div>",
            unsafe_allow_html=True
        )

# -------------------------------
# Backend Call
# -------------------------------
def call_fastapi(user_input: str) -> str:
    payload = {"user_input": user_input}

    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "No response from backend")
    except requests.exceptions.HTTPError as e:
        return f"❌ Backend error: {e.response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# -------------------------------
# User Input
# -------------------------------
user_input = st.chat_input("Type your message...")

if user_input:
    now = datetime.now().strftime("%H:%M")

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": now
    })

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            bot_reply = call_fastapi(user_input)
            st.markdown(bot_reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply,
        "time": now
    })

    st.rerun()
>>>>>>> 352c8d52bbf0ec2e22557e35926f17d3fa6233a4
