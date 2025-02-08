from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Type
import os
import re
import time
import json
from decimal import Decimal
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from langchain.tools import BaseTool
from cdp import Cdp, Wallet

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="CDP Agent API")

# CDP Configuration
CDP_API_KEY_NAME = os.getenv('CDP_API_KEY_NAME')
CDP_API_KEY_PRIVATE_KEY = os.getenv('CDP_API_KEY_PRIVATE_KEY')
NETWORK_ID = os.getenv('NETWORK_ID')

if not all([CDP_API_KEY_NAME, CDP_API_KEY_PRIVATE_KEY, NETWORK_ID]):
    raise ValueError("Missing required environment variables. Please check your .env file")

# Process the private key to handle newline characters correctly
PRIVATE_KEY = CDP_API_KEY_PRIVATE_KEY.replace('\\n', '\n')

# Configure CDP
Cdp.configure(CDP_API_KEY_NAME, PRIVATE_KEY)

# Contract configuration
CONTRACT_ADDRESS = "0xBda5Ef6f902c589862ca6e3079f835e527c80D06"
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "uint64", "name": "endDate", "type": "uint64"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_value", "type": "uint256"}
        ],
        "name": "createTransactionProposal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Global variables
agent_instances = {}
agent_configs = {}
WALLET_FILE_PATH = "wallet_seed.json"

# Mock database of wallet addresses
WALLET_DATABASE = {
    "plumber": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "electrician": "0x123d35Cc6634C0532925a3b844Bc454e4438f789",
    "carpenter": "0x456d35Cc6634C0532925a3b844Bc454e4438fabc"
}

# Model classes
class WalletLookupSchema(BaseModel):
    profession: str = Field(description="The profession of the service provider")

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
    11.) You have access to the get_wallet_address tool - USE IT whenever dealing with service providers!"""
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
    transaction_hash: Optional[str] = None

class WalletLookupTool(BaseTool):
    name: str = "get_wallet_address"
    description: str = "Use this tool to look up the wallet address for a service provider based on their profession."
    args_schema: Type[BaseModel] = WalletLookupSchema
    return_direct: bool = False

    def _run(self, profession: str) -> str:
        profession = profession.lower()
        if profession in WALLET_DATABASE:
            return f"The wallet address for the {profession} is: {WALLET_DATABASE[profession]}"
        return f"No wallet address found for profession: {profession}"

def get_or_create_wallet():
    """Get existing wallet or create a new one"""
    try:
        if os.path.exists(WALLET_FILE_PATH):
            try:
                # First try to load the existing wallet
                wallet = Wallet.create()
                wallet.load_seed_from_file(WALLET_FILE_PATH)
                print(f"Successfully loaded existing wallet: {wallet.id}")
                return wallet
            except Exception as load_error:
                print(f"Error loading existing wallet: {str(load_error)}")
                print("Creating new wallet instead...")
                # If loading fails, remove the corrupted file and create new wallet
                os.remove(WALLET_FILE_PATH)
        
        # Create new wallet if none exists or loading failed
        wallet = Wallet.create()
        wallet.save_seed(WALLET_FILE_PATH, encrypt=True)
        print(f"Created and saved new wallet: {wallet.id}")
        return wallet
        
    except Exception as e:
        print(f"Error in get_or_create_wallet: {str(e)}")
        raise

def fund_wallet_if_needed(wallet, required_amount: str) -> bool:
    """Fund the wallet if balance is insufficient"""
    asset_id = "eth"
    max_attempts = 3
    wait_time = 5  # seconds between attempts

    try:
        # First check current balance
        current_balance = wallet.balance(asset_id)
        required_decimal = Decimal(required_amount)
        
        if current_balance >= required_decimal:
            print(f"Wallet has sufficient balance: {current_balance} ETH")
            return True
            
        print(f"Current balance {current_balance} ETH, need {required_amount} ETH")
        
        # Try funding multiple times if needed
        for attempt in range(max_attempts):
            try:
                print(f"Funding attempt {attempt + 1} of {max_attempts}")
                faucet_tx = wallet.faucet()
                faucet_tx.wait()
                
                # Wait for balance update
                time.sleep(wait_time)
                
                # Check new balance
                new_balance = wallet.balance(asset_id)
                if new_balance >= required_decimal:
                    print(f"Successfully funded wallet. New balance: {new_balance} ETH")
                    return True
                    
            except Exception as e:
                print(f"Funding attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(wait_time)  # Wait before next attempt
                    
        # Final balance check
        final_balance = wallet.balance(asset_id)
        if final_balance >= required_decimal:
            return True
            
        print(f"Failed to fund wallet after {max_attempts} attempts. Final balance: {final_balance} ETH")
        return False
        
    except Exception as e:
        print(f"Error in fund_wallet_if_needed: {str(e)}")
        return False

def eth_to_wei(eth_amount: str) -> str:
    """Convert ETH amount to Wei (1 ETH = 10^18 Wei)"""
    try:
        eth_decimal = Decimal(eth_amount)
        wei_amount = int(eth_decimal * Decimal('1000000000000000000'))
        return str(wei_amount)
    except Exception as e:
        raise ValueError(f"Error converting ETH to Wei: {str(e)}")

def parse_agent_response(content: str) -> ParsedResponse:
    """Parse the agent's response into separate fields"""
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
        raise ValueError(f"Error parsing response: {str(e)}")

async def create_transaction_proposal(parsed_response: ParsedResponse) -> Optional[str]:
    """Create a transaction proposal if all required fields are present"""
    if not all([parsed_response.wallet_address, parsed_response.amount]):
        return None

    try:
        wallet = get_or_create_wallet()
        
        # Only need gas for contract interaction, not the full transaction amount
        gas_buffer = Decimal('0.00001')
        
        # Fund wallet if needed - only checking against gas requirements
        if not fund_wallet_if_needed(wallet, str(gas_buffer)):
            raise Exception("Failed to fund wallet with sufficient gas")

        current_time = int(time.time())
        end_time = current_time + (24 * 60 * 60)  # 24 hours from now

        transaction_data = {
            'endDate': str(end_time),
            '_to': parsed_response.wallet_address,
            '_value': eth_to_wei(parsed_response.amount)
        }

        print("Sending transaction with data:", transaction_data)

        invocation = wallet.invoke_contract(
            contract_address=CONTRACT_ADDRESS,
            abi=CONTRACT_ABI,
            method="createTransactionProposal",
            args=transaction_data
        )

        invocation.wait()
        return invocation.transaction_hash

    except Exception as e:
        print(f"Error in create_transaction_proposal: {str(e)}")
        raise

def create_cdp_agent(system_prompt: str, temperature: float, max_tokens: int):
    """Initialize the CDP agent"""
    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        agentkit = CdpAgentkitWrapper()
        cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
        tools = cdp_toolkit.get_tools()
        tools.append(WalletLookupTool())
        
        memory = MemorySaver()
        config = {"configurable": {"thread_id": "CDP Agent Chat"}}
        
        agent_executor = create_react_agent(
            llm,
            tools=tools,
            checkpointer=memory,
            state_modifier=system_prompt
        )
        
        return agent_executor, config
    except Exception as e:
        raise Exception(f"Error creating agent: {str(e)}")

def get_agent(system_prompt: str, temperature: float, max_tokens: int):
    """Get or create agent instance"""
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
        raise Exception(f"Error getting agent: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint that processes messages and returns responses"""
    try:
        agent_executor, config = get_agent(
            request.system_prompt,
            request.temperature,
            request.max_tokens
        )
        
        agent_response = None
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=request.message)]},
            config
        ):
            if "agent" in chunk:
                agent_response = chunk["agent"]["messages"][0].content
        
        if not agent_response:
            raise HTTPException(status_code=500, detail="No response received from agent")
        
        parsed_response = parse_agent_response(agent_response)
        
        transaction_hash = None
        if all([parsed_response.wallet_address, parsed_response.amount]):
            transaction_hash = await create_transaction_proposal(parsed_response)
        
        return ChatResponse(
            parsed_content=parsed_response,
            transaction_hash=transaction_hash
        )
            
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint that confirms the API is running"""
    return {"status": "CDP Agent API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
