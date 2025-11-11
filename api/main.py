"""
Production-Level FastAPI Application for Gemini Agent
======================================================

This module provides a production-ready REST API for the Gemini-powered strands agent
using the official strands-agents library with tool support.

Features:
- RESTful API endpoints
- Request validation with Pydantic
- Error handling and logging
- Rate limiting support
- API documentation (Swagger/OpenAPI)
- Health checks and monitoring
- Async support
- CORS configuration
- Tool support (calculator, etc.)
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gemini_agent import GeminiAgent, MultiAgentSystem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
agent_system: Optional[MultiAgentSystem] = None


# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    """
    global agent_system

    # Startup
    logger.info("Starting up API server...")
    try:
        agent_system = MultiAgentSystem()
        # Create default agent
        agent_system.create_agent("default", temperature=0.7)
        logger.info("Agent system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent system: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down API server...")


# Initialize FastAPI app
app = FastAPI(
    title="Gemini Agent API",
    description="Production-ready REST API for Gemini-powered strands agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class MessageRequest(BaseModel):
    """Request model for sending a message."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    agent_name: str = Field(default="default", description="Name of the agent to use")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Explain quantum computing in simple terms",
                "agent_name": "default",
                "system_prompt": "You are a helpful assistant."
            }
        }


class MessageResponse(BaseModel):
    """Response model for message."""
    response: str
    agent_name: str
    timestamp: str
    tokens_used: Optional[int] = None


class SummarizeRequest(BaseModel):
    """Request model for text summarization."""
    text: str = Field(..., min_length=1, description="Text to summarize")
    max_length: int = Field(default=200, ge=10, le=1000, description="Maximum summary length in words")
    agent_name: str = Field(default="default", description="Name of the agent to use")


class SentimentRequest(BaseModel):
    """Request model for sentiment analysis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    agent_name: str = Field(default="default", description="Name of the agent to use")


class QuestionRequest(BaseModel):
    """Request model for question answering."""
    question: str = Field(..., min_length=1, description="Question to answer")
    context: Optional[str] = Field(None, description="Optional context for answering")
    agent_name: str = Field(default="default", description="Name of the agent to use")


class CreateAgentRequest(BaseModel):
    """Request model for creating a new agent."""
    name: str = Field(..., min_length=1, max_length=50, description="Agent name")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature setting")
    model_name: str = Field(default="gemini-2.0-flash-exp", description="Model name")


class AgentInfo(BaseModel):
    """Information about an agent."""
    name: str
    model_name: str
    temperature: float
    created_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    agents_active: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: str


# Dependency to get agent system
def get_agent_system() -> MultiAgentSystem:
    """Dependency to get the agent system."""
    if agent_system is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent system not initialized"
        )
    return agent_system


# API Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "message": "Gemini Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check(mas: MultiAgentSystem = Depends(get_agent_system)):
    """
    Health check endpoint.

    Returns the current status of the API and agent system.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        agents_active=len(mas.list_agents())
    )


@app.post("/message", response_model=MessageResponse, tags=["Chat"])
async def send_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Send a message to an agent and get a response.

    - **message**: The message to send
    - **agent_name**: Name of the agent to use (default: "default")
    - **system_prompt**: Optional system prompt to guide the response
    """
    try:
        agent = mas.get_agent(request.agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{request.agent_name}' not found"
            )

        # Send message
        response = agent.send_message(request.message, request.system_prompt)

        # Log in background
        background_tasks.add_task(
            logger.info,
            f"Message processed - Agent: {request.agent_name}, "
            f"Message length: {len(request.message)}, "
            f"Response length: {len(response)}"
        )

        return MessageResponse(
            response=response,
            agent_name=request.agent_name,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@app.post("/summarize", response_model=MessageResponse, tags=["NLP"])
async def summarize_text(
    request: SummarizeRequest,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Summarize a text.

    - **text**: Text to summarize
    - **max_length**: Maximum length of summary in words (default: 200)
    - **agent_name**: Name of the agent to use
    """
    try:
        agent = mas.get_agent(request.agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{request.agent_name}' not found"
            )

        summary = agent.summarize(request.text, request.max_length)

        return MessageResponse(
            response=summary,
            agent_name=request.agent_name,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error summarizing text: {str(e)}"
        )


@app.post("/sentiment", response_model=MessageResponse, tags=["NLP"])
async def analyze_sentiment(
    request: SentimentRequest,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Analyze the sentiment of a text.

    - **text**: Text to analyze
    - **agent_name**: Name of the agent to use
    """
    try:
        agent = mas.get_agent(request.agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{request.agent_name}' not found"
            )

        sentiment = agent.analyze_sentiment(request.text)

        return MessageResponse(
            response=sentiment,
            agent_name=request.agent_name,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing sentiment: {str(e)}"
        )


@app.post("/question", response_model=MessageResponse, tags=["QA"])
async def answer_question(
    request: QuestionRequest,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Answer a question, optionally with provided context.

    - **question**: Question to answer
    - **context**: Optional context to use for answering
    - **agent_name**: Name of the agent to use
    """
    try:
        agent = mas.get_agent(request.agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{request.agent_name}' not found"
            )

        answer = agent.answer_question(request.question, request.context)

        return MessageResponse(
            response=answer,
            agent_name=request.agent_name,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error answering question: {str(e)}"
        )


@app.post("/agents", response_model=AgentInfo, tags=["Agent Management"], status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: CreateAgentRequest,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Create a new agent.

    - **name**: Unique name for the agent
    - **temperature**: Temperature setting (0.0 to 1.0)
    - **model_name**: Model to use
    """
    try:
        # Check if agent already exists
        if mas.get_agent(request.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent '{request.name}' already exists"
            )

        agent = mas.create_agent(
            name=request.name,
            temperature=request.temperature,
            model_name=request.model_name
        )

        logger.info(f"Created new agent: {request.name}")

        return AgentInfo(
            name=request.name,
            model_name=request.model_name,
            temperature=request.temperature,
            created_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating agent: {str(e)}"
        )


@app.get("/agents", response_model=List[str], tags=["Agent Management"])
async def list_agents(mas: MultiAgentSystem = Depends(get_agent_system)):
    """
    List all active agents.

    Returns a list of agent names.
    """
    return mas.list_agents()


@app.delete("/agents/{agent_name}", tags=["Agent Management"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_name: str,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Delete an agent.

    - **agent_name**: Name of the agent to delete
    """
    if agent_name == "default":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete the default agent"
        )

    if not mas.remove_agent(agent_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    logger.info(f"Deleted agent: {agent_name}")
    return None


@app.post("/agents/{agent_name}/clear-history", tags=["Agent Management"])
async def clear_agent_history(
    agent_name: str,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Clear the conversation history of an agent.

    - **agent_name**: Name of the agent
    """
    agent = mas.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    agent.clear_history()
    logger.info(f"Cleared history for agent: {agent_name}")

    return {"message": f"History cleared for agent '{agent_name}'"}


@app.get("/agents/{agent_name}/history", tags=["Agent Management"])
async def get_agent_history(
    agent_name: str,
    mas: MultiAgentSystem = Depends(get_agent_system)
):
    """
    Get the conversation history of an agent.

    - **agent_name**: Name of the agent
    """
    agent = mas.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    return {
        "agent_name": agent_name,
        "history": agent.get_history(),
        "message_count": len(agent.get_history())
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.utcnow().isoformat()
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.utcnow().isoformat()
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
