import faiss
import numpy as np
import os
import shutil
from ollama_client import generate_embedding

# Clear previous data
shutil.rmtree("documents", ignore_errors=True)
os.makedirs("documents", exist_ok=True)

# Initialize FAISS index with correct dimension
dim = 768  # For nomic-embed-text
index = faiss.IndexFlatL2(dim)

def store_document_in_faiss(text, data_id):
    try:
        # Verify embedding generation
        print(f"Generating embedding for: {text[:50]}...")
        embedding = generate_embedding(text)
        print(f"Generated embedding length: {len(embedding)}")
        
        # Validate dimension
        if len(embedding) != dim:
            raise ValueError(f"Embedding dimension mismatch. Expected {dim}, got {len(embedding)}")
        
        # Store document
        with open(f"documents/{data_id}.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        # Add to FAISS index
        embedding_array = np.array(embedding).astype('float32').reshape(1, -1)
        index.add(embedding_array)
        print(f"Successfully stored document {data_id}. Total vectors: {index.ntotal}")
        
    except Exception as e:
        print(f"Storage failed: {str(e)}")
        raise

def retrieve_document_from_faiss(query, top_k=2):
    try:
        print(f"Generating query embedding for: {query}")
        query_embedding = generate_embedding(query)
        query_embedding = np.array(query_embedding).astype('float32').reshape(1, -1)
        
        # Normalize for better results
        faiss.normalize_L2(query_embedding)
        
        print(f"Searching index with {index.ntotal} vectors...")
        distances, indices = index.search(query_embedding, top_k)
        print(f"Search results - Distances: {distances}, Indices: {indices}")
        
        # Retrieve documents
        documents = []
        for idx in indices[0]:
            if idx >= 0:  # FAISS returns -1 for invalid indices
                doc_path = f"documents/{idx}.txt"
                if os.path.exists(doc_path):
                    with open(doc_path, "r", encoding="utf-8") as f:
                        documents.append((str(idx), f.read()))
        
        if not documents:
            print("No documents found for query")
        return documents, distances
        
    except Exception as e:
        print(f"Retrieval failed: {str(e)}")
        raise