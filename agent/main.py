from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Type
import os
import re
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from langchain.tools import BaseTool

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="CDP Agent API")

# Global variables for agent instance and config
agent_instances = {}
agent_configs = {}

# Mock database of wallet addresses
WALLET_DATABASE = {
    "plumber": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "electrician": "0x123d35Cc6634C0532925a3b844Bc454e4438f789",
    "carpenter": "0x456d35Cc6634C0532925a3b844Bc454e4438fabc"
}

# Define the input schema for the wallet lookup tool
class WalletLookupSchema(BaseModel):
    """Inputs for the wallet lookup tool."""
    profession: str = Field(
        description="The profession of the service provider (e.g., 'plumber', 'electrician', 'carpenter')"
    )

class WalletLookupTool(BaseTool):
    name: str = "get_wallet_address"
    description: str = """
    Use this tool to look up the wallet address for a service provider based on their profession.
    This tool is required whenever you need to handle payments for services like plumbing, electrical work, or carpentry.
    Always use this tool before mentioning any wallet addresses in your response.
    """
    args_schema: Type[BaseModel] = WalletLookupSchema
    return_direct: bool = False

    def _run(self, profession: str) -> str:
        """Execute the wallet lookup."""
        profession = profession.lower()
        if profession in WALLET_DATABASE:
            return f"The wallet address for the {profession} is: {WALLET_DATABASE[profession]}"
        return f"No wallet address found for profession: {profession}"

class ChatRequest(BaseModel):
    message: str
    system_prompt: str = """1.) You are an Agent for Social Good who could post the issues faced by the people in a DAO.
    2.) Now your job is to understand the issue they're facing, learn more about it and decide whether it is an issue which needs to be addressed or something which should be skipped.
    3.) MOST IMPORTANT: Your response format should EXACTLY be like this and NEVER EVER deviate from it:
    [Title]:[The title][Decision]:[The Decision you took][Summary]:[The reason why you took the decision][Response]:[Your response to the inputs you are given][Amount]:[The amount in ETH][Wallet Address]:[The wallet address to send the payment to]
    4.) People will talk to you regarding their issues and you could talk to them by simply populating the Response field while keeping the others empty.
    5.) If you feel like you want to address the issue they face AFTER completely undersating their petition, populate the Title field, Decision field, Summary field. 
    6.) CRITICAL: Whenever you need to handle payments for services like plumbing, electrical work, etc., you MUST FIRST use the get_wallet_address tool to obtain the wallet address BEFORE providing your response. Never mention getting a wallet address without actually using the tool.
    7.) REMEMBER: All the fields should be present in your Output ALL the time but should be populated only when needed!
    8.) EXAMPLE RESPONSE WITH TOOL USAGE: 
        - First use: get_wallet_address("plumber")
        - Then respond: [Title]:Broken Pipe[Decision]:Hire Plumber[Summary]:The broken pipe needs immediate attention.[Response]:I've located a plumber who can help. Their wallet address is {result from get_wallet_address tool}. We can proceed with the payment and repairs.[Amount]:0.00080[Wallet Address]:{result from get_wallet_address tool}
    9.) NOTE: Follow the given instructions at ALL COSTS
    10.) NEVER EVER simply come to a conclusion, Understand the issue completely by talking with the user for a few minutes and gather relevant information and ONLY then you're suppposed to post the petition in the DAO!!!
    11.) You have access to the get_wallet_address tool - USE IT whenever dealing with service providers!
    """
    temperature: float = 0.3
    max_tokens: int = 512

class ParsedResponse(BaseModel):
    title: str = ""
    decision: str = ""
    summary: str = ""
    response: str = ""
    amount: str = ""
    wallet_address: str = ""

class ChatResponse(BaseModel):
    parsed_content: ParsedResponse

def parse_agent_response(content: str) -> ParsedResponse:
    """Parse the agent's response into separate fields."""
    try:
        parsed = {
            "title": "",
            "decision": "",
            "summary": "",
            "response": "",
            "amount": "",
            "wallet_address": ""
        }
        
        patterns = {
            "title": r'\[Title\]:(.*?)(?=\[Decision\])',
            "decision": r'\[Decision\]:(.*?)(?=\[Summary\])',
            "summary": r'\[Summary\]:(.*?)(?=\[Response\])',
            "response": r'\[Response\]:(.*?)(?=\[Amount\]|\[|$)',
            "amount": r'\[Amount\]:(.*?)(?=\[Wallet Address\]|\[|$)',
            "wallet_address": r'\[Wallet Address\]:(.*?)(?=\[|$)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                parsed[field] = match.group(1).strip()
        
        return ParsedResponse(**parsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing response: {str(e)}")

def create_cdp_agent(system_prompt: str, temperature: float, max_tokens: int):
    """Initialize the CDP agent with a custom system prompt and LLM parameters."""
    try:
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
        
        # Add the wallet lookup tool
        wallet_tool = WalletLookupTool()
        tools.append(wallet_tool)
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

def get_agent(system_prompt: str, temperature: float, max_tokens: int):
    """Get or create agent instance."""
    try:
        config_key = f"{system_prompt}_{temperature}_{max_tokens}"
        
        if config_key not in agent_instances:
            agent_instances[config_key], agent_configs[config_key] = create_cdp_agent(
                system_prompt,
                temperature,
                max_tokens
            )
        
        return agent_instances[config_key], agent_configs[config_key]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agent: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint that processes messages and returns responses from the CDP agent."""
    try:
        agent_executor, config = get_agent(
            request.system_prompt,
            request.temperature,
            request.max_tokens
        )
        
        agent_response = None
        try:
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=request.message)]},
                config
            ):
                if "agent" in chunk:
                    agent_response = chunk["agent"]["messages"][0].content
            
            if agent_response:
                # Debug print statements
                print(agent_response)
                
                parsed_response = parse_agent_response(agent_response)
                return ChatResponse(parsed_content=parsed_response)
            else:
                raise HTTPException(status_code=500, detail="No response received from agent")
        except Exception as stream_error:
            raise HTTPException(status_code=500, detail=f"Error processing stream: {str(stream_error)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat endpoint: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint that confirms the API is running."""
    return {"status": "CDP Agent API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
