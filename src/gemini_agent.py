"""
Strands Agent with Gemini Provider
===================================

This module provides a production-ready implementation using the official strands-agents library
with Google's Gemini API.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from strands import Agent
from strands.models.gemini import GeminiModel
from strands_tools import calculator

# Load environment variables
load_dotenv()


class GeminiAgent:
    """
    A strands agent powered by Google's Gemini API using the official strands-agents library.

    This agent can:
    - Process text queries with tool support
    - Maintain conversation history
    - Generate structured responses
    - Handle various NLP tasks with context awareness
    - Use tools like calculator for enhanced capabilities
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
        api_key: Optional[str] = None,
        tools: Optional[List] = None,
        top_p: float = 0.9,
        top_k: int = 40
    ):
        """
        Initialize the Gemini Agent using strands-agents library.

        Args:
            model_name: Name of the Gemini model to use
            temperature: Temperature for response generation (0.0 to 1.0)
            max_tokens: Maximum number of tokens in the response
            api_key: Google API key (defaults to GEMINI_API_KEY env variable)
            tools: List of tools to make available to the agent
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation_history: List[Dict[str, str]] = []

        # Configure API key
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize Gemini model with strands
        self.model = GeminiModel(
            client_args={
                "api_key": api_key,
            },
            model_id=model_name,
            params={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": top_p,
                "top_k": top_k
            }
        )

        # Initialize agent with tools
        default_tools = [calculator] if tools is None else tools
        self.agent = Agent(model=self.model, tools=default_tools)

    def send_message(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message to send
            system_prompt: Optional system prompt to guide the response

        Returns:
            Agent's response as a string
        """
        try:
            # If system prompt provided, prepend it
            if system_prompt:
                full_message = f"{system_prompt}\n\nUser: {message}"
            else:
                full_message = message

            # Send message and get response
            response = self.agent(full_message)

            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": str(response)
            })

            return str(response)

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return error_msg

    def send_message_with_context(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Send a message with additional context information.

        Args:
            message: User message
            context: Dictionary containing context information

        Returns:
            Agent's response
        """
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        full_message = f"Context:\n{context_str}\n\nUser Query: {message}"
        return self.send_message(full_message)

    def clear_history(self):
        """Clear the conversation history and restart the agent."""
        self.conversation_history = []
        # Recreate the agent to clear its internal history
        default_tools = [calculator]
        self.agent = Agent(model=self.model, tools=default_tools)

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history.

        Returns:
            List of conversation messages
        """
        return self.conversation_history

    def generate_structured_response(
        self,
        prompt: str,
        response_format: str = "json"
    ) -> str:
        """
        Generate a structured response in specified format.

        Args:
            prompt: The prompt for generation
            response_format: Format for the response (json, markdown, etc.)

        Returns:
            Structured response string
        """
        structured_prompt = (
            f"Please provide your response in {response_format} format.\n\n"
            f"{prompt}"
        )
        return self.send_message(structured_prompt)

    def summarize(self, text: str, max_length: int = 200) -> str:
        """
        Summarize the given text.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words

        Returns:
            Summary of the text
        """
        prompt = (
            f"Please provide a concise summary of the following text "
            f"in no more than {max_length} words:\n\n{text}"
        )
        return self.send_message(prompt)

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze the sentiment of the given text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result
        """
        prompt = (
            f"Analyze the sentiment of the following text. "
            f"Provide the overall sentiment (positive, negative, neutral) "
            f"and a brief explanation:\n\n{text}"
        )
        return self.send_message(prompt)

    def extract_entities(self, text: str) -> str:
        """
        Extract named entities from the text.

        Args:
            text: Text to process

        Returns:
            Extracted entities in JSON format
        """
        prompt = (
            f"Extract all named entities from the following text. "
            f"Return the result as JSON with categories like person, "
            f"organization, location, date, etc.:\n\n{text}"
        )
        return self.generate_structured_response(prompt, "json")

    def answer_question(
        self,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        Answer a question, optionally using provided context.

        Args:
            question: Question to answer
            context: Optional context to use for answering

        Returns:
            Answer to the question
        """
        if context:
            prompt = (
                f"Based on the following context, answer the question.\n\n"
                f"Context: {context}\n\n"
                f"Question: {question}"
            )
        else:
            prompt = question

        return self.send_message(prompt)


class MultiAgentSystem:
    """
    A system managing multiple specialized agents using strands-agents library.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the multi-agent system.

        Args:
            api_key: Google API key
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.agents: Dict[str, GeminiAgent] = {}

    def create_agent(
        self,
        name: str,
        temperature: float = 0.7,
        model_name: str = "gemini-2.0-flash-exp",
        tools: Optional[List] = None
    ) -> GeminiAgent:
        """
        Create a new specialized agent.

        Args:
            name: Name identifier for the agent
            temperature: Temperature setting
            model_name: Model to use
            tools: Optional list of tools for this agent

        Returns:
            Created agent instance
        """
        agent = GeminiAgent(
            model_name=model_name,
            temperature=temperature,
            api_key=self.api_key,
            tools=tools
        )
        self.agents[name] = agent
        return agent

    def get_agent(self, name: str) -> Optional[GeminiAgent]:
        """
        Get an agent by name.

        Args:
            name: Agent name

        Returns:
            Agent instance or None
        """
        return self.agents.get(name)

    def list_agents(self) -> List[str]:
        """
        List all agent names.

        Returns:
            List of agent names
        """
        return list(self.agents.keys())

    def remove_agent(self, name: str) -> bool:
        """
        Remove an agent.

        Args:
            name: Agent name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self.agents:
            del self.agents[name]
            return True
        return False


# Example usage
if __name__ == "__main__":
    # Initialize agent with tool support
    agent = GeminiAgent()

    # Simple conversation
    print("=== Simple Conversation ===")
    response = agent.send_message("Hello! Can you tell me about artificial intelligence?")
    print("Agent:", response)

    # Tool usage example - Calculator
    print("\n=== Tool Usage (Calculator) ===")
    response = agent.send_message("What is 2+2?")
    print("Agent:", response)

    # Math calculation
    print("\n=== Complex Calculation ===")
    response = agent.send_message("Calculate 15 * 23 + 47")
    print("Agent:", response)

    # Summarization
    print("\n=== Summarization ===")
    text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines,
    in contrast to the natural intelligence displayed by humans and animals.
    Leading AI textbooks define the field as the study of intelligent agents:
    any device that perceives its environment and takes actions that maximize
    its chance of successfully achieving its goals.
    """
    summary = agent.summarize(text, max_length=50)
    print("Summary:", summary)

    # Multi-agent system example
    print("\n=== Multi-Agent System ===")
    mas = MultiAgentSystem()

    # Create specialized agents
    creative_agent = mas.create_agent("creative", temperature=0.9)
    analytical_agent = mas.create_agent("analytical", temperature=0.3)

    # Use different agents
    creative_response = creative_agent.send_message(
        "Write a creative short story about a robot learning to paint."
    )
    print("\nCreative Agent:", creative_response[:200] + "...")

    analytical_response = analytical_agent.send_message(
        "Analyze the benefits and drawbacks of using AI in healthcare."
    )
    print("\nAnalytical Agent:", analytical_response[:200] + "...")
