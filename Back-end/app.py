from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import numpy as np
from datetime import datetime
from collections import deque
from ollama_client import generate_embedding, generate_response
import tempfile
import filetype
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Memory stores
DOCUMENT_STORE = {}  # Now stores file content temporarily
EMBEDDING_STORE = {}
CHAT_HISTORY = deque(maxlen=10)  # Last 10 conversations
UPLOADED_FILES = {}  # Stores file content temporarily during processing

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 
    'jpg', 'jpeg', 'png', 'gif', 
    'csv', 'txt'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/store_data/", methods=["POST"])
def store_data():
    data = request.get_json()
    doc_id = data["data_id"]
    text = data["text"]
    
    # Store in memory only (no disk storage)
    DOCUMENT_STORE[doc_id] = {
        "text": text,
        "timestamp": datetime.now().isoformat()
    }
    
    # Generate and store embedding
    embedding = generate_embedding(text)
    EMBEDDING_STORE[doc_id] = embedding
    
    return jsonify({"status": "success", "stored_id": doc_id})

@app.route("/upload/", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Secure the filename and create a temporary file ID
        filename = secure_filename(file.filename)
        file_id = f"file_{datetime.now().timestamp()}_{filename}"
        
        # Read file content (for text-based files)
        if filename.lower().endswith(('.pdf', '.doc', '.docx', '.csv', '.txt')):
            try:
                # For simplicity, we'll just read text files directly
                # In production, you'd use libraries like PyPDF2, python-docx, etc.
                if filename.lower().endswith('.txt'):
                    content = file.read().decode('utf-8')
                else:
                    # For other formats, we'll just store a reference
                    content = f"File [{filename}] uploaded. Content processing would happen here."
                
                UPLOADED_FILES[file_id] = {
                    "filename": filename,
                    "content": content,
                    "type": "text",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return jsonify({"error": f"Error processing file: {str(e)}"}), 500
        
        # Handle images
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            UPLOADED_FILES[file_id] = {
                "filename": filename,
                "content": None,  # We don't store the actual image data
                "type": "image",
                "timestamp": datetime.now().isoformat()
            }
        
        # Generate embedding for the file (either from text content or image description)
        if UPLOADED_FILES[file_id]["type"] == "text":
            embedding = generate_embedding(UPLOADED_FILES[file_id]["content"])
        else:
            # For images, we might generate an embedding from a description
            embedding = generate_embedding(f"Image file: {filename}")
        
        EMBEDDING_STORE[file_id] = embedding
        
        return jsonify({
            "status": "success",
            "file_id": file_id,
            "filename": filename,
            "type": UPLOADED_FILES[file_id]["type"]
        })
    
    return jsonify({"error": "File type not allowed"}), 400

@app.route("/chat/", methods=["POST"])
def chat():
    data = request.json
    query = data.get("message")
    file_id = data.get("file_id")
    
    # Add to conversation history
    CHAT_HISTORY.append({"role": "user", "content": query, "file_id": file_id})
    
    # Retrieve relevant documents and files
    results = []
    
    # Check documents
    for doc_id, embedding in EMBEDDING_STORE.items():
        similarity = cosine_similarity(embedding, generate_embedding(query))
        
        # Get content from appropriate store
        if doc_id in DOCUMENT_STORE:
            content = DOCUMENT_STORE[doc_id]["text"]
        elif doc_id in UPLOADED_FILES:
            content = UPLOADED_FILES[doc_id]["content"] or UPLOADED_FILES[doc_id]["filename"]
        else:
            continue
            
        results.append((doc_id, similarity, content))
    
    # Get top 2 most relevant
    results.sort(key=lambda x: x[1], reverse=True)
    relevant_docs = results[:2]
    
    # Generate response
    prompt = build_prompt(query, relevant_docs, CHAT_HISTORY, file_id)
    response = generate_response(prompt)
    
    # Store conversation
    CHAT_HISTORY.append({"role": "assistant", "content": response})
    
    # Prepare response with sources
    sources = []
    for doc in relevant_docs:
        doc_id = doc[0]
        if doc_id in DOCUMENT_STORE:
            sources.append({
                "id": doc_id,
                "type": "text",
                "timestamp": DOCUMENT_STORE[doc_id]["timestamp"]
            })
        elif doc_id in UPLOADED_FILES:
            sources.append({
                "id": doc_id,
                "type": UPLOADED_FILES[doc_id]["type"],
                "filename": UPLOADED_FILES[doc_id]["filename"],
                "timestamp": UPLOADED_FILES[doc_id]["timestamp"]
            })
    
    return jsonify({
        "reply": response,
        "sources": sources
    })

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def build_prompt(query, docs, history, current_file_id=None):
    # Build context from relevant documents
    context_parts = []
    for doc in docs:
        doc_id = doc[0]
        if doc_id in UPLOADED_FILES:
            file_info = UPLOADED_FILES[doc_id]
            if file_info["type"] == "image":
                context_parts.append(f"Image file: {file_info['filename']} (relevance: {doc[1]:.2f})")
            else:
                context_parts.append(f"File {file_info['filename']} (relevance: {doc[1]:.2f}):\n{doc[2]}")
        else:
            context_parts.append(f"Document {doc_id} (relevance: {doc[1]:.2f}):\n{doc[2]}")
    
    context = "\n".join(context_parts)
    
    # Build history
    history_text = []
    for msg in history:
        entry = f"{msg['role']}: {msg['content']}"
        if msg.get('file_id'):
            file_info = UPLOADED_FILES.get(msg['file_id'], {})
            entry += f" [Attached file: {file_info.get('filename', 'unknown')}]"
        history_text.append(entry)
    
    history_str = "\n".join(history_text)
    
    # Add current file context if available
    file_context = ""
    if current_file_id and current_file_id in UPLOADED_FILES:
        file_info = UPLOADED_FILES[current_file_id]
        if file_info["type"] == "image":
            file_context = f"\nUser has attached an image file: {file_info['filename']}"
        else:
            file_context = f"\nUser has attached a file: {file_info['filename']}\nContent: {file_info['content']}"
    
    return f"""System: You are a knowledgeable assistant with access to these documents:
{context}

Conversation History:
{history_str}
{file_context}

User: {query}
Assistant:"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)