import streamlit as st
import requests
from datetime import datetime

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
</style>
""", unsafe_allow_html=True)

# Session State
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "documents" not in st.session_state:
    st.session_state.documents = {}

# Sidebar - Document Management
with st.sidebar:
    st.title("📚 Document Hub")
    with st.expander("➕ Add New Document", expanded=True):
        doc_id = st.text_input("Document ID", key="doc_id")
        doc_content = st.text_area("Content", height=150, key="doc_content")
        if st.button("Store Document", type="primary"):
            if doc_id and doc_content:
                response = requests.post(
                    "http://localhost:5010/store_data/",
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
    
    st.divider()
    st.subheader("📂 Document Library")
    for doc_id, doc in st.session_state.documents.items():
        with st.expander(f"📄 {doc_id}"):
            st.write(doc["content"])
            st.caption(f"Stored at {doc['time']}")

# Main Chat Interface
st.title("🧠 Memory-Aware RAG Chat")
st.caption("Powered by Ollama with document memory")

# Display conversation
for msg in st.session_state.conversation:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander("📌 Sources Used"):
                for source in msg["sources"]:
                    st.write(f"🔗 {source}")

# Chat input
if prompt := st.chat_input("Ask about your documents..."):
    # Add user message
    st.session_state.conversation.append({
        "role": "user",
        "content": prompt,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    
    # Get response
    with st.spinner("Consulting knowledge base..."):
        response = requests.post(
            "http://localhost:5010/chat/",
            json={"message": prompt}
        ).json()
        
        # Add assistant response
        st.session_state.conversation.append({
            "role": "assistant",
            "content": response["reply"],
            "sources": response.get("sources", []),
            "time": datetime.now().strftime("%H:%M:%S")
        })
        
        # Rerun to update UI
        st.rerun()