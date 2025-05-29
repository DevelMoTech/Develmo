import faiss
import numpy as np
import os
import pickle
from datetime import datetime
from ollama_client import generate_embedding

# Configuration
DIMENSION = 768
INDEX_FILE = "faiss_index.index"
META_FILE = "faiss_meta.pkl"
MAX_DOCS_IN_MEMORY = 1000
SAVE_INTERVAL = 50

class FaissDocumentStore:
    def __init__(self):
        self.index = None
        self.document_metadata = {}
        self.doc_id_to_index = {}  # Maps doc_id to FAISS index position
        self.next_index = 0
        self.ops_since_last_save = 0
        self.load_index()

    def load_index(self):
        try:
            if os.path.exists(INDEX_FILE):
                self.index = faiss.read_index(INDEX_FILE)
                self.next_index = self.index.ntotal
            
            if os.path.exists(META_FILE):
                with open(META_FILE, "rb") as f:
                    data = pickle.load(f)
                    self.document_metadata = data.get("metadata", {})
                    self.doc_id_to_index = data.get("id_map", {})
            
            if self.index is None:
                self.index = faiss.IndexFlatIP(DIMENSION)  # Using Inner Product for similarity
            
            print(f"Loaded index with {len(self.document_metadata)} documents")
        except Exception as e:
            print(f"Error loading index: {e}")
            self._initialize_new_index()

    def _initialize_new_index(self):
        self.index = faiss.IndexFlatIP(DIMENSION)
        self.document_metadata = {}
        self.doc_id_to_index = {}
        self.next_index = 0
        print("Initialized new FAISS index")

    def save_index(self):
        try:
            faiss.write_index(self.index, INDEX_FILE)
            with open(META_FILE, "wb") as f:
                pickle.dump({
                    "metadata": self.document_metadata,
                    "id_map": self.doc_id_to_index
                }, f)
            self.ops_since_last_save = 0
            print(f"Saved index with {len(self.document_metadata)} documents")
        except Exception as e:
            print(f"Error saving index: {e}")

    def store_document(self, text, doc_id):
        try:
            if doc_id in self.document_metadata:
                print(f"Document {doc_id} already exists - updating")
                self._remove_document(doc_id)

            timestamp = datetime.now().isoformat()
            
            # Store metadata immediately
            self.document_metadata[doc_id] = {
                "text": text,
                "timestamp": timestamp,
                "index_pos": self.next_index
            }
            self.doc_id_to_index[doc_id] = self.next_index
            
            # Save document to disk
            self._save_document_to_disk(doc_id, text, timestamp)
            
            # Generate embedding and add to index
            embedding = generate_embedding(text)
            if len(embedding) != DIMENSION:
                raise ValueError(f"Invalid embedding dimension: {len(embedding)}")
                
            embedding_array = np.array(embedding).astype('float32').reshape(1, -1)
            faiss.normalize_L2(embedding_array)
            self.index.add(embedding_array)
            self.next_index += 1
            
            # Periodic save
            self.ops_since_last_save += 1
            if self.ops_since_last_save >= SAVE_INTERVAL:
                self.save_index()
                
            return True
        except Exception as e:
            print(f"Error storing document: {e}")
            return False

    def _remove_document(self, doc_id):
        """Mark document as removed (we don't actually remove from FAISS index)"""
        if doc_id in self.document_metadata:
            del self.document_metadata[doc_id]
        if doc_id in self.doc_id_to_index:
            del self.doc_id_to_index[doc_id]

    def _save_document_to_disk(self, doc_id, text, timestamp):
        os.makedirs("documents", exist_ok=True)
        with open(f"documents/{doc_id}.txt", "w", encoding="utf-8") as f:
            f.write(f"TIMESTAMP:{timestamp}\n")
            f.write(text)

    def retrieve_documents(self, query, top_k=3):
        try:
            query_embedding = generate_embedding(query)
            query_embedding = np.array(query_embedding).astype('float32').reshape(1, -1)
            faiss.normalize_L2(query_embedding)
            
            # Search with larger k to account for potential empty results
            distances, indices = self.index.search(query_embedding, top_k*2)
            
            results = []
            seen_docs = set()
            
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:
                    continue
                    
                # Find doc_id for this index position
                doc_id = next((did for did, pos in self.doc_id_to_index.items() if pos == idx), None)
                
                if doc_id and doc_id in self.document_metadata and doc_id not in seen_docs:
                    doc = self.document_metadata[doc_id]
                    results.append((doc_id, doc["text"], float(distance), doc["timestamp"]))
                    seen_docs.add(doc_id)
                    if len(results) >= top_k:
                        break
            
            # Sort by similarity score (higher is better)
            results.sort(key=lambda x: x[2], reverse=True)
            
            return results
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []

# Global instance
document_store = FaissDocumentStore()

def store_document_in_faiss(text, doc_id):
    return document_store.store_document(text, doc_id)

def retrieve_document_from_faiss(query, top_k=10):
    results = document_store.retrieve_documents(query, top_k)
    documents = [(doc[0], doc[1]) for doc in results]
    distances = [[doc[2] for doc in results]]
    return documents, distances