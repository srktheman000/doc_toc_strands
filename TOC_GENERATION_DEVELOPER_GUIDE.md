# Table of Contents (TOC) Generation from PDF Data
## Developer Implementation Guide with Strands Agents

**Version:** 1.0.0
**Last Updated:** November 2025
**Target Audience:** Developers implementing production-ready TOC extraction systems

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Prerequisites](#prerequisites)
4. [Phase 1: PDF Parsing & Text Extraction](#phase-1-pdf-parsing--text-extraction)
5. [Phase 2: TOC Detection](#phase-2-toc-detection)
6. [Phase 3: Structure Extraction](#phase-3-structure-extraction)
7. [Phase 4: Verification & Validation](#phase-4-verification--validation)
8. [Phase 5: Tree Construction](#phase-5-tree-construction)
9. [Phase 6: Enhancement & Enrichment](#phase-6-enhancement--enrichment)
10. [Production Implementation Tasks](#production-implementation-tasks)
11. [Code Examples](#code-examples)
12. [Testing Strategy](#testing-strategy)
13. [Deployment Guide](#deployment-guide)
14. [Troubleshooting](#troubleshooting)
15. [Performance Optimization](#performance-optimization)

---

## Overview

### What is TOC Generation?

Table of Contents (TOC) generation is the process of extracting or generating a hierarchical structure from PDF documents, mapping sections/chapters to their corresponding page numbers and creating a navigable tree structure.

### Why Use Strands Agents with Gemini?

The **strands-agents** library with **Google Gemini** provides:

- **Built-in tool support** (calculator, web search, etc.)
- **Production-ready abstractions** for multi-agent systems
- **Excellent cost-performance ratio** with Gemini models
- **Native async support** for parallel processing
- **Simple, pythonic API**

### Document Flow Overview

```
PDF Document (Input)
        │
        ├─> Parse & Extract Text (PyPDF2/PyMuPDF)
        │
        ├─> Detect TOC (Gemini Agent)
        │   ├─> TOC with page numbers → Mode 1
        │   ├─> TOC without numbers → Mode 2
        │   └─> No TOC → Mode 3 (Generate)
        │
        ├─> Extract Structure (Gemini Agent)
        │
        ├─> Verify Accuracy (Parallel Gemini Agents)
        │
        ├─> Build Tree Structure
        │
        ├─> Generate Summaries (Parallel Gemini Agents)
        │
        └─> JSON Output (hierarchical structure)
```

---

## System Architecture

### High-Level Component Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              FastAPI REST API                           │  │
│  │  • /pdf/upload → Upload PDF                            │  │
│  │  • /pdf/{id}/toc → Generate TOC                        │  │
│  │  • /pdf/{id}/status → Check progress                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │         TOC Generation Service                        │    │
│  │  • PDFParser                                         │    │
│  │  • TOCDetector (Gemini Agent)                        │    │
│  │  • StructureExtractor (Gemini Agent)                 │    │
│  │  • TreeBuilder                                       │    │
│  │  • Verifier (Multi-Agent)                            │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                   AGENT LAYER (Strands)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ TOC Detector │  │ Structure    │  │ Summarizer   │        │
│  │ Agent        │  │ Extractor    │  │ Agent        │        │
│  │ (Gemini)     │  │ Agent        │  │ (Gemini)     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           Multi-Agent System Manager                  │    │
│  │  • Agent pool management                             │    │
│  │  • Task distribution                                 │    │
│  │  • Result aggregation                                │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                   MODEL LAYER                                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           Google Gemini API                          │    │
│  │  • gemini-2.0-flash-exp (default)                    │    │
│  │  • gemini-1.5-pro (for complex tasks)                │    │
│  │  • Rate limiting & retry logic                       │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Dependencies

```txt
# Core dependencies
strands-agents[gemini]==1.15.0
strands-agents-tools==0.2.14
python-dotenv==1.0.1

# PDF processing
PyPDF2==3.0.1
PyMuPDF==1.24.0  # Alternative: better for complex PDFs

# Text processing
tiktoken==0.8.0  # Token counting

# API framework
fastapi==0.115.6
uvicorn==0.38.0
pydantic==2.12.4

# Async support
aiofiles==24.1.0
asyncio==3.4.3

# Utilities
numpy==1.26.4
```

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### API Key Configuration

```.env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Model Configuration
DEFAULT_MODEL=gemini-2.0-flash-exp
DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=2048

# Processing Configuration
TOC_CHECK_PAGE_NUM=20
MAX_PAGE_NUM_EACH_NODE=10
MAX_TOKEN_NUM_EACH_NODE=20000

# Feature Flags
IF_ADD_NODE_ID=yes
IF_ADD_NODE_SUMMARY=yes
IF_ADD_DOC_DESCRIPTION=no
IF_ADD_NODE_TEXT=no
```

---

## Phase 1: PDF Parsing & Text Extraction

### Objective
Extract text content from PDF files with page-level granularity and token counting.

### Implementation Tasks

#### Task 1.1: Set Up PDF Parser Module

**File:** `src/pdf_parser.py`

```python
"""
PDF parsing and text extraction module.
"""

import os
from typing import List, Tuple, Dict
import PyPDF2
import tiktoken
from dotenv import load_dotenv

load_dotenv()


class PDFParser:
    """
    Parse PDF documents and extract text with token counting.
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize PDF parser.

        Args:
            encoding_name: Tokenizer encoding name (for token counting)
        """
        self.encoding = tiktoken.get_encoding(encoding_name)

    def get_page_tokens(self, pdf_path: str) -> List[Tuple[str, int]]:
        """
        Extract text from each page with token counts.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of (page_text, token_count) tuples
        """
        page_list = []

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()

                    # Clean text
                    text = self._clean_text(text)

                    # Count tokens
                    token_count = len(self.encoding.encode(text))

                    page_list.append((text, token_count))

                    print(f"Extracted page {page_num + 1}/{num_pages} "
                          f"({token_count} tokens)")

        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")

        return page_list

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text from PDF

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Fix common OCR issues
        text = text.replace('\x00', '')

        return text

    def get_page_text_range(
        self,
        pdf_path: str,
        start_page: int,
        end_page: int
    ) -> str:
        """
        Get text from a specific page range.

        Args:
            pdf_path: Path to PDF file
            start_page: Starting page (0-indexed)
            end_page: Ending page (0-indexed, inclusive)

        Returns:
            Combined text from page range
        """
        page_list = self.get_page_tokens(pdf_path)

        # Extract text from specified range
        text_range = ' '.join([
            page_list[i][0]
            for i in range(start_page, min(end_page + 1, len(page_list)))
        ])

        return text_range
```

#### Task 1.2: Add Error Handling for Different PDF Types

```python
class PDFParser:
    # ... previous code ...

    def parse_with_fallback(self, pdf_path: str) -> List[Tuple[str, int]]:
        """
        Parse PDF with fallback to alternative library if needed.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of (page_text, token_count) tuples
        """
        try:
            # Try PyPDF2 first
            return self.get_page_tokens(pdf_path)
        except Exception as e:
            print(f"PyPDF2 failed: {e}. Trying PyMuPDF...")

            try:
                # Fallback to PyMuPDF
                return self._parse_with_pymupdf(pdf_path)
            except Exception as e2:
                raise Exception(
                    f"Both parsers failed. PyPDF2: {e}, PyMuPDF: {e2}"
                )

    def _parse_with_pymupdf(self, pdf_path: str) -> List[Tuple[str, int]]:
        """
        Parse PDF using PyMuPDF (fitz).

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of (page_text, token_count) tuples
        """
        import fitz  # PyMuPDF

        page_list = []
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Clean and count tokens
            text = self._clean_text(text)
            token_count = len(self.encoding.encode(text))

            page_list.append((text, token_count))

        doc.close()
        return page_list
```

#### Task 1.3: Create Unit Tests

**File:** `tests/test_pdf_parser.py`

```python
import pytest
from src.pdf_parser import PDFParser


class TestPDFParser:

    @pytest.fixture
    def parser(self):
        return PDFParser()

    def test_parse_simple_pdf(self, parser):
        """Test parsing a simple PDF file."""
        result = parser.get_page_tokens("tests/fixtures/simple.pdf")

        assert len(result) > 0
        assert all(isinstance(page, tuple) for page in result)
        assert all(len(page) == 2 for page in result)

    def test_token_counting(self, parser):
        """Test token counting accuracy."""
        result = parser.get_page_tokens("tests/fixtures/simple.pdf")

        for text, token_count in result:
            assert token_count > 0
            assert token_count == len(parser.encoding.encode(text))

    def test_page_range_extraction(self, parser):
        """Test extracting specific page range."""
        text = parser.get_page_text_range(
            "tests/fixtures/simple.pdf",
            start_page=0,
            end_page=2
        )

        assert isinstance(text, str)
        assert len(text) > 0
```

---

## Phase 2: TOC Detection

### Objective
Detect if a PDF contains a Table of Contents and determine if it has page numbers.

### Implementation Tasks

#### Task 2.1: Create TOC Detector Agent

**File:** `src/agents/toc_detector.py`

```python
"""
TOC detection using Strands Gemini Agent.
"""

import os
from typing import Dict, Optional
from strands import Agent
from strands.models.gemini import GeminiModel
from dotenv import load_dotenv

load_dotenv()


class TOCDetectorAgent:
    """
    Agent for detecting Table of Contents in PDF pages.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.3  # Low temperature for deterministic detection
    ):
        """
        Initialize TOC detector agent.

        Args:
            model_name: Gemini model to use
            temperature: Model temperature (lower = more deterministic)
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        # Initialize Gemini model
        self.model = GeminiModel(
            client_args={"api_key": api_key},
            model_id=model_name,
            params={
                "temperature": temperature,
                "max_output_tokens": 1024,
                "top_p": 0.9,
                "top_k": 40
            }
        )

        # Create agent (no tools needed for this task)
        self.agent = Agent(model=self.model, tools=[])

    def detect_toc_on_page(self, page_text: str, page_num: int) -> Dict:
        """
        Detect if a page contains a Table of Contents.

        Args:
            page_text: Text content of the page
            page_num: Page number (for logging)

        Returns:
            Dict with detection results:
            {
                "has_toc": bool,
                "confidence": float,
                "reasoning": str
            }
        """
        prompt = f"""Analyze this page (page {page_num}) and determine if it contains a Table of Contents (TOC).

Page Content:
{page_text[:3000]}  # Limit context

Instructions:
1. Look for typical TOC indicators:
   - Headers like "Contents", "Table of Contents", "Index"
   - Hierarchical numbering (1, 1.1, 1.2, 2, 2.1, etc.)
   - Chapter/section titles with page numbers
   - Dotted lines connecting titles to numbers

2. Return your analysis as JSON:
{{
    "has_toc": true or false,
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}

Be conservative: only return true if you're confident this is a TOC."""

        response = str(self.agent(prompt))

        # Parse JSON response
        import json
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract from text
            result = {
                "has_toc": "true" in response.lower(),
                "confidence": 0.5,
                "reasoning": "Failed to parse JSON, used text matching"
            }

        return result

    def detect_page_numbers_in_toc(self, toc_text: str) -> Dict:
        """
        Detect if TOC contains page numbers.

        Args:
            toc_text: Extracted TOC text

        Returns:
            Dict with detection results:
            {
                "has_page_numbers": bool,
                "confidence": float,
                "page_number_pattern": str
            }
        """
        prompt = f"""Analyze this Table of Contents and determine if it contains page numbers.

TOC Content:
{toc_text[:2000]}

Instructions:
1. Look for:
   - Numbers after section titles
   - Numbers aligned to the right
   - Dotted lines leading to numbers
   - Patterns like "Chapter 1 ............. 5"

2. Return JSON:
{{
    "has_page_numbers": true or false,
    "confidence": 0.0 to 1.0,
    "page_number_pattern": "description of how page numbers appear"
}}"""

        response = str(self.agent(prompt))

        import json
        try:
            result = json.loads(response)
        except:
            result = {
                "has_page_numbers": False,
                "confidence": 0.5,
                "page_number_pattern": "unknown"
            }

        return result
```

#### Task 2.2: Implement TOC Page Finder

```python
class TOCDetectorAgent:
    # ... previous code ...

    def find_toc_pages(
        self,
        page_list: list,
        max_pages_to_check: int = 20
    ) -> Optional[list]:
        """
        Find which pages contain the Table of Contents.

        Args:
            page_list: List of (page_text, token_count) tuples
            max_pages_to_check: Maximum pages to check (from start)

        Returns:
            List of page indices containing TOC, or None if not found
        """
        toc_pages = []
        pages_to_check = min(max_pages_to_check, len(page_list))

        print(f"\nScanning first {pages_to_check} pages for TOC...")

        for i in range(pages_to_check):
            page_text, _ = page_list[i]

            result = self.detect_toc_on_page(page_text, i + 1)

            if result["has_toc"] and result["confidence"] > 0.7:
                toc_pages.append(i)
                print(f"  ✓ Found TOC on page {i + 1} "
                      f"(confidence: {result['confidence']:.2f})")

        if not toc_pages:
            print("  ✗ No TOC found in first pages")
            return None

        return toc_pages
```

#### Task 2.3: Extract TOC Content

```python
class TOCDetectorAgent:
    # ... previous code ...

    def extract_toc_content(
        self,
        page_list: list,
        toc_page_indices: list
    ) -> str:
        """
        Extract and combine TOC content from multiple pages.

        Args:
            page_list: List of (page_text, token_count) tuples
            toc_page_indices: List of page indices containing TOC

        Returns:
            Combined TOC text
        """
        toc_content = ""

        for page_idx in toc_page_indices:
            page_text, _ = page_list[page_idx]
            toc_content += page_text + "\n\n"

        # Clean TOC content
        toc_content = self._clean_toc_content(toc_content)

        return toc_content

    def _clean_toc_content(self, toc_text: str) -> str:
        """
        Clean extracted TOC text.

        Args:
            toc_text: Raw TOC text

        Returns:
            Cleaned TOC text
        """
        # Remove page headers/footers
        lines = toc_text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip very short lines (likely page numbers or artifacts)
            if len(line.strip()) < 3:
                continue

            # Skip lines that are just numbers
            if line.strip().isdigit():
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)
```

---

## Phase 3: Structure Extraction

### Objective
Extract hierarchical structure from TOC or generate it if no TOC exists.

### Implementation Tasks

#### Task 3.1: Create Structure Extractor Agent

**File:** `src/agents/structure_extractor.py`

```python
"""
Structure extraction using Strands Gemini Agent.
"""

import os
import json
from typing import List, Dict, Optional
from strands import Agent
from strands.models.gemini import GeminiModel
from dotenv import load_dotenv

load_dotenv()


class StructureExtractorAgent:
    """
    Agent for extracting hierarchical structure from TOC or document.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.3
    ):
        """Initialize structure extractor agent."""
        api_key = os.getenv("GEMINI_API_KEY")

        self.model = GeminiModel(
            client_args={"api_key": api_key},
            model_id=model_name,
            params={
                "temperature": temperature,
                "max_output_tokens": 4096,
                "top_p": 0.9,
                "top_k": 40
            }
        )

        self.agent = Agent(model=self.model, tools=[])

    def transform_toc_to_json(
        self,
        toc_content: str,
        has_page_numbers: bool = True
    ) -> List[Dict]:
        """
        Transform TOC text to structured JSON.

        Args:
            toc_content: Raw TOC text
            has_page_numbers: Whether TOC contains page numbers

        Returns:
            List of structured sections:
            [
                {
                    "structure": "1",
                    "title": "Introduction",
                    "page": 1  # Optional
                },
                ...
            ]
        """
        prompt = self._build_toc_transformation_prompt(
            toc_content,
            has_page_numbers
        )

        response = str(self.agent(prompt))

        # Parse JSON response
        try:
            structure = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            structure = self._extract_json_from_text(response)

        return structure

    def _build_toc_transformation_prompt(
        self,
        toc_content: str,
        has_page_numbers: bool
    ) -> str:
        """Build prompt for TOC transformation."""

        base_prompt = f"""Transform this Table of Contents into a structured JSON format.

TOC Content:
{toc_content}

Instructions:
1. Extract each section/chapter with its hierarchical position
2. Detect the numbering structure (1, 1.1, 1.2, 2, 2.1, etc.)
3. Extract the title of each section
"""

        if has_page_numbers:
            base_prompt += """4. Extract the page number for each section

Return JSON array:
[
    {{
        "structure": "1",
        "title": "Introduction",
        "page": 1
    }},
    {{
        "structure": "1.1",
        "title": "Background",
        "page": 2
    }},
    ...
]"""
        else:
            base_prompt += """
Return JSON array:
[
    {{
        "structure": "1",
        "title": "Introduction"
    }},
    {{
        "structure": "1.1",
        "title": "Background"
    }},
    ...
]"""

        base_prompt += """

Rules:
- Maintain hierarchical numbering (1, 1.1, 1.2, 2, 2.1, etc.)
- Keep titles concise and clean
- Preserve the order from the TOC
- Return ONLY valid JSON (no additional text)"""

        return base_prompt

    def _extract_json_from_text(self, text: str) -> List[Dict]:
        """
        Extract JSON from text that may contain additional content.

        Args:
            text: Response text potentially containing JSON

        Returns:
            Extracted JSON structure
        """
        # Find JSON array in text
        import re

        # Look for [...] pattern
        json_match = re.search(r'\[.*\]', text, re.DOTALL)

        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass

        # Fallback: return empty list
        return []
```

#### Task 3.2: Implement No-TOC Structure Generation

```python
class StructureExtractorAgent:
    # ... previous code ...

    def generate_structure_from_text(
        self,
        page_text_chunk: str,
        is_first_chunk: bool = True,
        previous_structure: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Generate hierarchical structure from document text (no TOC).

        Args:
            page_text_chunk: Chunk of document text
            is_first_chunk: Whether this is the first chunk
            previous_structure: Previously extracted structure (for continuation)

        Returns:
            List of structure sections
        """
        if is_first_chunk:
            prompt = self._build_initial_structure_prompt(page_text_chunk)
        else:
            prompt = self._build_continuation_prompt(
                page_text_chunk,
                previous_structure
            )

        response = str(self.agent(prompt))

        try:
            structure = json.loads(response)
        except:
            structure = self._extract_json_from_text(response)

        return structure

    def _build_initial_structure_prompt(self, text: str) -> str:
        """Build prompt for initial structure generation."""
        return f"""Analyze this document text and extract its hierarchical structure.

Document Text:
{text[:8000]}  # Limit context

Instructions:
1. Identify main sections, subsections, and sub-subsections
2. Look for:
   - Chapter headers
   - Section headings
   - Numbered or lettered sections
   - Font size changes (if evident)
   - Hierarchical organization

3. Create a hierarchical numbering structure
4. Note where each section appears in the text

Return JSON:
[
    {{
        "structure": "1",
        "title": "Introduction",
        "physical_index": 1,
        "markers": "text markers that identify this section"
    }},
    {{
        "structure": "1.1",
        "title": "Background",
        "physical_index": 2,
        "markers": "text markers"
    }},
    ...
]

physical_index should be the page number where the section starts (use <physical_index_N> tags if present in text)."""

    def _build_continuation_prompt(
        self,
        text: str,
        previous_structure: List[Dict]
    ) -> str:
        """Build prompt for continuing structure extraction."""
        prev_summary = json.dumps(previous_structure[-5:], indent=2)  # Last 5 items

        return f"""Continue extracting the hierarchical structure from this document.

Previous structure (last few items):
{prev_summary}

Current text chunk:
{text[:8000]}

Instructions:
1. Continue the numbering from the previous structure
2. Identify new sections in this chunk
3. Maintain the same format as previous structure

Return JSON array of new sections found in this chunk."""
```

---

## Phase 4: Verification & Validation

### Objective
Verify extracted TOC accuracy using parallel agent verification.

### Implementation Tasks

#### Task 4.1: Create Verification Agent

**File:** `src/agents/verifier.py`

```python
"""
TOC verification using multiple parallel Gemini agents.
"""

import os
import asyncio
from typing import List, Dict, Tuple
from strands import Agent
from strands.models.gemini import GeminiModel
from dotenv import load_dotenv

load_dotenv()


class VerifierAgent:
    """
    Agent for verifying TOC accuracy.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.1  # Very low for accurate verification
    ):
        """Initialize verifier agent."""
        api_key = os.getenv("GEMINI_API_KEY")

        self.model = GeminiModel(
            client_args={"api_key": api_key},
            model_id=model_name,
            params={
                "temperature": temperature,
                "max_output_tokens": 512,
                "top_p": 0.9,
                "top_k": 40
            }
        )

        self.agent = Agent(model=self.model, tools=[])

    async def verify_single_entry(
        self,
        entry: Dict,
        page_text: str
    ) -> Dict:
        """
        Verify a single TOC entry.

        Args:
            entry: TOC entry to verify
                {
                    "structure": "1.1",
                    "title": "Background",
                    "physical_index": 5
                }
            page_text: Text of the claimed page

        Returns:
            Verification result:
            {
                "entry": original entry,
                "is_correct": bool,
                "confidence": float,
                "actual_page": int or None
            }
        """
        title = entry.get("title", "")
        claimed_page = entry.get("physical_index", entry.get("page", 0))

        prompt = f"""Verify if this section title appears on the claimed page.

Section Title: "{title}"
Claimed Page: {claimed_page}

Page Content:
{page_text[:2000]}

Instructions:
1. Check if the title (or very similar) appears in this page
2. Be flexible with minor variations (capitalization, punctuation)
3. Return JSON:

{{
    "is_correct": true or false,
    "confidence": 0.0 to 1.0,
    "found_text": "actual text found (if any)"
}}

Return ONLY the JSON, no additional text."""

        response = str(self.agent(prompt))

        import json
        try:
            result = json.loads(response)
        except:
            result = {
                "is_correct": False,
                "confidence": 0.0,
                "found_text": ""
            }

        return {
            "entry": entry,
            "is_correct": result.get("is_correct", False),
            "confidence": result.get("confidence", 0.0),
            "actual_page": claimed_page if result.get("is_correct") else None
        }

    async def verify_toc_parallel(
        self,
        toc_structure: List[Dict],
        page_list: List[Tuple[str, int]],
        sample_size: Optional[int] = None
    ) -> Tuple[float, List[Dict]]:
        """
        Verify TOC structure using parallel async agents.

        Args:
            toc_structure: List of TOC entries
            page_list: List of (page_text, token_count) tuples
            sample_size: Number of entries to verify (None = all)

        Returns:
            Tuple of (accuracy, incorrect_entries)
        """
        import random

        # Sample entries if needed
        if sample_size and len(toc_structure) > sample_size:
            entries_to_verify = random.sample(toc_structure, sample_size)
        else:
            entries_to_verify = toc_structure

        print(f"\n🔍 Verifying {len(entries_to_verify)} TOC entries...")

        # Create verification tasks
        tasks = []
        for entry in entries_to_verify:
            page_idx = entry.get("physical_index", entry.get("page", 1)) - 1

            # Ensure page index is valid
            if 0 <= page_idx < len(page_list):
                page_text, _ = page_list[page_idx]
                task = self.verify_single_entry(entry, page_text)
                tasks.append(task)

        # Execute verification in parallel
        results = await asyncio.gather(*tasks)

        # Calculate accuracy
        correct_count = sum(1 for r in results if r["is_correct"])
        accuracy = correct_count / len(results) if results else 0.0

        # Get incorrect entries
        incorrect_entries = [
            r["entry"] for r in results if not r["is_correct"]
        ]

        print(f"  ✓ Accuracy: {accuracy:.2%} ({correct_count}/{len(results)})")

        return accuracy, incorrect_entries
```

#### Task 4.2: Implement Error Fixing

```python
class VerifierAgent:
    # ... previous code ...

    async def fix_incorrect_entry(
        self,
        entry: Dict,
        page_list: List[Tuple[str, int]],
        search_range: int = 5
    ) -> Optional[Dict]:
        """
        Fix an incorrect TOC entry by searching nearby pages.

        Args:
            entry: Incorrect TOC entry
            page_list: List of (page_text, token_count) tuples
            search_range: Number of pages to search before/after

        Returns:
            Corrected entry or None if not found
        """
        title = entry.get("title", "")
        claimed_page = entry.get("physical_index", entry.get("page", 1))

        # Search range
        start_page = max(0, claimed_page - search_range - 1)
        end_page = min(len(page_list), claimed_page + search_range)

        print(f"  🔧 Fixing: {title} (claimed page {claimed_page})")
        print(f"     Searching pages {start_page + 1} to {end_page}")

        # Search each page in range
        for page_idx in range(start_page, end_page):
            page_text, _ = page_list[page_idx]

            result = await self.verify_single_entry(
                {**entry, "physical_index": page_idx + 1},
                page_text
            )

            if result["is_correct"] and result["confidence"] > 0.7:
                corrected_entry = entry.copy()
                corrected_entry["physical_index"] = page_idx + 1

                print(f"     ✓ Found on page {page_idx + 1}")
                return corrected_entry

        print(f"     ✗ Could not find correct page")
        return None
```

---

## Phase 5: Tree Construction

### Objective
Convert flat TOC list to hierarchical tree structure.

### Implementation Tasks

#### Task 5.1: Create Tree Builder

**File:** `src/tree_builder.py`

```python
"""
Tree construction from flat TOC structure.
"""

from typing import List, Dict, Optional


class TreeBuilder:
    """
    Build hierarchical tree from flat TOC structure.
    """

    def list_to_tree(self, flat_structure: List[Dict]) -> List[Dict]:
        """
        Convert flat structure list to hierarchical tree.

        Args:
            flat_structure: Flat list of TOC entries
                [
                    {"structure": "1", "title": "Intro", "physical_index": 1},
                    {"structure": "1.1", "title": "Background", "physical_index": 2},
                    ...
                ]

        Returns:
            Hierarchical tree structure
        """
        if not flat_structure:
            return []

        # Add level information
        for item in flat_structure:
            item["level"] = self._get_level(item["structure"])

        # Build tree recursively
        tree = self._build_tree_recursive(flat_structure, 0)

        # Calculate end indices
        self._calculate_end_indices(tree)

        return tree

    def _get_level(self, structure: str) -> int:
        """
        Get hierarchical level from structure string.

        Args:
            structure: Structure string (e.g., "1.2.3")

        Returns:
            Level (number of dots + 1)
        """
        return structure.count('.') + 1

    def _build_tree_recursive(
        self,
        items: List[Dict],
        current_index: int,
        parent_level: int = 0
    ) -> List[Dict]:
        """
        Recursively build tree structure.

        Args:
            items: List of items to process
            current_index: Current position in list
            parent_level: Level of parent node

        Returns:
            List of tree nodes at current level
        """
        result = []

        i = current_index
        while i < len(items):
            item = items[i]
            item_level = item["level"]

            if item_level <= parent_level:
                # Back to parent level or higher
                break

            if item_level == parent_level + 1:
                # Direct child
                node = {
                    "structure": item.get("structure", ""),
                    "title": item.get("title", ""),
                    "start_index": item.get("physical_index", 0),
                    "end_index": None,  # Will be calculated later
                    "nodes": []
                }

                # Check for children
                if i + 1 < len(items) and items[i + 1]["level"] > item_level:
                    # Has children
                    children, next_i = self._build_tree_recursive(
                        items,
                        i + 1,
                        item_level
                    )
                    node["nodes"] = children
                    i = next_i
                else:
                    i += 1

                result.append(node)
            else:
                # Skip items at deeper levels (handled by recursion)
                i += 1

        return result, i

    def _calculate_end_indices(
        self,
        tree: List[Dict],
        parent_end: Optional[int] = None
    ):
        """
        Calculate end_index for each node.

        Args:
            tree: Tree structure
            parent_end: End index of parent node
        """
        for i, node in enumerate(tree):
            # Get next sibling's start index
            if i + 1 < len(tree):
                next_start = tree[i + 1]["start_index"]
                node["end_index"] = next_start - 1
            else:
                # Last sibling: use parent's end
                node["end_index"] = parent_end or node["start_index"]

            # Recursively process children
            if node.get("nodes"):
                self._calculate_end_indices(
                    node["nodes"],
                    node["end_index"]
                )
```

#### Task 5.2: Add Post-Processing

```python
class TreeBuilder:
    # ... previous code ...

    def add_node_ids(self, tree: List[Dict], prefix: str = "") -> List[Dict]:
        """
        Add sequential node IDs to tree.

        Args:
            tree: Tree structure
            prefix: Prefix for node IDs

        Returns:
            Tree with node_id added to each node
        """
        counter = [1]  # Use list to make it mutable in nested function

        def add_id_recursive(nodes, path=""):
            for node in nodes:
                node_id = f"{counter[0]:04d}"  # e.g., "0001"
                node["node_id"] = node_id
                counter[0] += 1

                if node.get("nodes"):
                    add_id_recursive(node["nodes"], f"{path}/{node_id}")

        add_id_recursive(tree)
        return tree
```

---

## Phase 6: Enhancement & Enrichment

### Objective
Add summaries, descriptions, and other metadata to the tree structure.

### Implementation Tasks

#### Task 6.1: Create Summarizer Agent

**File:** `src/agents/summarizer.py`

```python
"""
Content summarization using Strands Gemini Agent.
"""

import os
import asyncio
from typing import List, Dict
from strands import Agent
from strands.models.gemini import GeminiModel
from dotenv import load_dotenv

load_dotenv()


class SummarizerAgent:
    """
    Agent for generating summaries of document sections.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.5
    ):
        """Initialize summarizer agent."""
        api_key = os.getenv("GEMINI_API_KEY")

        self.model = GeminiModel(
            client_args={"api_key": api_key},
            model_id=model_name,
            params={
                "temperature": temperature,
                "max_output_tokens": 512,
                "top_p": 0.9,
                "top_k": 40
            }
        )

        self.agent = Agent(model=self.model, tools=[])

    async def generate_summary(
        self,
        title: str,
        content: str,
        max_length: int = 150
    ) -> str:
        """
        Generate a summary for a document section.

        Args:
            title: Section title
            content: Section content
            max_length: Maximum summary length in words

        Returns:
            Summary text
        """
        prompt = f"""Create a concise summary of this document section.

Section Title: {title}

Content:
{content[:4000]}  # Limit context

Instructions:
1. Summarize the main points
2. Keep it under {max_length} words
3. Focus on key information
4. Write in clear, professional language

Return ONLY the summary text, no JSON or additional formatting."""

        response = str(self.agent(prompt))

        # Clean response
        summary = response.strip()

        # Truncate if needed
        words = summary.split()
        if len(words) > max_length:
            summary = ' '.join(words[:max_length]) + '...'

        return summary

    async def generate_summaries_parallel(
        self,
        tree: List[Dict],
        page_list: List[tuple]
    ) -> List[Dict]:
        """
        Generate summaries for all nodes in parallel.

        Args:
            tree: Tree structure
            page_list: List of (page_text, token_count) tuples

        Returns:
            Tree with summaries added
        """
        print("\n📝 Generating summaries...")

        # Collect all nodes
        all_nodes = []
        self._collect_nodes(tree, all_nodes)

        # Create tasks
        tasks = []
        for node in all_nodes:
            start_idx = node.get("start_index", 1) - 1
            end_idx = node.get("end_index", start_idx + 1) - 1

            # Extract content
            content = self._extract_node_content(
                page_list,
                start_idx,
                end_idx
            )

            task = self.generate_summary(
                node.get("title", ""),
                content
            )
            tasks.append((node, task))

        # Execute in parallel
        for node, task in tasks:
            node["summary"] = await task
            print(f"  ✓ {node.get('title', 'Untitled')}")

        return tree

    def _collect_nodes(self, tree: List[Dict], result: List[Dict]):
        """Recursively collect all nodes."""
        for node in tree:
            result.append(node)
            if node.get("nodes"):
                self._collect_nodes(node["nodes"], result)

    def _extract_node_content(
        self,
        page_list: List[tuple],
        start_idx: int,
        end_idx: int
    ) -> str:
        """Extract text content for a node."""
        content = ""
        for i in range(start_idx, min(end_idx + 1, len(page_list))):
            page_text, _ = page_list[i]
            content += page_text + " "

        return content.strip()
```

---

## Production Implementation Tasks

### Task P1: Multi-Agent System Manager

**File:** `src/multi_agent_manager.py`

```python
"""
Multi-agent system manager for coordinating TOC generation.
"""

import asyncio
from typing import List, Dict, Tuple
from src.pdf_parser import PDFParser
from src.agents.toc_detector import TOCDetectorAgent
from src.agents.structure_extractor import StructureExtractorAgent
from src.agents.verifier import VerifierAgent
from src.agents.summarizer import SummarizerAgent
from src.tree_builder import TreeBuilder


class MultiAgentTOCManager:
    """
    Orchestrate multiple agents for complete TOC generation pipeline.
    """

    def __init__(self):
        """Initialize all agents and components."""
        self.pdf_parser = PDFParser()
        self.toc_detector = TOCDetectorAgent()
        self.structure_extractor = StructureExtractorAgent()
        self.verifier = VerifierAgent()
        self.summarizer = SummarizerAgent()
        self.tree_builder = TreeBuilder()

    async def generate_toc(
        self,
        pdf_path: str,
        add_summaries: bool = True,
        add_node_ids: bool = True
    ) -> Dict:
        """
        Complete TOC generation pipeline.

        Args:
            pdf_path: Path to PDF file
            add_summaries: Whether to generate summaries
            add_node_ids: Whether to add node IDs

        Returns:
            Complete TOC structure as JSON
        """
        print(f"\n{'='*60}")
        print(f"TOC Generation Pipeline: {pdf_path}")
        print(f"{'='*60}")

        # Phase 1: Parse PDF
        print("\n[Phase 1] Parsing PDF...")
        page_list = self.pdf_parser.get_page_tokens(pdf_path)
        print(f"✓ Extracted {len(page_list)} pages")

        # Phase 2: Detect TOC
        print("\n[Phase 2] Detecting TOC...")
        toc_pages = self.toc_detector.find_toc_pages(page_list)

        if toc_pages:
            # Has TOC
            toc_content = self.toc_detector.extract_toc_content(
                page_list,
                toc_pages
            )

            # Check for page numbers
            page_num_result = self.toc_detector.detect_page_numbers_in_toc(
                toc_content
            )
            has_page_numbers = page_num_result["has_page_numbers"]

            print(f"✓ Found TOC on pages: {[p+1 for p in toc_pages]}")
            print(f"✓ Has page numbers: {has_page_numbers}")
        else:
            # No TOC
            toc_content = None
            has_page_numbers = False
            print("✗ No TOC found - will generate structure")

        # Phase 3: Extract Structure
        print("\n[Phase 3] Extracting Structure...")
        if toc_content:
            toc_structure = self.structure_extractor.transform_toc_to_json(
                toc_content,
                has_page_numbers
            )
        else:
            # Generate structure from document
            toc_structure = await self._generate_structure_no_toc(page_list)

        print(f"✓ Extracted {len(toc_structure)} top-level sections")

        # Phase 4: Verify & Fix
        print("\n[Phase 4] Verifying Accuracy...")
        accuracy, incorrect_entries = await self.verifier.verify_toc_parallel(
            toc_structure,
            page_list,
            sample_size=min(30, len(toc_structure))
        )

        if accuracy < 0.6:
            print(f"⚠ Low accuracy ({accuracy:.1%}), attempting fixes...")
            # Attempt to fix incorrect entries
            fixed_count = 0
            for entry in incorrect_entries:
                fixed = await self.verifier.fix_incorrect_entry(
                    entry,
                    page_list
                )
                if fixed:
                    # Update entry
                    for i, e in enumerate(toc_structure):
                        if e.get("structure") == entry.get("structure"):
                            toc_structure[i] = fixed
                            fixed_count += 1
                            break
            print(f"✓ Fixed {fixed_count}/{len(incorrect_entries)} entries")

        # Phase 5: Build Tree
        print("\n[Phase 5] Building Tree Structure...")
        tree = self.tree_builder.list_to_tree(toc_structure)
        print(f"✓ Built hierarchical tree")

        # Phase 6: Add Enhancements
        if add_node_ids:
            print("\n[Phase 6a] Adding Node IDs...")
            tree = self.tree_builder.add_node_ids(tree)
            print("✓ Added sequential node IDs")

        if add_summaries:
            print("\n[Phase 6b] Generating Summaries...")
            tree = await self.summarizer.generate_summaries_parallel(
                tree,
                page_list
            )
            print("✓ Generated summaries for all nodes")

        # Final output
        result = {
            "doc_name": pdf_path.split('/')[-1],
            "total_pages": len(page_list),
            "has_toc": toc_content is not None,
            "accuracy": accuracy,
            "structure": tree
        }

        print(f"\n{'='*60}")
        print("✅ TOC Generation Complete!")
        print(f"{'='*60}\n")

        return result

    async def _generate_structure_no_toc(
        self,
        page_list: List[Tuple[str, int]]
    ) -> List[Dict]:
        """
        Generate structure when no TOC is present.

        Args:
            page_list: List of (page_text, token_count) tuples

        Returns:
            Generated structure
        """
        # Chunk pages into processable sizes
        chunks = self._create_chunks(page_list, max_tokens=20000)

        all_structure = []

        for i, chunk in enumerate(chunks):
            is_first = (i == 0)

            structure = self.structure_extractor.generate_structure_from_text(
                chunk,
                is_first_chunk=is_first,
                previous_structure=all_structure
            )

            all_structure.extend(structure)
            print(f"  ✓ Processed chunk {i+1}/{len(chunks)} "
                  f"({len(structure)} sections)")

        return all_structure

    def _create_chunks(
        self,
        page_list: List[Tuple[str, int]],
        max_tokens: int
    ) -> List[str]:
        """Create text chunks under token limit."""
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for page_text, token_count in page_list:
            if current_tokens + token_count > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = page_text
                current_tokens = token_count
            else:
                current_chunk += "\n" + page_text
                current_tokens += token_count

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
```

### Task P2: FastAPI Application

**File:** `api/toc_api.py`

```python
"""
FastAPI application for TOC generation service.
"""

import os
import uuid
import asyncio
from typing import Dict, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from datetime import datetime

from src.multi_agent_manager import MultiAgentTOCManager


app = FastAPI(
    title="TOC Generation API",
    description="Extract Table of Contents from PDFs using Gemini agents",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (use Redis/database in production)
jobs: Dict[str, Dict] = {}

# Models
class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class TOCGenerationRequest(BaseModel):
    add_summaries: bool = True
    add_node_ids: bool = True


# Routes
@app.post("/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file for TOC generation."""

    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")

    # Save file
    job_id = str(uuid.uuid4())
    file_path = f"./uploads/{job_id}.pdf"

    os.makedirs("./uploads", exist_ok=True)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create job
    jobs[job_id] = {
        "job_id": job_id,
        "status": "uploaded",
        "file_path": file_path,
        "filename": file.filename,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None
    }

    return {
        "job_id": job_id,
        "filename": file.filename,
        "message": "File uploaded successfully"
    }


@app.post("/pdf/{job_id}/generate")
async def generate_toc(
    job_id: str,
    request: TOCGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate TOC for uploaded PDF."""

    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    job = jobs[job_id]

    if job["status"] != "uploaded":
        raise HTTPException(400, f"Job status is {job['status']}")

    # Start generation in background
    background_tasks.add_task(
        run_toc_generation,
        job_id,
        job["file_path"],
        request.add_summaries,
        request.add_node_ids
    )

    job["status"] = "processing"

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "TOC generation started"
    }


@app.get("/pdf/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of TOC generation job."""

    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    return JobStatus(**jobs[job_id])


@app.get("/pdf/{job_id}/result")
async def get_toc_result(job_id: str):
    """Get TOC generation result."""

    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(400, f"Job status is {job['status']}")

    if job["error"]:
        raise HTTPException(500, job["error"])

    return job["result"]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_jobs": len([j for j in jobs.values() if j["status"] == "processing"])
    }


# Background task
async def run_toc_generation(
    job_id: str,
    pdf_path: str,
    add_summaries: bool,
    add_node_ids: bool
):
    """Run TOC generation asynchronously."""

    try:
        manager = MultiAgentTOCManager()

        result = await manager.generate_toc(
            pdf_path,
            add_summaries=add_summaries,
            add_node_ids=add_node_ids
        )

        # Update job
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = result
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

        # Save result to file
        output_path = f"./results/{job_id}_toc.json"
        os.makedirs("./results", exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        jobs[job_id]["output_path"] = output_path

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Code Examples

### Example 1: Simple TOC Generation

```python
"""
Simple example of TOC generation.
"""

import asyncio
from src.multi_agent_manager import MultiAgentTOCManager


async def main():
    # Initialize manager
    manager = MultiAgentTOCManager()

    # Generate TOC
    result = await manager.generate_toc(
        pdf_path="sample.pdf",
        add_summaries=True,
        add_node_ids=True
    )

    # Print result
    import json
    print(json.dumps(result, indent=2))

    # Save to file
    with open("toc_output.json", "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Using Individual Agents

```python
"""
Example using individual agents for more control.
"""

import asyncio
from src.pdf_parser import PDFParser
from src.agents.toc_detector import TOCDetectorAgent
from src.agents.structure_extractor import StructureExtractorAgent


async def main():
    # Parse PDF
    parser = PDFParser()
    pages = parser.get_page_tokens("sample.pdf")

    # Detect TOC
    detector = TOCDetectorAgent()
    toc_pages = detector.find_toc_pages(pages, max_pages_to_check=20)

    if toc_pages:
        # Extract TOC content
        toc_content = detector.extract_toc_content(pages, toc_pages)

        # Check for page numbers
        has_nums = detector.detect_page_numbers_in_toc(toc_content)

        # Extract structure
        extractor = StructureExtractorAgent()
        structure = extractor.transform_toc_to_json(
            toc_content,
            has_page_numbers=has_nums["has_page_numbers"]
        )

        print(f"Extracted {len(structure)} sections")

        for section in structure[:5]:  # Print first 5
            print(f"  {section['structure']} - {section['title']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_toc_detector.py

import pytest
from src.agents.toc_detector import TOCDetectorAgent


class TestTOCDetector:

    @pytest.fixture
    def detector(self):
        return TOCDetectorAgent()

    def test_detect_toc_positive(self, detector):
        """Test TOC detection on page with TOC."""
        sample_toc = """
        Table of Contents

        1. Introduction ................... 1
        2. Background ..................... 5
        3. Methodology .................... 10
        """

        result = detector.detect_toc_on_page(sample_toc, 1)

        assert result["has_toc"] == True
        assert result["confidence"] > 0.7

    def test_detect_page_numbers(self, detector):
        """Test page number detection."""
        toc_with_numbers = """
        1. Chapter One ........ 10
        2. Chapter Two ........ 25
        """

        result = detector.detect_page_numbers_in_toc(toc_with_numbers)

        assert result["has_page_numbers"] == True
```

### Integration Tests

```python
# tests/test_integration.py

import pytest
import asyncio
from src.multi_agent_manager import MultiAgentTOCManager


@pytest.mark.asyncio
async def test_full_pipeline():
    """Test complete TOC generation pipeline."""

    manager = MultiAgentTOCManager()

    result = await manager.generate_toc(
        "tests/fixtures/sample.pdf",
        add_summaries=False,  # Faster for testing
        add_node_ids=True
    )

    assert result is not None
    assert "structure" in result
    assert len(result["structure"]) > 0
    assert result["doc_name"] == "sample.pdf"
```

---

## Deployment Guide

### Production Deployment Checklist

- [ ] Set up environment variables securely
- [ ] Configure API rate limiting
- [ ] Set up Redis for job queue
- [ ] Add authentication/authorization
- [ ] Configure logging and monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Deploy with Docker
- [ ] Set up CI/CD pipeline
- [ ] Configure load balancer
- [ ] Add backup strategy

### Docker Deployment

**Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/results

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.toc_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  toc-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DEFAULT_MODEL=gemini-2.0-flash-exp
    volumes:
      - ./uploads:/app/uploads
      - ./results:/app/results
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

---

## Troubleshooting

### Common Issues

**Issue 1: API Rate Limits**
```
Error: 429 Too Many Requests
```

**Solution:**
- Implement exponential backoff
- Reduce parallel agent count
- Use rate limiting middleware

**Issue 2: Low TOC Accuracy**
```
Warning: Accuracy < 60%
```

**Solution:**
- Check PDF quality (OCR issues)
- Adjust verification sample size
- Try alternative PDF parser (PyMuPDF)

**Issue 3: Memory Issues with Large PDFs**
```
Error: Out of memory
```

**Solution:**
- Process in smaller chunks
- Stream pages instead of loading all
- Increase system resources

---

## Performance Optimization

### Optimization Strategies

1. **Parallel Processing**
   - Use asyncio for concurrent agent calls
   - Batch verification tasks
   - Parallel summary generation

2. **Caching**
   - Cache PDF parsing results
   - Store intermediate results
   - Use Redis for distributed caching

3. **Token Optimization**
   - Truncate long contexts intelligently
   - Use smaller models for simple tasks
   - Batch similar requests

4. **Resource Management**
   - Connection pooling
   - Agent pool management
   - Memory-efficient data structures

---

## Conclusion

This guide provides a complete blueprint for implementing production-ready TOC generation from PDF documents using Strands Agents with Google Gemini. Follow the phased approach, implement the provided code examples, and adapt to your specific requirements.

**Key Takeaways:**

1. **Multi-Phase Pipeline**: Parse → Detect → Extract → Verify → Build → Enhance
2. **Strands Agents**: Leverage official library for robust, scalable agent management
3. **Parallel Processing**: Use async/await for maximum throughput
4. **Verification Critical**: Always verify and fix extracted structures
5. **Production Ready**: Include monitoring, error handling, and testing

**Next Steps:**

1. Set up development environment
2. Implement Phase 1 (PDF Parsing)
3. Create and test individual agents
4. Build multi-agent orchestration
5. Add API layer
6. Deploy to production

For questions or contributions, refer to the main project documentation.

---

**Document Version:** 1.0.0
**Last Updated:** November 2025
**Maintainer:** Development Team
