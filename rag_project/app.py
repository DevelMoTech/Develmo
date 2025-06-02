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
import tempfile
from file_conversion import convert_to_text

app = Flask(__name__)
CORS(app)

# Configuration
DOCUMENTS_DIR = "documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.pdf': 'PDF',
    '.doc': 'Word',
    '.docx': 'Word',
    '.xls': 'Excel',
    '.xlsx': 'Excel',
    '.csv': 'CSV',
    '.txt': 'Text',
    '.ppt': 'PowerPoint',
    '.pptx': 'PowerPoint'
}

# Memory stores (only for chat history)
CHAT_HISTORY = deque(maxlen=10)
SYSTEM_PROMPT = """You are an intelligent, articulate, and knowledgeable assistant called Nexus. Your role is to provide accurate, well-structured information while maintaining a professional yet approachable tone.

Key Response Guidelines:
1. Always be precise, clear, and concise
2. Structure complex information logically with appropriate formatting
3. When referencing documents:
   - Clearly indicate which document(s) you're using
   - Provide context about why the information is relevant
4. For technical questions, provide both conceptual explanations and practical details
5. Maintain appropriate formality based on user's tone
6. Admit uncertainty when appropriate, but suggest potential solutions
7. Limit responses to 3-5 sentences unless more detail is explicitly requested

Current Date: {current_date}"""

@app.route("/store_data/", methods=["POST"])
def store_data():
    # Check if data is coming as JSON or file upload
    if request.files:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400
            
        doc_id = request.form.get("data_id", os.path.splitext(file.filename)[0])
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in SUPPORTED_EXTENSIONS:
            return jsonify({
                "status": "error",
                "message": f"Unsupported file type: {file_ext}. Supported types: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
            }), 400
            
        try:
            # Save the original file temporarily
            temp_dir = tempfile.mkdtemp()
            original_path = os.path.join(temp_dir, file.filename)
            file.save(original_path)
            
            # Convert to text
            text_content = convert_to_text(original_path, file_ext)
            
            # Clean up temporary files
            os.remove(original_path)
            os.rmdir(temp_dir)
            
            if not text_content.strip():
                return jsonify({"status": "error", "message": "Empty document after conversion"}), 400
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"File processing failed: {str(e)}"
            }), 500
    else:
        # Handle text input
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"status": "error", "message": "Invalid request format"}), 400
            
        doc_id = data.get("data_id", f"text_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        text_content = data["text"]
        
        if not text_content.strip():
            return jsonify({"status": "error", "message": "Empty document"}), 400
    
    try:
        timestamp = datetime.now().isoformat()
        
        def async_store():
            try:
                # Store in FAISS
                store_document_in_faiss(text_content, doc_id)
                
                # Save to documents directory
                with open(f"{DOCUMENTS_DIR}/{doc_id}.txt", "w", encoding="utf-8") as f:
                    f.write(f"TIMESTAMP:{timestamp}\n")
                    f.write(f"ORIGINAL_FORMAT:{SUPPORTED_EXTENSIONS.get(file_ext, 'text') if request.files else 'text'}\n")
                    f.write(text_content)
                    
            except Exception as e:
                print(f"Async storage failed: {str(e)}")
        
        threading.Thread(target=async_store).start()
        
        return jsonify({
            "status": "success",
            "stored_id": doc_id,
            "timestamp": timestamp,
            "note": "Document is being processed in background",
            "original_format": SUPPORTED_EXTENSIONS.get(file_ext, 'text') if request.files else 'text'
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/chat/", methods=["POST"])
def chat():
    if not request.json or 'message' not in request.json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400
        
    query = request.json["message"].strip()
    if not query:
        return jsonify({"status": "error", "message": "Empty message"}), 400
    
    # Add to conversation history
    CHAT_HISTORY.append({"role": "user", "content": query})
    
    try:
        # Retrieve relevant documents from FAISS
        documents, distances = retrieve_document_from_faiss(query, top_k=3)
        
        # Prepare context
        context_parts = []
        for doc_id, doc_text in documents:
            context_parts.append(
                f"DOCUMENT REFERENCE: {doc_id}\n"
                f"CONTENT EXCERPT:\n"
                f"{doc_text[:1000]}\n"  # Limit excerpt length
                f"----\n"
            )
        context = "\n".join(context_parts) if context_parts else "No relevant documents found"
        
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
        error_msg = "I encountered difficulty processing your request. Please try again or rephrase your question."
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
            for line in f:
                if line.startswith("TIMESTAMP:"):
                    return line.split("TIMESTAMP:")[1].strip()
    except:
        pass
    return datetime.now().isoformat()

def polish_response(response):
    # Remove any special markers
    response = re.sub(r'\*+', '', response)
    
    # Ensure proper punctuation
    response = response.strip()
    if not response.endswith(('.', '!', '?')):
        response += '.'
        
    # Clean up common issues
    response = re.sub(r'\n+', '\n', response)  # Remove excessive newlines
    response = re.sub(r' +', ' ', response)    # Remove multiple spaces
    
    # Capitalize first letter
    if len(response) > 0:
        response = response[0].upper() + response[1:]
        
    return response

def build_response_prompt(query, context, history):
    current_date = datetime.now().strftime("%B %d, %Y")
    system_prompt = SYSTEM_PROMPT.format(current_date=current_date)
    
    history_text = "\n".join(
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in history
    )
    
    return f"""SYSTEM INSTRUCTIONS:
{system_prompt}

CONVERSATION CONTEXT:
{history_text}

DOCUMENT CONTEXT:
{context}

USER QUERY:
{query}

RESPONSE GUIDELINES:
1. Begin with a clear, direct answer to the query
2. If using documents, reference them appropriately (e.g., "According to document X...")
3. Structure complex information with line breaks for readability
4. Maintain a professional but approachable tone
5. If unsure, say so but suggest potential avenues for finding the answer

ASSISTANT RESPONSE:"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)