# Gemini Strands Agent Project

A production-ready implementation of a strands agent system powered by Google's Gemini API, featuring both a Python library and a RESTful API for integration.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Setup & Installation](#setup--installation)
5. [Quick Start](#quick-start)
6. [API Documentation](#api-documentation)
7. [Usage Examples](#usage-examples)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)

---

## Overview

This project provides a comprehensive implementation of intelligent agents using Google's Gemini API. It includes:

- **Core Agent Library**: Python library for creating and managing Gemini-powered agents
- **REST API**: Production-ready FastAPI application for HTTP-based agent interactions
- **Multi-Agent System**: Support for multiple specialized agents with different configurations
- **Testing Framework**: Jupyter notebook and test suite for validation

### What is a Strands Agent?

A strands agent is an AI-powered system that can:
- Maintain conversation context
- Process and analyze text
- Answer questions with contextual awareness
- Perform specialized tasks (summarization, sentiment analysis, entity extraction)
- Collaborate in multi-agent systems

---

## Features

### Core Capabilities

- **Conversation Management**: Maintain context across multiple interactions
- **Text Summarization**: Condense long documents while preserving key information
- **Sentiment Analysis**: Analyze emotional tone and sentiment in text
- **Entity Extraction**: Identify and categorize named entities
- **Question Answering**: Context-aware question answering with supporting documents
- **Structured Generation**: Generate responses in specific formats (JSON, Markdown, etc.)

### API Features

- RESTful endpoints with OpenAPI/Swagger documentation
- Request/response validation with Pydantic
- Comprehensive error handling and logging
- CORS support for web applications
- Background task processing
- Health checks and monitoring
- Multi-agent management

### Production Features

- Environment-based configuration
- Logging to file and console
- Async request processing
- Rate limiting support
- Exception handling
- API versioning

---

## Architecture

```
doc_toc_strands/
├── src/
│   └── gemini_agent.py          # Core agent implementation
├── api/
│   ├── main.py                  # FastAPI application
│   └── config.py                # Configuration management
├── notebooks/
│   └── test_gemini_agent.ipynb  # Interactive testing notebook
├── tests/
│   └── (test files)
├── docs/                        # Additional documentation
├── venv/                        # Virtual environment
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── claude.md                    # This file
```

### Component Diagram

```
┌─────────────────────────────────────────────┐
│          Client Applications                │
│  (Web, Mobile, CLI, Jupyter, etc.)         │
└──────────────┬──────────────────────────────┘
               │
               v
┌─────────────────────────────────────────────┐
│          FastAPI REST API                   │
│  ┌─────────────────────────────────────┐   │
│  │  Endpoints (Chat, NLP, QA, etc.)    │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼──────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────┐
│       Multi-Agent System                    │
│  ┌────────────┐  ┌────────────┐            │
│  │  Agent 1   │  │  Agent 2   │   ...      │
│  └─────┬──────┘  └─────┬──────┘            │
└────────┼───────────────┼───────────────────┘
         │               │
         v               v
┌─────────────────────────────────────────────┐
│          Google Gemini API                  │
│     (gemini-2.0-flash-exp, etc.)           │
└─────────────────────────────────────────────┘
```

---

## Setup & Installation

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Virtual environment (recommended)

### Installation Steps

#### 1. Clone or Download the Project

```bash
cd doc_toc_strands
```

#### 2. Create and Activate Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

#### 5. Verify Installation

```bash
python -c "from src.gemini_agent import GeminiAgent; print('✓ Installation successful')"
```

---

## Quick Start

### Using the Python Library

```python
from src.gemini_agent import GeminiAgent

# Initialize agent
agent = GeminiAgent()

# Send a message
response = agent.send_message("Explain quantum computing in simple terms")
print(response)

# Summarize text
text = "Your long text here..."
summary = agent.summarize(text, max_length=100)
print(summary)

# Analyze sentiment
sentiment = agent.analyze_sentiment("I love this product!")
print(sentiment)
```

### Starting the API Server

```bash
# Navigate to api directory
cd api

# Start the server
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Using the Jupyter Notebook

```bash
# Start Jupyter
jupyter notebook

# Open notebooks/test_gemini_agent.ipynb
```

---

## API Documentation

### Base URL

```
http://localhost:8000
```

### Authentication

Currently, the API uses API key authentication via the `GEMINI_API_KEY` environment variable. For production, implement proper authentication middleware.

### Endpoints

#### General

##### `GET /`
Root endpoint with API information.

##### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-10T12:00:00",
  "version": "1.0.0",
  "agents_active": 1
}
```

#### Chat

##### `POST /message`
Send a message to an agent.

**Request Body:**
```json
{
  "message": "Explain quantum computing",
  "agent_name": "default",
  "system_prompt": "You are a helpful assistant"
}
```

**Response:**
```json
{
  "response": "Quantum computing is...",
  "agent_name": "default",
  "timestamp": "2024-11-10T12:00:00"
}
```

#### NLP Tasks

##### `POST /summarize`
Summarize text.

**Request Body:**
```json
{
  "text": "Long text to summarize...",
  "max_length": 200,
  "agent_name": "default"
}
```

##### `POST /sentiment`
Analyze sentiment.

**Request Body:**
```json
{
  "text": "Text to analyze",
  "agent_name": "default"
}
```

#### Question Answering

##### `POST /question`
Answer questions with optional context.

**Request Body:**
```json
{
  "question": "What is Python?",
  "context": "Python is a programming language...",
  "agent_name": "default"
}
```

#### Agent Management

##### `POST /agents`
Create a new agent.

**Request Body:**
```json
{
  "name": "creative_writer",
  "temperature": 0.9,
  "model_name": "gemini-2.0-flash-exp"
}
```

##### `GET /agents`
List all agents.

**Response:**
```json
["default", "creative_writer", "technical_expert"]
```

##### `DELETE /agents/{agent_name}`
Delete an agent.

##### `POST /agents/{agent_name}/clear-history`
Clear agent's conversation history.

##### `GET /agents/{agent_name}/history`
Get agent's conversation history.

---

## Usage Examples

### Example 1: Basic Conversation

```python
from src.gemini_agent import GeminiAgent

agent = GeminiAgent()

# Single message
response = agent.send_message("Hello! What can you help me with?")
print(response)

# Follow-up (uses context)
response = agent.send_message("Can you give me an example?")
print(response)
```

### Example 2: Document Analysis

```python
agent = GeminiAgent()

document = """
[Your document text here]
"""

# Summarize
summary = agent.summarize(document, max_length=150)

# Extract entities
entities = agent.extract_entities(document)

# Answer questions
answer = agent.answer_question(
    "What are the main points?",
    context=document
)
```

### Example 3: Multi-Agent System

```python
from src.gemini_agent import MultiAgentSystem

mas = MultiAgentSystem()

# Create specialized agents
creative = mas.create_agent("creative", temperature=0.9)
technical = mas.create_agent("technical", temperature=0.3)

# Use different agents for different tasks
story = creative.send_message("Write a short story about AI")
analysis = technical.send_message("Explain how neural networks work")
```

### Example 4: API Client (Python)

```python
import requests

BASE_URL = "http://localhost:8000"

# Send message
response = requests.post(
    f"{BASE_URL}/message",
    json={
        "message": "Explain machine learning",
        "agent_name": "default"
    }
)
print(response.json())

# Create specialized agent
requests.post(
    f"{BASE_URL}/agents",
    json={
        "name": "data_analyst",
        "temperature": 0.5
    }
)

# Use the new agent
response = requests.post(
    f"{BASE_URL}/sentiment",
    json={
        "text": "This is amazing!",
        "agent_name": "data_analyst"
    }
)
print(response.json())
```

### Example 5: API Client (cURL)

```bash
# Health check
curl http://localhost:8000/health

# Send message
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "agent_name": "default"
  }'

# Summarize text
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your long text here...",
    "max_length": 100
  }'
```

### Example 6: API Client (JavaScript)

```javascript
const BASE_URL = 'http://localhost:8000';

// Send message
async function sendMessage(message) {
  const response = await fetch(`${BASE_URL}/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      agent_name: 'default'
    })
  });

  const data = await response.json();
  console.log(data.response);
}

sendMessage('Explain artificial intelligence');
```

---

## Testing

### Running Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov=api

# Run specific test file
pytest tests/test_agent.py
```

### Interactive Testing with Jupyter

1. Start Jupyter:
   ```bash
   jupyter notebook
   ```

2. Open `notebooks/test_gemini_agent.ipynb`

3. Run all cells to test various features

### Manual API Testing

1. Start the API server:
   ```bash
   cd api
   python main.py
   ```

2. Visit http://localhost:8000/docs for interactive API testing

---

## Deployment

### Local Development

```bash
# Start with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

#### Using Uvicorn with Multiple Workers

```bash
uvicorn api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

#### Using Gunicorn

```bash
pip install gunicorn

gunicorn api.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

#### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Build and run:

```bash
docker build -t gemini-agent-api .
docker run -p 8000:8000 --env-file .env gemini-agent-api
```

#### Cloud Deployment Options

1. **AWS**:
   - EC2 with Docker
   - ECS/Fargate
   - Lambda with API Gateway

2. **Google Cloud**:
   - Cloud Run
   - GKE (Kubernetes)
   - App Engine

3. **Azure**:
   - Container Instances
   - AKS (Kubernetes)
   - App Service

4. **Other**:
   - Heroku
   - Railway
   - Render
   - DigitalOcean

---

## Best Practices

### Security

1. **API Keys**: Never commit `.env` files or API keys to version control
2. **Environment Variables**: Use environment variables for sensitive data
3. **CORS**: Configure CORS origins appropriately for production
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Authentication**: Add proper authentication for production use

### Performance

1. **Caching**: Cache frequently requested responses
2. **Connection Pooling**: Reuse HTTP connections
3. **Async Operations**: Use async/await for I/O operations
4. **Worker Processes**: Use multiple workers for production
5. **Load Balancing**: Distribute traffic across multiple instances

### Code Quality

1. **Type Hints**: Use type hints throughout the codebase
2. **Documentation**: Document all functions and classes
3. **Error Handling**: Implement comprehensive error handling
4. **Logging**: Log important events and errors
5. **Testing**: Maintain good test coverage

### Agent Configuration

1. **Temperature**:
   - Low (0.0-0.3): Precise, factual responses
   - Medium (0.4-0.7): Balanced creativity and accuracy
   - High (0.8-1.0): Creative, varied responses

2. **Conversation History**: Clear history periodically to prevent context overflow

3. **Specialized Agents**: Create specialized agents for different tasks

---

## Troubleshooting

### Common Issues

#### 1. API Key Error

**Error**: `Gemini API key not found`

**Solution**:
```bash
# Check .env file exists and has correct key
cat .env

# Verify key is set
echo $GEMINI_API_KEY
```

#### 2. Module Import Error

**Error**: `ModuleNotFoundError: No module named 'gemini_agent'`

**Solution**:
```bash
# Ensure you're in the correct directory
pwd

# Verify PYTHONPATH or use absolute imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 3. Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Kill the process or use different port
uvicorn api.main:app --port 8001
```

#### 4. Rate Limiting

**Error**: `429 Too Many Requests`

**Solution**:
- Wait before retrying
- Implement exponential backoff
- Check your API quota

#### 5. Timeout Errors

**Error**: `Request timeout`

**Solution**:
- Increase timeout in configuration
- Check network connectivity
- Verify API service status

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set in `.env`:
```
LOG_LEVEL=DEBUG
```

---

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pre-commit black flake8 mypy
   ```
4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting
- Use type hints
- Write docstrings for all public functions

### Testing Requirements

- Write tests for new features
- Maintain test coverage above 80%
- Ensure all tests pass before submitting PR

### Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure CI passes
4. Request review from maintainers

---

## License

This project is provided as-is for educational and development purposes.

---

## Contact & Support

For questions, issues, or contributions:

1. Open an issue on GitHub
2. Check existing documentation
3. Review API docs at `/docs` endpoint

---

## Acknowledgments

- **Google Gemini**: For providing the AI API
- **FastAPI**: For the web framework
- **Strands-Agents**: For the agent framework
- **Community**: For contributions and feedback

---

## Changelog

### Version 1.0.0 (2024-11-10)

- Initial release
- Core agent implementation with Gemini
- Multi-agent system support
- Production-ready FastAPI application
- Comprehensive testing notebook
- Full documentation

---

**Last Updated**: November 10, 2024

**Documentation Version**: 1.0.0

**Project Status**: Active Development
