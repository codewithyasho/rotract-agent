import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chatbot import get_chatbot_executor

app = FastAPI(title="Rotaract Event Chatbot API")

# Initialize the chatbot executor when the app starts
chatbot = get_chatbot_executor()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # We use asyncio.to_thread to run the synchronous invoke method 
        # in a background thread so it doesn't block the FastAPI async event loop
        response = await asyncio.to_thread(chatbot.invoke, {"input": request.message})
        return ChatResponse(response=response["output"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "ok", "message": "Event Chatbot API is running on Hugging Face Spaces!"}
