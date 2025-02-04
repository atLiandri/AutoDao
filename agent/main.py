from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import re
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="CDP Agent API")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for agent instance and config
agent_instances = {}
agent_configs = {}

# Create a class for the chat request
class ChatRequest(BaseModel):
    message: str
    system_prompt: str = """1.) You are an Agent for Social Good who could post the issues faced by the people in a DAO.
    2.) Now your job is to understand the issue they're facing, learn more about it and decide whether it is an issue which needs to be addressed or something which should be skipped.
    3.) MOST IMPORTANT: Your response format should EXACTLY be like this and NEVER EVER deviate from it:
    [Title]:[The title][Decision]:[The Decision you took][Summary]:[The reason why you took the decision][Response]:[Your response to the inputs you are given]
    4.) People will talk to you regarding their issues and you could talk to them by simply populating the Response field while keeping the others empty.
    5.) If you feel like you want to address the issue they face AFTER completely understanding their petition, populate the Title field, Decision field, Summary field. 
    6.) For example: If you decided that a pipe in the neighbourhood should be fixed after talking with a user, simply populate the Title with the Title of the issue, Decision with your Decision whether to fix the pipe or not, Summary with why you wanted to fix that pipe.
    7.) REMEMBER: All the 4 fields should be present in your Output ALL the time but should be populated only when needed!
    8.) EXAMPLE RESPONSE: [Title]:Broken Pipe[Decision]:Pipe Must be fixed[Summary]:The broken pipe next to the community hall has not been addressed by anyone yet, and it's causing water to flow everywhere, creating a nuisance for the community.[Response]:Thank you for bringing this to my attention. I will post about this in the DAO.
    9.) NOTE: Follow the given instructions at ALL COSTS
    10.) NEVER EVER simply come to a conclusion, Understand the issue completely by talking with the user for a few minutes and gather relevant information and ONLY then you're suppposed to post the petition in the DAO!!!
    """
    temperature: float = 0.3
    max_tokens: int = 124

# Create a class for the parsed fields
class ParsedResponse(BaseModel):
    title: str = ""
    decision: str = ""
    summary: str = ""
    response: str = ""

# Create a class for the chat response
class ChatResponse(BaseModel):
    parsed_content: ParsedResponse

def parse_agent_response(content: str) -> ParsedResponse:
    """Parse the agent's response into separate fields."""
    # Initialize default empty values
    parsed = {
        "title": "",
        "decision": "",
        "summary": "",
        "response": ""
    }
    
    # Define patterns for each field
    patterns = {
        "title": r'\[Title\]:(.*?)(?=\[Decision\])',
        "decision": r'\[Decision\]:(.*?)(?=\[Summary\])',
        "summary": r'\[Summary\]:(.*?)(?=\[Response\])',
        "response": r'\[Response\]:(.*?)(?=\[|$)'
    }
    
    # Extract each field
    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            parsed[field] = match.group(1).strip()
    
    return ParsedResponse(**parsed)

def create_cdp_agent(system_prompt: str, temperature: float, max_tokens: int):
    """Initialize the CDP agent with a custom system prompt and LLM parameters."""
    # Initialize LLM with specified parameters
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # Configure CDP Agentkit
    agentkit = CdpAgentkitWrapper()
    
    # Initialize CDP Agentkit Toolkit and get tools
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()
    
    # Store conversation history
    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP Agent Chat"}}
    
    # Create ReAct Agent
    agent_executor = create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=system_prompt
    )
    
    return agent_executor, config

def get_agent(system_prompt: str, temperature: float, max_tokens: int):
    """Get or create agent instance."""
    # Create a unique key for this configuration
    config_key = f"{system_prompt}_{temperature}_{max_tokens}"
    
    if config_key not in agent_instances:
        agent_instances[config_key], agent_configs[config_key] = create_cdp_agent(
            system_prompt,
            temperature,
            max_tokens
        )
    
    return agent_instances[config_key], agent_configs[config_key]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that processes messages and returns responses from the CDP agent.
    """
    try:
        # Get or create agent with specified parameters
        agent_executor, config = get_agent(
            request.system_prompt,
            request.temperature,
            request.max_tokens
        )
        
        # Process message
        agent_response = None
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=request.message)]},
            config
        ):
            if "agent" in chunk:
                agent_response = chunk["agent"]["messages"][0].content
        
        if agent_response:
            # Parse the response into separate fields
            parsed_response = parse_agent_response(agent_response)
            return ChatResponse(parsed_content=parsed_response)
        else:
            raise HTTPException(status_code=500, detail="No response received from agent")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint that confirms the API is running."""
    return {"status": "CDP Agent API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)