import streamlit as st
import requests
from datetime import datetime
import os

# UI Config
st.set_page_config(
    page_title="Memory-Aware RAG Chat",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stChatInput {position: fixed; bottom: 20px;}
    .stChatMessage {border-radius: 15px; padding: 15px;}
    .user-message {background-color: #f0f2f6;}
    .assistant-message {background-color: #e6f7ff;}
    .file-uploader {padding: 20px; border: 2px dashed #ccc; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# Session State
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None

# Backend URL
BACKEND_URL = "http://localhost:5010"

# Sidebar - Document Management
with st.sidebar:
    st.title("📚 Document Hub")
    
    # Document Upload Section
    with st.expander("📤 Upload Files", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a file (PDF, DOC, image, CSV)",
            type=["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif", "csv", "txt"],
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(f"{BACKEND_URL}/upload/", files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.current_file_id = data["file_id"]
                    st.session_state.uploaded_files[data["file_id"]] = {
                        "name": uploaded_file.name,
                        "type": data["type"],
                        "time": datetime.now().strftime("%H:%M:%S")
                    }
                    st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                else:
                    st.error(f"Error: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to backend server")
    
    # Text Document Section
    with st.expander("✍️ Add Text Document", expanded=True):
        doc_id = st.text_input("Document ID", key="doc_id")
        doc_content = st.text_area("Content", height=150, key="doc_content")
        if st.button("Store Document", type="primary"):
            if doc_id and doc_content:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/store_data/",
                        json={"text": doc_content, "data_id": doc_id}
                    )
                    if response.status_code == 200:
                        st.session_state.documents[doc_id] = {
                            "content": doc_content,
                            "time": datetime.now().strftime("%H:%M:%S")
                        }
                        st.success("Document stored in memory!")
                    else:
                        st.error(response.text)
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to backend server")
    
    st.divider()
    
    # Document Library
    st.subheader("📂 Document Library")
    
    # Uploaded Files Section
    if st.session_state.uploaded_files:
        with st.expander("📁 Uploaded Files", expanded=True):
            for file_id, file in st.session_state.uploaded_files.items():
                st.write(f"📄 {file['name']}")
                st.caption(f"Type: {file['type']} | Uploaded: {file['time']}")
    
    # Text Documents Section
    if st.session_state.documents:
        with st.expander("📝 Text Documents", expanded=True):
            for doc_id, doc in st.session_state.documents.items():
                with st.expander(f"📄 {doc_id}"):
                    st.write(doc["content"])
                    st.caption(f"Stored at {doc['time']}")

# Main Chat Interface
st.title("🧠 Memory-Aware RAG Chat")
st.caption("Powered by Ollama with document memory and file processing")

# Display conversation
for msg in st.session_state.conversation:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        
        if msg.get("file"):
            st.caption(f"📎 Attachment: {msg['file']}")
        
        if msg.get("sources"):
            with st.expander("🔍 Sources Used"):
                for source in msg["sources"]:
                    if isinstance(source, dict):
                        st.write(f"📄 {source.get('filename', source.get('id', 'Unknown'))}")
                        st.caption(f"Type: {source.get('type', 'unknown')}")
                    else:
                        st.write(f"📄 {source}")

# Chat input
if prompt := st.chat_input("Ask about your documents..."):
    # Add user message
    user_message = {
        "role": "user",
        "content": prompt,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    
    if st.session_state.current_file_id:
        file_info = st.session_state.uploaded_files.get(st.session_state.current_file_id, {})
        user_message["file"] = file_info.get("name", "Uploaded file")
    
    st.session_state.conversation.append(user_message)
    
    # Get response
    with st.spinner("🧠 Consulting knowledge base..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat/",
                json={
                    "message": prompt,
                    "file_id": st.session_state.current_file_id
                }
            ).json()
            
            # Add assistant response
            assistant_message = {
                "role": "assistant",
                "content": response["reply"],
                "sources": response.get("sources", []),
                "time": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.conversation.append(assistant_message)
            
            # Clear current file after processing
            st.session_state.current_file_id = None
            
            # Rerun to update UI
            st.rerun()
        except requests.exceptions.ConnectionError:
            st.error("Failed to connect to backend server")
            st.session_state.conversation.pop()  # Remove the last user message

# Clear button
if st.button("🧹 Clear Chat History", use_container_width=True):
    st.session_state.conversation = []
    st.rerun()