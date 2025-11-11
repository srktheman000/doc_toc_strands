# PageIndex Developer Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Project Overview](#project-overview)
3. [Architecture](#architecture)
4. [Core Concepts](#core-concepts)
5. [Module Deep Dive](#module-deep-dive)
6. [Working with the Code](#working-with-the-code)
7. [Advanced Topics](#advanced-topics)
8. [Best Practices](#best-practices)

---

## Introduction

Welcome to the **PageIndex Developer Guide**! This guide is designed for Python developers and generative AI enthusiasts who want to understand how PageIndex works under the hood.

### What is PageIndex?

PageIndex is a **reasoning-based RAG (Retrieval-Augmented Generation)** system that:

- Transforms long documents into hierarchical tree structures
- Uses LLM reasoning instead of vector similarity for retrieval
- Eliminates the need for chunking and vector databases
- Mimics how human experts navigate complex documents

### Who is This Guide For?

- Python developers learning about generative AI applications
- AI engineers building RAG systems
- Researchers exploring document understanding
- Anyone curious about LLM-based document processing

---

## Project Overview

### Directory Structure

```
PageIndex/
├── pageindex/              # Core library code
│   ├── __init__.py        # Package initialization
│   ├── page_index.py      # Main PDF processing logic
│   ├── page_index_md.py   # Markdown processing logic
│   ├── utils.py           # Utility functions (API calls, helpers)
│   └── config.yaml        # Default configuration
├── run_pageindex.py       # CLI entry point
├── tests/                 # Test documents and results
│   ├── pdfs/             # Sample PDF files
│   └── results/          # Generated tree structures
├── cookbook/              # Example notebooks
└── tutorials/             # Learning materials
```

### Key Files

| File               | Purpose                                                |
| ------------------ | ------------------------------------------------------ |
| `page_index.py`    | PDF document processing, TOC extraction, tree building |
| `page_index_md.py` | Markdown document processing                           |
| `utils.py`         | LLM API calls, PDF parsing, helper functions           |
| `run_pageindex.py` | Command-line interface                                 |
| `config.yaml`      | Default configuration parameters                       |

---

## Architecture

### High-Level Flow

```
┌─────────────────┐
│  Input Document │
│   (PDF/MD)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  Extract Text       │
│  & Detect TOC       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Process TOC        │
│  (with/without      │
│   page numbers)     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Build Tree         │
│  Structure          │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Verify & Fix       │
│  Physical Indices   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Process Large      │
│  Nodes Recursively  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Generate           │
│  Summaries          │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Output Tree        │
│  Structure (JSON)   │
└─────────────────────┘
```

### Three Processing Modes

PageIndex handles documents in three different ways:

1. **TOC with Page Numbers**: Document has a table of contents with page numbers
   - Fastest and most accurate
   - Extracts TOC and maps to physical pages
2. **TOC without Page Numbers**: Document has a TOC but no page numbers
   - Searches through document to find where sections start
   - More computationally expensive
3. **No TOC**: Document has no table of contents
   - Generates structure by analyzing document content
   - Most expensive but fully automatic

---

## Core Concepts

### 1. Tree Structure

PageIndex represents documents as hierarchical trees:

```json
{
  "title": "Chapter 1",
  "node_id": "0001",
  "start_index": 5,
  "end_index": 15,
  "summary": "This chapter discusses...",
  "nodes": [
    {
      "title": "Section 1.1",
      "node_id": "0002",
      "start_index": 5,
      "end_index": 10,
      "summary": "...",
      "nodes": []
    }
  ]
}
```

**Key Fields:**

- `title`: Section heading
- `node_id`: Unique identifier (4-digit, zero-padded)
- `start_index`: First page of this section
- `end_index`: Last page of this section
- `summary`: AI-generated description
- `nodes`: Child sections (recursive structure)

### 2. Physical vs Logical Indices

- **Physical Index**: Actual page number in the PDF (1-based)
- **Logical Index**: Page number as printed in the document (may differ)
- **Structure Index**: Hierarchical numbering (e.g., "1.2.3")

### 3. Reasoning-Based Retrieval

Instead of semantic similarity, PageIndex uses:

- **LLM reasoning** to understand document structure
- **Tree search** to navigate hierarchically
- **Context-aware matching** based on section relationships

---

## Module Deep Dive

### utils.py - Foundation Layer

This module provides the building blocks for all operations.

#### LLM API Functions

```python
# Synchronous API call
def ChatGPT_API(model, prompt, api_key=None, chat_history=None):
    """
    Makes a synchronous call to OpenAI's API

    Args:
        model: Model name (e.g., "gpt-4o-2024-11-20")
        prompt: Input text for the model
        api_key: OpenAI API key (from env if not provided)
        chat_history: Previous conversation messages

    Returns:
        str: Model's response text

    Features:
        - Automatic retry logic (10 attempts)
        - Temperature set to 0 for consistency
        - Error handling with exponential backoff
    """
```

```python
# Asynchronous API call (for parallel processing)
async def ChatGPT_API_async(model, prompt, api_key=None):
    """
    Asynchronous version for concurrent API calls

    Used when processing multiple nodes in parallel
    Example: Generating summaries for all nodes simultaneously
    """
```

**Why Async?** When processing a document with 50 sections, async calls can:

- Process all sections concurrently
- Reduce total time from ~5 minutes to ~30 seconds
- Better utilize API rate limits

#### Token Management

```python
def count_tokens(text, model=None):
    """
    Counts tokens using tiktoken

    Why it matters:
        - Prevents context overflow
        - Estimates API costs
        - Determines node splitting strategy

    Returns:
        int: Number of tokens in text
    """
```

#### PDF Parsing

```python
def get_page_tokens(pdf_path, model="gpt-4o-2024-11-20", pdf_parser="PyPDF2"):
    """
    Extracts text from PDF pages with token counts

    Args:
        pdf_path: Path to PDF or BytesIO object
        model: Model for token counting
        pdf_parser: "PyPDF2" or "PyMuPDF"

    Returns:
        list: [(page_text, token_count), ...]

    Note: PyMuPDF generally provides better text extraction
    """
```

#### JSON Extraction

````python
def extract_json(content):
    """
    Robustly extracts JSON from LLM responses

    Handles:
        - JSON wrapped in ```json blocks
        - Python None → JSON null conversion
        - Trailing commas
        - Whitespace issues

    Critical for reliable LLM parsing!
    """
````

#### Structure Manipulation

```python
def structure_to_list(structure):
    """Flattens tree to list (preserves order)"""

def get_leaf_nodes(structure):
    """Gets only bottom-level nodes"""

def write_node_id(data, node_id=0):
    """Assigns sequential IDs to all nodes"""
```

---

### page_index.py - PDF Processing Engine

This is the heart of PageIndex for PDF documents.

#### Main Entry Point

```python
def page_index_main(doc, opt=None):
    """
    Main processing function

    Flow:
        1. Parse PDF to extract text and tokens
        2. Build tree structure (async)
        3. Add node IDs
        4. Add text content (if requested)
        5. Generate summaries (if requested)
        6. Generate doc description (if requested)

    Returns:
        dict: {
            'doc_name': str,
            'doc_description': str (optional),
            'structure': list of nodes
        }
    """
```

#### TOC Detection

```python
def toc_detector_single_page(content, model=None):
    """
    Detects if a page contains a table of contents

    Uses LLM to identify TOC characteristics:
        - List of section titles
        - Hierarchical structure
        - Page numbers (optional)

    Returns: "yes" or "no"
    """

def find_toc_pages(start_page_index, page_list, opt, logger=None):
    """
    Finds all consecutive TOC pages

    Algorithm:
        1. Check pages sequentially from start
        2. Stop after toc_check_page_num pages without TOC
        3. Continue if consecutive TOC pages found

    Returns: List of page indices containing TOC
    """
```

#### TOC Extraction & Transformation

```python
def toc_transformer(toc_content, model=None):
    """
    Converts raw TOC text to structured JSON

    Process:
        1. Extract hierarchical structure
        2. Parse section numbering (e.g., "1.2.3")
        3. Extract titles
        4. Extract page numbers (if present)

    Handles:
        - Multi-page TOCs
        - Incomplete responses (continues generation)
        - Various TOC formats

    Output format:
        [
            {
                "structure": "1",
                "title": "Introduction",
                "page": 5
            },
            {
                "structure": "1.1",
                "title": "Background",
                "page": 7
            }
        ]
    """
```

#### Page Number Mapping

```python
def calculate_page_offset(pairs):
    """
    Calculates offset between logical and physical pages

    Example:
        - Document shows "Page 1" on physical page 5
        - Offset = 4

    Uses:
        - Multiple reference points for accuracy
        - Most common offset (majority voting)

    Returns: int offset
    """

def add_page_offset_to_toc_json(data, offset):
    """
    Converts logical page numbers to physical indices

    Example:
        - TOC says "Page 10"
        - Offset is 4
        - Physical index = 14
    """
```

#### Verification & Fixing

```python
async def verify_toc(page_list, list_result, start_index=1, N=None, model=None):
    """
    Verifies extracted TOC entries against actual document

    Process:
        1. Sample N entries (or check all)
        2. For each entry, check if title appears on claimed page
        3. Calculate accuracy

    Returns:
        accuracy: float (0.0 to 1.0)
        incorrect_results: list of failed entries

    Accuracy thresholds:
        - 1.0: Perfect, use as-is
        - > 0.6: Good, fix incorrect entries
        - < 0.6: Poor, try different method
    """

async def fix_incorrect_toc(toc_with_page_number, page_list, incorrect_results, ...):
    """
    Fixes incorrect TOC entries

    For each incorrect entry:
        1. Find range (previous correct to next correct entry)
        2. Search within range for actual location
        3. Verify fixed location

    Uses binary search strategy to narrow down location
    """
```

#### Tree Construction

```python
def list_to_tree(flat_list):
    """
    Converts flat list to hierarchical tree

    Algorithm:
        1. Use structure index (e.g., "1.2.3") to determine nesting
        2. Build parent-child relationships
        3. Preserve order

    Example:
        Input: [
            {"structure": "1", ...},
            {"structure": "1.1", ...},
            {"structure": "2", ...}
        ]

        Output: [
            {
                "structure": "1",
                "nodes": [
                    {"structure": "1.1", "nodes": []}
                ]
            },
            {"structure": "2", "nodes": []}
        ]
    """

def post_processing(structure, end_physical_index):
    """
    Finalizes tree structure

    Sets:
        - start_index: Where section begins
        - end_index: Where section ends

    Note: Child's end_index may be parent's start_index - 1
    """
```

#### Large Node Processing

```python
async def process_large_node_recursively(node, page_list, opt=None, logger=None):
    """
    Subdivides large nodes recursively

    Conditions for subdivision:
        - Node spans > max_page_num_each_node pages
        - Node has > max_token_num_each_node tokens

    Process:
        1. Extract text from node's pages
        2. Generate sub-structure (no TOC mode)
        3. Attach as child nodes
        4. Process children recursively

    This ensures no node exceeds LLM context limits!
    """
```

#### Summary Generation

```python
async def generate_summaries_for_structure(structure, model=None):
    """
    Generates summaries for all nodes in parallel

    Process:
        1. Flatten tree to list
        2. Create async tasks for each node
        3. Execute all tasks concurrently
        4. Assign summaries back to nodes

    Typical prompt:
        "Summarize the main points covered in this section:
         [section text]"
    """
```

---

### page_index_md.py - Markdown Processing

Handles Markdown files differently than PDFs.

#### Node Extraction

````python
def extract_nodes_from_markdown(markdown_content):
    """
    Extracts headers from Markdown

    Strategy:
        - Use regex to find lines starting with #, ##, ###, etc.
        - Skip code blocks (ignore ``` sections)
        - Record line numbers

    Returns:
        node_list: List of {node_title, line_num}
        lines: All lines in document
    """

def extract_node_text_content(node_list, markdown_lines):
    """
    Extracts text for each node

    Algorithm:
        - Text for a node = from its header to next header
        - Last node extends to end of file

    Also determines:
        - Level: Number of # symbols (1-6)
    """
````

#### Tree Thinning

```python
def tree_thinning_for_index(node_list, min_node_token=None, model=None):
    """
    Merges small nodes into parents

    Problem:
        - Very small sections fragment the tree
        - Inefficient for retrieval

    Solution:
        - If node + all descendants < min_node_token
        - Merge all descendants into parent
        - Remove descendants as separate nodes

    Example:
        Before:
            Section 1 (100 tokens)
                ├─ 1.1 (50 tokens)
                └─ 1.2 (50 tokens)

        After (if threshold = 300):
            Section 1 (200 tokens, merged content)
    """
```

#### Tree Building

```python
def build_tree_from_nodes(node_list):
    """
    Constructs tree from flat list of Markdown headers

    Uses stack-based algorithm:
        1. For each node, check its level
        2. Pop stack until parent level is less
        3. Attach to parent (or root)
        4. Push to stack

    Time complexity: O(n)
    """
```

---

## Working with the Code

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/VectifyAI/PageIndex.git
cd PageIndex

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "CHATGPT_API_KEY=your_key_here" > .env
```

### Running PageIndex

#### Basic Usage

```bash
# Process a PDF
python run_pageindex.py --pdf_path tests/pdfs/2023-annual-report.pdf

# Process a Markdown file
python run_pageindex.py --md_path docs/example.md
```

#### Advanced Options

```bash
# Customize model
python run_pageindex.py \
    --pdf_path document.pdf \
    --model gpt-4o-2024-11-20

# Control node size
python run_pageindex.py \
    --pdf_path document.pdf \
    --max-pages-per-node 15 \
    --max-tokens-per-node 30000

# Generate summaries and description
python run_pageindex.py \
    --pdf_path document.pdf \
    --if-add-node-summary yes \
    --if-add-doc-description yes

# Include full text in output
python run_pageindex.py \
    --pdf_path document.pdf \
    --if-add-node-text yes
```

### Using PageIndex as a Library

```python
from pageindex import page_index

# Basic usage
result = page_index(
    doc="path/to/document.pdf",
    model="gpt-4o-2024-11-20"
)

print(result['doc_name'])
print(result['structure'])

# Advanced usage
result = page_index(
    doc="path/to/document.pdf",
    model="gpt-4o-2024-11-20",
    toc_check_page_num=25,  # Check first 25 pages for TOC
    max_page_num_each_node=12,  # Max 12 pages per node
    max_token_num_each_node=25000,  # Max 25k tokens per node
    if_add_node_id="yes",
    if_add_node_summary="yes",
    if_add_doc_description="yes",
    if_add_node_text="no"
)

# Access the tree structure
for node in result['structure']:
    print(f"Title: {node['title']}")
    print(f"Pages: {node['start_index']} - {node['end_index']}")
    if 'summary' in node:
        print(f"Summary: {node['summary']}")
    print()
```

### Markdown Processing

```python
import asyncio
from pageindex.page_index_md import md_to_tree

async def process_markdown():
    result = await md_to_tree(
        md_path="path/to/document.md",
        if_thinning=True,
        min_token_threshold=5000,  # Merge nodes smaller than 5k tokens
        if_add_node_summary="yes",
        summary_token_threshold=200,
        model="gpt-4o-2024-11-20",
        if_add_doc_description="yes",
        if_add_node_text="no",
        if_add_node_id="yes"
    )
    return result

# Run async function
result = asyncio.run(process_markdown())
```

---

## Advanced Topics

### Custom Configuration

Create a custom config file:

```yaml
# my_config.yaml
model: "gpt-4o-2024-11-20"
toc_check_page_num: 30
max_page_num_each_node: 15
max_token_num_each_node: 30000
if_add_node_id: "yes"
if_add_node_summary: "yes"
if_add_doc_description: "yes"
if_add_node_text: "no"
```

Load custom config:

```python
from pageindex.utils import ConfigLoader
from types import SimpleNamespace as config

# Load custom config
loader = ConfigLoader(default_path="my_config.yaml")
opt = loader.load()

# Override specific values
user_opt = {
    'model': 'gpt-4-turbo',
    'if_add_node_summary': 'no'
}
opt = loader.load(user_opt)
```

### Handling Large Documents

For documents exceeding context limits:

```python
# Strategy 1: Reduce node size
result = page_index(
    doc="large_document.pdf",
    max_page_num_each_node=8,  # Smaller nodes
    max_token_num_each_node=15000  # Lower token limit
)

# Strategy 2: Disable text inclusion
result = page_index(
    doc="large_document.pdf",
    if_add_node_text="no",  # Don't include full text
    if_add_node_summary="yes"  # Use summaries instead
)

# Strategy 3: Process sections independently
# (Manual approach)
from pageindex.utils import get_page_tokens

pages = get_page_tokens("large_document.pdf")
section1_pages = pages[0:100]
section2_pages = pages[100:200]
# Process each section separately
```

### Logging and Debugging

PageIndex includes built-in logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run PageIndex
result = page_index(doc="document.pdf")

# Check logs for:
# - TOC detection results
# - Verification accuracy
# - API call failures
# - Processing decisions
```

Check the generated log file:

```bash
# Logs are saved in JSON format
cat logs/document_pdf_TIMESTAMP.json | jq '.'
```

### Error Handling

Common issues and solutions:

```python
from pageindex import page_index

try:
    result = page_index(doc="document.pdf")
except ValueError as e:
    # Invalid input (wrong file type, missing file)
    print(f"Input error: {e}")
except Exception as e:
    # API errors, processing failures
    print(f"Processing error: {e}")
    # Check logs for details
```

**Common Errors:**

1. **API Rate Limits**

   - Solution: Add delays between calls
   - Use exponential backoff (built-in)

2. **Context Length Exceeded**

   - Solution: Reduce max_token_num_each_node
   - Enable node splitting

3. **TOC Detection Failure**

   - Solution: Manually process without TOC
   - Check toc_check_page_num setting

4. **Poor Verification Accuracy**
   - Often due to complex document structure
   - System automatically falls back to no-TOC mode

---

## Best Practices

### 1. Choose the Right Model

```python
# For accuracy (slower, more expensive)
result = page_index(doc="document.pdf", model="gpt-4o-2024-11-20")

# For speed (faster, cheaper, less accurate)
result = page_index(doc="document.pdf", model="gpt-4o-mini")
```

**Recommendation:**

- Use `gpt-4o-2024-11-20` for production
- Use `gpt-4o-mini` for development/testing

### 2. Optimize Token Usage

```python
# Minimize tokens in output
result = page_index(
    doc="document.pdf",
    if_add_node_text="no",  # Save tokens
    if_add_node_summary="yes",  # Concise summaries only
    if_add_doc_description="no"  # Skip if not needed
)
```

### 3. Batch Processing

```python
import os
from pageindex import page_index

pdf_dir = "documents/"
output_dir = "results/"

for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        try:
            result = page_index(
                doc=os.path.join(pdf_dir, filename),
                model="gpt-4o-2024-11-20"
            )

            output_file = os.path.join(
                output_dir,
                filename.replace(".pdf", "_structure.json")
            )

            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"✓ Processed {filename}")

        except Exception as e:
            print(f"✗ Failed {filename}: {e}")
```

### 4. Validate Results

```python
def validate_structure(structure):
    """
    Validates generated tree structure
    """
    for node in structure:
        # Check required fields
        assert 'title' in node
        assert 'start_index' in node
        assert 'end_index' in node

        # Check index ordering
        assert node['start_index'] <= node['end_index']

        # Recursively validate children
        if 'nodes' in node and node['nodes']:
            validate_structure(node['nodes'])

            # Check child indices within parent range
            for child in node['nodes']:
                assert child['start_index'] >= node['start_index']
                assert child['end_index'] <= node['end_index']

# Use validation
result = page_index(doc="document.pdf")
try:
    validate_structure(result['structure'])
    print("✓ Structure is valid")
except AssertionError as e:
    print(f"✗ Structure validation failed: {e}")
```

### 5. Caching Results

```python
import json
import hashlib
import os

def get_file_hash(filepath):
    """Generate hash of file for caching"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def process_with_cache(pdf_path, cache_dir="cache"):
    """
    Process PDF with caching
    """
    # Check cache
    file_hash = get_file_hash(pdf_path)
    cache_file = os.path.join(cache_dir, f"{file_hash}.json")

    if os.path.exists(cache_file):
        print("Using cached result")
        with open(cache_file, 'r') as f:
            return json.load(f)

    # Process document
    print("Processing document...")
    result = page_index(doc=pdf_path)

    # Save to cache
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(result, f, indent=2)

    return result
```

### 6. Monitor Costs

```python
from pageindex.utils import count_tokens

def estimate_cost(pdf_path, model="gpt-4o-2024-11-20"):
    """
    Estimates processing cost
    """
    from pageindex.utils import get_page_tokens

    pages = get_page_tokens(pdf_path, model=model)
    total_tokens = sum(token_count for _, token_count in pages)

    # Rough estimate (actual usage varies)
    # TOC extraction: ~2x document tokens
    # Verification: ~1x per sample
    # Summary generation: ~1.5x per node

    estimated_input_tokens = total_tokens * 4
    estimated_output_tokens = total_tokens * 0.2

    # GPT-4o pricing (as of 2024)
    input_cost = (estimated_input_tokens / 1_000_000) * 2.50
    output_cost = (estimated_output_tokens / 1_000_000) * 10.00

    print(f"Estimated input tokens: {estimated_input_tokens:,}")
    print(f"Estimated output tokens: {estimated_output_tokens:,}")
    print(f"Estimated cost: ${input_cost + output_cost:.2f}")

    return input_cost + output_cost

# Check cost before processing
estimate_cost("large_document.pdf")
```

---

## Summary

You now have a comprehensive understanding of PageIndex:

1. **Architecture**: How documents flow through the system
2. **Core modules**: Utils, page_index, page_index_md
3. **Key algorithms**: TOC detection, verification, tree building
4. **Practical usage**: CLI, library, batch processing
5. **Best practices**: Optimization, validation, caching

### Next Steps

- Explore the [cookbook](../cookbook/) for practical examples
- Read the [tutorials](../tutorials/) for advanced techniques
- Check the [API documentation](https://docs.pageindex.ai/quickstart) for cloud service
- Join the [Discord community](https://discord.com/invite/VuXuf29EUj) for support

### Additional Resources

- **Paper**: [Understanding PageIndex's Approach](https://vectify.ai/blog/Mafin2.5)
- **Benchmark**: [FinanceBench Results](https://github.com/VectifyAI/Mafin2.5-FinanceBench)
- **MCP Integration**: [PageIndex MCP Server](https://github.com/VectifyAI/pageindex-mcp)

---

**Happy coding!** If you have questions or feedback, please open an issue on GitHub or reach out on Discord.
