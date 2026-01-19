import streamlit as st
import requests
import json

# -------------------------------
# CONFIG
# -------------------------------
API_URL = "http://127.0.0.1:8000/chat"  # change if needed

st.set_page_config(
    page_title="Multi-Agent AI System",
    page_icon="🤖",
    layout="wide"
)

# -------------------------------
# UI HEADER
# -------------------------------
st.title("🤖 Multi-Agent AI Assistant")
st.caption("Powered by LangChain / LangGraph Multi-Agent System")

# -------------------------------
# SIDEBAR
# -------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    show_steps = st.checkbox("Show Agent Reasoning", value=True)
    timeout = st.slider("API Timeout (seconds)", 5, 60, 20)

# -------------------------------
# SESSION STATE
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# CHAT HISTORY
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------
# USER INPUT
# -------------------------------
user_input = st.chat_input("Ask something to the multi-agent system...")

if user_input:
    # show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    with st.chat_message("user"):
        st.markdown(user_input)

    # call backend
    with st.chat_message("assistant"):
        with st.spinner("Agents are thinking... 🧠"):
            try:
                response = requests.post(
                    API_URL,
                    json={"question": user_input},
                    timeout=timeout
                )

                if response.status_code == 200:
                    data = response.json()

                    final_answer = data.get("final_answer", "No response")
                    agent_steps = data.get("agent_steps", [])

                    st.markdown(final_answer)

                    # show agent steps
                    if show_steps and agent_steps:
                        st.divider()
                        st.subheader("🧩 Agent Reasoning")
                        for step in agent_steps:
                            st.markdown(
                                f"**{step['agent']}** → {step['output']}"
                            )

                    st.session_state.messages.append(
                        {"role": "assistant", "content": final_answer}
                    )

                else:
                    st.error(f"API Error: {response.status_code}")

            except Exception as e:
                st.error(f"Connection failed: {e}")
