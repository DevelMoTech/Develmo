# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from faiss_client import store_data_in_faiss, retrieve_data_from_faiss
from ollama_client import generate_response

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

class StoreDataRequest(BaseModel):
    text: str
    data_id: str

# Route to store data (documents) in FAISS
@app.post("/store_data/")
async def store_data(request: StoreDataRequest):
    try:
        store_data_in_faiss(request.text, request.data_id)
        return {"message": "Data stored successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Route to chat and retrieve response based on user query
@app.post("/chat/")
async def chat(request: ChatRequest):
    try:
        # Step 1: Retrieve relevant data from FAISS
        distances, indices = retrieve_data_from_faiss(request.message, top_k=5)

        # Step 2: Use retrieved documents to augment the user query
        context = "\n".join([f"Document {i} with similarity score {dist}" for i, dist in zip(indices[0], distances[0])])

        # Step 3: Formulate the prompt for Llama 3.2 Vision to generate the response
        prompt = f"{context}\n\nUser: {request.message}\nBot:"

        # Step 4: Generate a response using Llama 3.2 Vision
        response = generate_response(prompt)

        return {"reply": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
