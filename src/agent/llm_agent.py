"""LLM agent integration with Ollama and LangChain."""

import logging
import os
import sys
from typing import List, Dict, Any, Optional
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage
from langchain_community.llms import Ollama

# Add src to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from agent.context_manager import ContextManager
from tools.schema_tools import SchemaTools


class LLMAgent:
    """LLM agent for handling conversational schema queries."""
    
    def __init__(
        self,
        model_name: str = "phi3:mini",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.1,
        max_tokens: int = 1000,
        schema_tools: SchemaTools = None
    ):
        """Initialize the LLM agent.
        
        Args:
            model_name: Name of the Ollama model
            base_url: Ollama server URL
            temperature: LLM temperature setting
            max_tokens: Maximum tokens for responses
            schema_tools: SchemaTools instance
        """
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = get_logger("tabletalk.agent")
        
        # Initialize components
        self.context_manager = ContextManager()
        self.schema_tools = schema_tools
        
        # Initialize LLM and agent
        self._init_llm()
        self._init_agent()
    
    def _init_llm(self) -> None:
        """Initialize the Ollama LLM."""
        try:
            self.llm = Ollama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature,
                num_predict=self.max_tokens
            )
            
            # Test connection
            test_response = self.llm.invoke("Hello")
            self.logger.info(f"LLM initialized successfully with model: {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {str(e)}")
            raise RuntimeError(f"Could not connect to Ollama. Make sure it's running on {self.base_url}")
    
    def _init_agent(self) -> None:
        """Initialize the LangChain agent with tools."""
        try:
            # Get tools from schema_tools
            tools = self.schema_tools.get_langchain_tools() if self.schema_tools else []
            
            # Initialize memory for conversation context
            self.memory = ConversationBufferWindowMemory(
                k=5,  # Remember last 5 exchanges
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create agent with strict limits for fast responses
            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=False,  # Suppress verbose chain output
                handle_parsing_errors=True,
                max_iterations=2,  # Reduced from 3 to 2 for faster responses
                max_execution_time=30  # 30 second timeout
            )
            
            self.logger.info(f"Agent initialized with {len(tools)} tools")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {str(e)}")
            raise RuntimeError(f"Could not initialize LangChain agent: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent.
        
        Returns:
            System prompt string
        """
        return """You are TableTalk, a helpful assistant for exploring data schemas and file structures.
Your role is to help users understand their datasets by answering questions about file schemas, column information, data types, and inconsistencies across files.
Always use the provided tools to get accurate information and provide clear, specific answers."""
    
    def query(self, user_input: str) -> str:
        """Process a user query and return a response.
        
        Args:
            user_input: User's query string
            
        Returns:
            Agent's response
        """
        try:
            # Detect intent and prepare context
            intent, parameter = self.context_manager.detect_intent(user_input)
            context = self.context_manager.prepare_context(intent, parameter)
            
            self.logger.debug(f"Processing query with intent: {intent}, parameter: {parameter}")
            
            # Use the agent to process the query with invoke instead of deprecated run
            response = self.agent.invoke({"input": user_input})
            
            # Extract the output from the response
            if isinstance(response, dict) and 'output' in response:
                result = response['output'].strip() if response['output'] else "I couldn't process that query."
            else:
                result = str(response).strip() if response else "I couldn't process that query."
            
            # Filter response length if needed
            filtered_response = self.context_manager.filter_context_for_llm(result)
            
            return filtered_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            error_msg = str(e)
            
            # Provide more specific error messages
            if "Connection" in error_msg or "Ollama" in error_msg:
                suggestion = "Check if Ollama is running with: ollama serve"
            elif "tool" in error_msg.lower():
                suggestion = "There might be an issue with the tools. Try using /status to check system health."
            else:
                suggestion = "Try rephrasing your question or use /help for guidance."
                
            return self.context_manager.format_error_message(error_msg, suggestion)
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """Get the current conversation history.
        
        Returns:
            List of conversation messages
        """
        if hasattr(self.memory, 'chat_memory'):
            return self.memory.chat_memory.messages
        return []
    
    def clear_memory(self) -> None:
        """Clear the conversation memory."""
        if hasattr(self.memory, 'clear'):
            self.memory.clear()
        self.logger.info("Conversation memory cleared")
    
    def test_connection(self) -> bool:
        """Test the connection to Ollama.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self.llm.invoke("Hello")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
