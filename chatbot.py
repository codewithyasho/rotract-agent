import os
from typing import List, Dict, Any
from datetime import datetime

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables (e.g., GROQ_API_KEY)
load_dotenv()

# 1. Initialize Firebase Admin SDK
# Make sure "serviceAccountKey.json" is in the same directory
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    db = None

# 2. Define LangChain Tools for fetching real-time data
# By fetching from Firestore inside the tool, the agent always gets the most up-to-date data.

@tool
def get_all_events() -> str:
    """
    Fetches all events from the Firestore database. 
    Use this to answer questions like 'how many events are there?' or 'what are all the events?'.
    """
    if not db:
        return "Database connection is not initialized."
    
    events_ref = db.collection("EVENTS")
    docs = events_ref.stream()
    
    events = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        events.append(data)
        
    if not events:
        return "No events found in the database."
        
    return str(events)

@tool
def search_events_by_status(status: str) -> str:
    """
    Searches for events based on a specific status (e.g., 'upcoming', 'past', 'active').
    Use this when the user asks about 'upcoming events' or events with a specific status.
    """
    if not db:
        return "Database connection is not initialized."
        
    # Note: Depending on your Firestore schema, you might need to adjust this query.
    # For example, if you store dates, you might want to query based on dates instead.
    # Here we assume there's a field 'status'. If there isn't, the agent can use get_all_events 
    # and filter the results itself.
    events_ref = db.collection("EVENTS")
    
    # Example query if you have a status field:
    # docs = events_ref.where("status", "==", status).stream()
    
    # Fallback: fetching all and letting the LLM filter, or returning all
    # For a production app with many events, implement specific Firestore queries here.
    docs = events_ref.stream()
    
    events = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        events.append(data)
        
    return str(events)

tools = [get_all_events, search_events_by_status]

# 3. Initialize the Agent
def get_chatbot_executor():
    # We use GROQ's model as the reasoning engine.
    # You can change this to ChatGoogleGenerativeAI for Gemini.
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

    # Define the system prompt for the chatbot
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful event management assistant of rotaract club . You have access to a real-time database of events. "
                   "When a user asks about events, ALWAYS use your tools to fetch the latest data from the database. "
                   "Do not make up information. If an event is not in the database, say you don't know. and answer in proper context.and hinglish language."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Create the agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create the executor that manages the agent's execution loop
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

# 4. Interactive Chat Loop
if __name__ == "__main__":
    print("Initializing Event Chatbot...")
    
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not found in environment variables.")
        print("Please create a .env file and add your GROQ_API_KEY=your_key_here")
    
    chatbot = get_chatbot_executor()
    
    print("\nChatbot is ready! Ask me about your events. (Type 'quit' to exit)")
    print("-" * 50)
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        try:
            response = chatbot.invoke({"input": user_input})
            print("\nBot:", response["output"])
            print("-" * 50)
        except Exception as e:
            print(f"\nError: {e}")
