from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import numpy as np
from datetime import datetime
from collections import deque
from ollama_client import generate_embedding, generate_response
from faiss_client import store_document_in_faiss, retrieve_document_from_faiss
import re
import threading
import random

app = Flask(__name__)
CORS(app)

# Configuration
DOCUMENTS_DIR = "documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Memory stores (only for chat history)
CHAT_HISTORY = deque(maxlen=10)
SYSTEM_PROMPT = """You are a friendly and helpful AI assistant. Be warm, polite, and conversational while providing accurate information. 
If you reference documents, mention which ones you're using. Keep responses concise but helpful."""

@app.route("/store_data/", methods=["POST"])
def store_data():
    data = request.get_json()
    doc_id = data["data_id"]
    text = data["text"]
    
    if not text.strip():
        return jsonify({"status": "error", "message": "Empty document"}), 400
    
    try:
        timestamp = datetime.now().isoformat()
        
        def async_store():
            try:
                store_document_in_faiss(text, doc_id)
            except Exception as e:
                print(f"Async storage failed: {str(e)}")
        
        threading.Thread(target=async_store).start()
        
        return jsonify({
            "status": "success",
            "stored_id": doc_id,
            "timestamp": timestamp,
            "note": "Document is being processed in background"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/chat/", methods=["POST"])
def chat():
    query = request.json["message"].strip()
    lower_query = query.lower()
    
    # Add to conversation history
    CHAT_HISTORY.append({"role": "user", "content": query})
    
    try:
        # Retrieve relevant documents from FAISS
        documents, distances = retrieve_document_from_faiss(query, top_k=3)
        
        # Prepare context
        context_parts = []
        for doc_id, doc_text in documents:
            context_parts.append(
                f"Document {doc_id}:\n"
                f"{doc_text}\n"
                f"----\n"
            )
        context = "\n".join(context_parts)
        
        # Generate response
        prompt = build_response_prompt(query, context, CHAT_HISTORY)
        response = generate_response(prompt)
        
        # Post-process response
        response = polish_response(response)
        
        # Store conversation
        CHAT_HISTORY.append({"role": "assistant", "content": response})
        
        return jsonify({
            "reply": response,
            "sources": [doc[0] for doc in documents],
            "timestamps": [get_document_timestamp(doc[0]) for doc in documents],
            "confidence_scores": [float(1/(1+d)) for d in distances[0]] if distances else []
        })
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error processing your request."
        print(f"Error in chat endpoint: {str(e)}")
        CHAT_HISTORY.append({"role": "assistant", "content": error_msg})
        return jsonify({
            "reply": error_msg,
            "sources": [],
            "timestamps": []
        }), 500

def get_document_timestamp(doc_id):
    try:
        with open(f"{DOCUMENTS_DIR}/{doc_id}.txt", "r", encoding="utf-8") as f:
            first_line = f.readline()
            if first_line.startswith("TIMESTAMP:"):
                return first_line.split("TIMESTAMP:")[1].strip()
    except:
        pass
    return datetime.now().isoformat()

def polish_response(response):
    # Remove any special markers
    response = response.replace("*", "")
    
    # Ensure proper punctuation
    if not response.endswith(('.', '!', '?')):
        response = response.rstrip() + '.'
        
    # Remove any awkward phrasing
    response = response.replace("the document states that", "according to the information")
    response = response.replace("as per the document", "based on what I found")
    
    return response.strip()

def build_response_prompt(query, context, history):
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    
    return f"""System: {SYSTEM_PROMPT}

Context Documents:
{context if context else 'No specific documents found'}

Conversation History:
{history_text}

User Query: {query}

Guidelines:
1. Respond conversationally using "I" and "you"
2. If using documents, mention relevant ones briefly
3. Keep responses under 3 sentences unless more is needed
4. Be polite and helpful
5. If unsure, say so but still try to help

Assistant Response:"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)