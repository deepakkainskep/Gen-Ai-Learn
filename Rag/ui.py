import streamlit as st
import requests

# ----------------------------
# CONFIG
# ----------------------------
BACKEND_URL = "http://127.0.0.1:8000"
UPLOAD_API = 'http://127.0.0.1:8000/upload'
ASK_API = 'http://127.0.0.1:8000/chat'

st.set_page_config(
    page_title="📄 PDF Chat Assistant",
    page_icon="🤖",
    layout="centered"
)

# ----------------------------
# SESSION STATE
# ----------------------------
if "uploaded" not in st.session_state:
    st.session_state.uploaded = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------------
# UI HEADER
# ----------------------------
st.title("📄 PDF Question Answering Assistant")
st.caption("Upload a PDF and ask questions using RAG")

st.divider()

# ----------------------------
# PDF UPLOAD
# ----------------------------
st.subheader("1️⃣ Upload PDF")

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"]
)

if uploaded_file and st.button("📤 Upload PDF"):
    with st.spinner("Uploading PDF..."):
        files = {"file": uploaded_file}
        response = requests.post(UPLOAD_API, files=files)

    if response.status_code == 200:
        st.success("✅ PDF uploaded successfully")
        st.session_state.uploaded = True
    else:
        st.error("❌ Failed to upload PDF")

st.divider()

# ----------------------------
# CHAT SECTION
# ----------------------------
st.subheader("2️⃣ Ask Questions")

if not st.session_state.uploaded:
    st.info("Please upload a PDF before asking questions.")
else:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_question = st.chat_input("Ask a question from the PDF...")

    if user_question:
        # Show user message
        st.session_state.messages.append(
            {"role": "user", "content": user_question}
        )
        with st.chat_message("user"):
            st.markdown(user_question)

        # Call backend
        with st.spinner("Thinking..."):
            payload = {"question": user_question}
            response = requests.post(ASK_API, json=payload)

        if response.status_code == 200:
            answer = response.json().get("answer", "No answer returned")

            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
            with st.chat_message("assistant"):
                st.markdown(answer)
        else:
            st.error("❌ Error getting response from backend")
