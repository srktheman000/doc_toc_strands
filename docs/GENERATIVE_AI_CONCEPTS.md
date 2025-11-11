# Generative AI Concepts in PageIndex

## Table of Contents

1. [Introduction to Generative AI in PageIndex](#introduction)
2. [Understanding LLM-Based Document Processing](#llm-based-processing)
3. [Prompt Engineering in PageIndex](#prompt-engineering)
4. [Reasoning vs Similarity](#reasoning-vs-similarity)
5. [Async Processing & Parallelization](#async-processing)
6. [Token Management](#token-management)
7. [Error Handling & Robustness](#error-handling)
8. [Real-World Examples](#real-world-examples)
9. [Tips for Generative AI Developers](#tips-for-developers)

---

## Introduction to Generative AI in PageIndex

### What Makes PageIndex Different?

Traditional RAG systems use **vector embeddings** to find similar text chunks. PageIndex uses **LLM reasoning** to understand document structure and navigate intelligently.

**Traditional Vector-Based RAG:**

```
Query: "What was the revenue in Q4?"
↓
[Convert to embedding vector]
↓
[Find similar text chunks via cosine similarity]
↓
[Return most similar chunks]
```

**PageIndex Reasoning-Based RAG:**

```
Query: "What was the revenue in Q4?"
↓
[LLM reads table of contents]
↓
[LLM reasons: "Q4 data is likely in 'Quarterly Results' section"]
↓
[Navigate to that section in tree]
↓
[LLM searches within section for revenue data]
↓
[Return relevant content with context]
```

### Key Insight: Humans Don't Use Vector Search

When you read a financial report looking for Q4 revenue, you:

1. Check the table of contents
2. Navigate to "Financial Results" or similar section
3. Look for Q4 subsection
4. Find the revenue figure

PageIndex mimics this human reasoning process!

---

## Understanding LLM-Based Document Processing

### The Power of LLMs for Structure Understanding

PageIndex leverages several LLM capabilities:

#### 1. Pattern Recognition

```python
# LLM can identify if text is a table of contents
prompt = """
Your job is to detect if there is a table of content provided in the given text.

Given text: {content}

Return:
{
    "toc_detected": "yes" or "no"
}
"""
```

**Why this works:**

- LLMs are trained on millions of documents
- They recognize TOC patterns: indentation, numbering, page numbers
- They distinguish TOCs from abstracts, figure lists, etc.

#### 2. Structural Understanding

```python
# LLM can parse hierarchical structure
prompt = """
Transform this table of contents into JSON format with hierarchy.

TOC:
1. Introduction
   1.1 Background
   1.2 Motivation
2. Methods

Output format:
[
    {
        "structure": "1",
        "title": "Introduction",
        "nodes": [
            {"structure": "1.1", "title": "Background"},
            {"structure": "1.2", "title": "Motivation"}
        ]
    },
    ...
]
"""
```

**Why this works:**

- LLMs understand nested structures
- They recognize numbering systems (1.1, 1.2, etc.)
- They maintain parent-child relationships

#### 3. Semantic Matching

```python
# LLM can verify if a section title appears on a page
prompt = """
Check if the section "{title}" appears or starts in this page:

{page_text}

Answer:
{
    "thinking": "explain your reasoning",
    "answer": "yes" or "no"
}
"""
```

**Why this works:**

- LLMs do fuzzy matching (handle typos, spacing)
- They understand synonyms and variations
- They consider context (not just exact string match)

---

## Prompt Engineering in PageIndex

PageIndex uses carefully crafted prompts for reliability.

### Anatomy of a Good Prompt

**Example: TOC Transformation Prompt**

```python
prompt = """
You are an expert in extracting hierarchical tree structure,
your task is to generate the tree structure of the document.

The structure variable is the numeric system which represents
the index of the hierarchy section. For example:
- First section: structure index 1
- First subsection: structure index 1.1
- Second subsection: structure index 1.2

For the title, extract the original title from the text,
only fix space inconsistency.

The provided text contains tags like <physical_index_X> to
indicate page X.

Response format:
[
    {
        "structure": "x.x.x" (string),
        "title": "exact title from text",
        "physical_index": "<physical_index_X>"
    },
    ...
]

Directly return the final JSON structure. Do not output anything else.
"""
```

**Prompt Components:**

1. **Role Definition**: "You are an expert in..."

   - Sets context for the LLM
   - Activates relevant training data

2. **Clear Task**: "your task is to..."

   - Unambiguous instruction
   - No room for misinterpretation

3. **Examples**: "For example: ..."

   - Shows desired format
   - Clarifies edge cases

4. **Format Specification**: "Response format: ..."

   - Ensures consistent output
   - Makes parsing reliable

5. **Constraints**: "Directly return... Do not output anything else"
   - Prevents unwanted explanations
   - Improves parsability

### Handling Incomplete Responses

LLMs have output token limits. PageIndex handles this:

```python
def toc_transformer(toc_content, model=None):
    # Initial prompt
    prompt = "Transform this TOC to JSON: " + toc_content

    # Get response and check if complete
    response, finish_reason = ChatGPT_API_with_finish_reason(model, prompt)

    # If incomplete (hit token limit)
    if finish_reason != "finished":
        # Continue generation
        chat_history = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response}
        ]

        continuation_prompt = "Please continue the JSON structure"
        new_response, finish_reason = ChatGPT_API_with_finish_reason(
            model, continuation_prompt, chat_history=chat_history
        )

        # Append to previous response
        response = response + new_response

    return extract_json(response)
```

**Key Techniques:**

- Check `finish_reason` to detect truncation
- Use chat history to maintain context
- Iteratively continue until complete
- Validate completeness with LLM

### Temperature = 0 for Consistency

```python
response = client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=0,  # Deterministic output
)
```

**Why temperature=0?**

- **Consistency**: Same input → same output
- **Reliability**: Predictable behavior in production
- **Parsability**: Fewer format variations

**When to use higher temperature:**

- Creative tasks (summary generation could use 0.3-0.5)
- Multiple valid outputs
- Brainstorming/exploration

---

## Reasoning vs Similarity

### The Fundamental Difference

**Vector Similarity (Traditional RAG):**

```python
# Embedding-based search
query = "What was Q4 revenue?"
query_embedding = embed(query)

# Find similar chunks
for chunk in document_chunks:
    chunk_embedding = embed(chunk)
    similarity = cosine_similarity(query_embedding, chunk_embedding)

# Return top-k most similar
```

**Problems:**

- May return text about "Q4 costs" (semantically similar)
- May miss "fourth quarter income" (different phrasing)
- No understanding of document structure

**Reasoning-Based (PageIndex):**

```python
# LLM-based navigation
query = "What was Q4 revenue?"

# Step 1: Understand query intent
understanding = llm_analyze("""
What section of an annual report would contain Q4 revenue?

Query: {query}
""")
# Response: "Financial Results" or "Quarterly Performance"

# Step 2: Navigate tree structure
relevant_sections = search_tree(
    structure=document_tree,
    target_sections=understanding
)

# Step 3: Extract from relevant sections
answer = llm_extract("""
From this section, find Q4 revenue:

{relevant_sections}

Query: {query}
""")
```

**Advantages:**

- Understands document organization
- Reasons about where information should be
- Maintains context across sections
- Can handle multi-hop reasoning

### Example: Multi-Hop Reasoning

**Query**: "How did Q4 revenue compare to Q3?"

**Vector-based approach:**

- Finds Q4 revenue mention → returns chunk
- Finds Q3 revenue mention → returns chunk
- User must manually compare

**PageIndex approach:**

1. Navigate to "Quarterly Results" section
2. Understand this section contains all quarters
3. Extract both Q3 and Q4 revenue
4. Reason about the comparison
5. Return comprehensive answer with context

---

## Async Processing & Parallelization

### Why Async Matters for LLM Applications

**Synchronous Processing (Slow):**

```python
summaries = []
for node in nodes:  # 50 nodes
    summary = generate_summary(node)  # 2 seconds each
    summaries.append(summary)
# Total time: 50 * 2 = 100 seconds
```

**Asynchronous Processing (Fast):**

```python
tasks = [generate_summary_async(node) for node in nodes]
summaries = await asyncio.gather(*tasks)
# Total time: ~2-5 seconds (parallel API calls)
```

### Implementing Async in PageIndex

**1. Async API Wrapper:**

```python
import asyncio
import openai

async def ChatGPT_API_async(model, prompt, api_key=None):
    """Async version of ChatGPT API call"""
    max_retries = 10
    messages = [{"role": "user", "content": prompt}]

    for i in range(max_retries):
        try:
            async with openai.AsyncOpenAI(api_key=api_key) as client:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0,
                )
                return response.choices[0].message.content
        except Exception as e:
            if i < max_retries - 1:
                await asyncio.sleep(1)  # Exponential backoff
            else:
                raise
```

**2. Parallel Summary Generation:**

```python
async def generate_summaries_for_structure(structure, model=None):
    """Generate summaries for all nodes in parallel"""

    # Flatten tree to list
    nodes = structure_to_list(structure)

    # Create async task for each node
    tasks = [
        generate_node_summary(node, model=model)
        for node in nodes
    ]

    # Execute all tasks concurrently
    summaries = await asyncio.gather(*tasks)

    # Assign summaries back to nodes
    for node, summary in zip(nodes, summaries):
        node['summary'] = summary

    return structure
```

**3. Verification in Parallel:**

```python
async def verify_toc(page_list, list_result, model=None):
    """Verify multiple TOC entries concurrently"""

    # Prepare tasks
    tasks = [
        check_title_appearance(item, page_list, model)
        for item in list_result
    ]

    # Run all verifications in parallel
    results = await asyncio.gather(*tasks)

    # Process results
    correct_count = sum(1 for r in results if r['answer'] == 'yes')
    accuracy = correct_count / len(results)

    return accuracy, results
```

### Best Practices for Async LLM Calls

**1. Rate Limiting:**

```python
import asyncio
from asyncio import Semaphore

async def rate_limited_llm_call(prompt, semaphore, model):
    """Limit concurrent API calls"""
    async with semaphore:  # Max N concurrent calls
        result = await ChatGPT_API_async(model, prompt)
        await asyncio.sleep(0.1)  # Small delay between calls
        return result

# Use in practice
semaphore = Semaphore(10)  # Max 10 concurrent calls
tasks = [
    rate_limited_llm_call(prompt, semaphore, model)
    for prompt in prompts
]
results = await asyncio.gather(*tasks)
```

**2. Error Handling:**

```python
async def safe_llm_call(prompt, model):
    """LLM call with error handling"""
    try:
        return await ChatGPT_API_async(model, prompt)
    except Exception as e:
        print(f"Error: {e}")
        return None

# Use with gather and return_exceptions
results = await asyncio.gather(
    *tasks,
    return_exceptions=True  # Don't fail entire batch
)

# Filter out errors
valid_results = [r for r in results if not isinstance(r, Exception)]
```

**3. Progress Tracking:**

```python
from tqdm.asyncio import tqdm

async def process_with_progress(nodes, model):
    """Show progress bar for async operations"""
    tasks = [
        generate_summary(node, model)
        for node in nodes
    ]

    results = []
    for coro in tqdm.as_completed(tasks, total=len(tasks)):
        result = await coro
        results.append(result)

    return results
```

---

## Token Management

### Understanding Tokens

**What are tokens?**

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o-2024-11-20")

text = "Hello, world!"
tokens = enc.encode(text)
print(tokens)  # [9906, 11, 1917, 0]
print(len(tokens))  # 4 tokens

# Roughly: 1 token ≈ 4 characters in English
```

**Why tokens matter:**

1. **Context Limits**: Models have max token limits (e.g., 128k)
2. **Cost**: Pricing is per token
3. **Processing Time**: More tokens = slower responses

### Token Counting in PageIndex

```python
def count_tokens(text, model=None):
    """Count tokens in text"""
    if not text:
        return 0
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    return len(tokens)

# Used throughout PageIndex
page_tokens = count_tokens(page_text, model="gpt-4o-2024-11-20")
```

### Token Budget Strategies

**1. Node Size Management:**

```python
# Ensure nodes fit in context window
def process_large_node_recursively(node, page_list, opt):
    """Subdivide nodes exceeding token limit"""

    node_text = get_text_of_pdf_pages(
        page_list,
        node['start_index'],
        node['end_index']
    )
    token_num = count_tokens(node_text, model=opt.model)

    # Check limits
    if (node['end_index'] - node['start_index'] > opt.max_page_num_each_node
        and token_num >= opt.max_token_num_each_node):

        # Generate sub-structure
        sub_structure = await meta_processor(
            node_page_list,
            mode='process_no_toc',
            start_index=node['start_index'],
            opt=opt
        )

        # Attach as child nodes
        node['nodes'] = sub_structure
```

**2. Summary Generation:**

```python
async def get_node_summary(node, summary_token_threshold=200, model=None):
    """Generate summary only if node is large"""

    node_text = node.get('text')
    num_tokens = count_tokens(node_text, model=model)

    if num_tokens < summary_token_threshold:
        # Small node - use original text
        return node_text
    else:
        # Large node - generate summary
        return await generate_node_summary(node, model=model)
```

**3. Grouping Pages:**

```python
def page_list_to_group_text(page_contents, token_lengths, max_tokens=20000):
    """Group pages to stay within token limit"""

    num_tokens = sum(token_lengths)

    if num_tokens <= max_tokens:
        # All pages fit in one group
        return [''.join(page_contents)]

    # Split into groups
    groups = []
    current_group = []
    current_tokens = 0

    for page_content, page_tokens in zip(page_contents, token_lengths):
        if current_tokens + page_tokens > max_tokens:
            # Start new group
            groups.append(''.join(current_group))
            current_group = [page_content]
            current_tokens = page_tokens
        else:
            # Add to current group
            current_group.append(page_content)
            current_tokens += page_tokens

    # Add last group
    if current_group:
        groups.append(''.join(current_group))

    return groups
```

### Cost Optimization

**Estimate costs before processing:**

```python
def estimate_processing_cost(pdf_path, model="gpt-4o-2024-11-20"):
    """Estimate API cost for processing a document"""

    pages = get_page_tokens(pdf_path, model=model)
    total_tokens = sum(token_count for _, token_count in pages)

    # Rough estimates
    # TOC extraction: ~2x document size
    # Verification: ~1x per sample (sample 20%)
    # Summary generation: ~1.5x per node (~50 nodes avg)

    estimated_input = total_tokens * 4
    estimated_output = total_tokens * 0.2

    # GPT-4o pricing (example, check current rates)
    input_cost = (estimated_input / 1_000_000) * 2.50  # $2.50 per 1M tokens
    output_cost = (estimated_output / 1_000_000) * 10.00  # $10 per 1M tokens

    total_cost = input_cost + output_cost

    print(f"Document: {total_tokens:,} tokens")
    print(f"Estimated input: {estimated_input:,} tokens")
    print(f"Estimated output: {estimated_output:,} tokens")
    print(f"Estimated cost: ${total_cost:.2f}")

    return total_cost

# Check before processing
if estimate_processing_cost("large_report.pdf") > 5.00:
    print("Warning: Processing will cost more than $5")
    proceed = input("Continue? (y/n): ")
    if proceed.lower() != 'y':
        exit()
```

---

## Error Handling & Robustness

### Retry Logic

```python
def ChatGPT_API(model, prompt, api_key=None):
    """API call with automatic retry"""
    max_retries = 10
    client = openai.OpenAI(api_key=api_key)

    for i in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return response.choices[0].message.content

        except openai.RateLimitError as e:
            # Rate limit - wait and retry
            wait_time = 2 ** i  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)

        except openai.APIError as e:
            # API error - retry
            print(f"API error: {e}. Retrying...")
            time.sleep(1)

        except Exception as e:
            # Unknown error
            print(f"Error: {e}")
            if i == max_retries - 1:
                raise  # Give up after max retries
            time.sleep(1)
```

### JSON Parsing Robustness

````python
def extract_json(content):
    """Robustly extract JSON from LLM response"""
    try:
        # Remove markdown code blocks
        start_idx = content.find("```json")
        if start_idx != -1:
            start_idx += 7
            end_idx = content.rfind("```")
            json_content = content[start_idx:end_idx].strip()
        else:
            json_content = content.strip()

        # Clean up common issues
        json_content = json_content.replace('None', 'null')  # Python → JSON
        json_content = json_content.replace('\n', ' ')  # Remove newlines
        json_content = ' '.join(json_content.split())  # Normalize whitespace

        # Parse
        return json.loads(json_content)

    except json.JSONDecodeError as e:
        # Try fixing common issues
        try:
            # Remove trailing commas
            json_content = json_content.replace(',]', ']')
            json_content = json_content.replace(',}', '}')
            return json.loads(json_content)
        except:
            print(f"JSON parsing failed: {e}")
            return {}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}
````

### Validation & Fallback

```python
async def meta_processor(page_list, mode=None, opt=None):
    """Process with validation and fallback"""

    # Try primary method
    if mode == 'process_toc_with_page_numbers':
        result = process_toc_with_page_numbers(...)
        accuracy, incorrect = await verify_toc(page_list, result, opt.model)

        if accuracy == 1.0:
            # Perfect - use as-is
            return result

        elif accuracy > 0.6:
            # Good - fix incorrect entries
            result, incorrect = await fix_incorrect_toc(...)
            return result

        else:
            # Poor - fallback to next method
            print("Accuracy too low, trying without page numbers...")
            return await meta_processor(
                page_list,
                mode='process_toc_no_page_numbers',
                opt=opt
            )

    # Try secondary method
    elif mode == 'process_toc_no_page_numbers':
        result = process_toc_no_page_numbers(...)
        accuracy, incorrect = await verify_toc(page_list, result, opt.model)

        if accuracy > 0.6:
            return result
        else:
            # Fallback to last resort
            print("Falling back to no-TOC processing...")
            return await meta_processor(
                page_list,
                mode='process_no_toc',
                opt=opt
            )

    # Last resort - generate structure from scratch
    else:
        return process_no_toc(page_list, opt=opt)
```

---

## Real-World Examples

### Example 1: Processing Financial Report

```python
from pageindex import page_index

# Process annual report
result = page_index(
    doc="2023-annual-report.pdf",
    model="gpt-4o-2024-11-20",
    if_add_node_summary="yes",
    if_add_doc_description="yes"
)

# Navigate structure
for section in result['structure']:
    if 'financial' in section['title'].lower():
        print(f"\n{section['title']}")
        print(f"Pages: {section['start_index']}-{section['end_index']}")
        print(f"Summary: {section['summary']}")

        # Check subsections
        for subsection in section.get('nodes', []):
            if 'revenue' in subsection['title'].lower():
                print(f"  → {subsection['title']}")
                print(f"     Summary: {subsection['summary']}")
```

### Example 2: Batch Processing Research Papers

```python
import os
import json
from pageindex import page_index

papers_dir = "research_papers/"
output_dir = "processed_papers/"

for filename in os.listdir(papers_dir):
    if not filename.endswith('.pdf'):
        continue

    print(f"Processing {filename}...")

    try:
        result = page_index(
            doc=os.path.join(papers_dir, filename),
            model="gpt-4o-2024-11-20",
            if_add_node_summary="yes"
        )

        # Extract key information
        abstract = None
        methods = None
        results = None

        for section in result['structure']:
            title_lower = section['title'].lower()

            if 'abstract' in title_lower:
                abstract = section.get('summary', section.get('text', ''))
            elif 'method' in title_lower:
                methods = section.get('summary', section.get('text', ''))
            elif 'result' in title_lower:
                results = section.get('summary', section.get('text', ''))

        # Save summary
        summary = {
            'filename': filename,
            'doc_description': result.get('doc_description', ''),
            'abstract': abstract,
            'methods': methods,
            'results': results,
            'full_structure': result['structure']
        }

        output_file = os.path.join(
            output_dir,
            filename.replace('.pdf', '_summary.json')
        )

        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved to {output_file}")

    except Exception as e:
        print(f"✗ Failed: {e}")
```

### Example 3: Building a RAG System

```python
from pageindex import page_index
import openai

class PageIndexRAG:
    def __init__(self, pdf_path, model="gpt-4o-2024-11-20"):
        """Initialize RAG system with PageIndex"""
        self.model = model

        # Generate tree structure
        print("Building document index...")
        self.doc_structure = page_index(
            doc=pdf_path,
            model=model,
            if_add_node_summary="yes",
            if_add_node_text="yes"  # Include full text for retrieval
        )

        print(f"✓ Indexed {self.doc_structure['doc_name']}")

    def search_tree(self, query, structure=None):
        """Search tree structure using LLM reasoning"""
        if structure is None:
            structure = self.doc_structure['structure']

        # Build structure representation
        structure_str = self._format_structure(structure)

        # Ask LLM to identify relevant sections
        prompt = f"""
Given this document structure and a query, identify the most relevant sections.

Document structure:
{structure_str}

Query: {query}

Return JSON:
{{
    "thinking": "explain which sections are relevant and why",
    "relevant_node_ids": ["0001", "0005", ...]
}}
"""

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        result = json.loads(response.choices[0].message.content)
        return result['relevant_node_ids']

    def retrieve(self, query):
        """Retrieve relevant content for query"""
        # Find relevant sections
        relevant_ids = self.search_tree(query)

        # Extract text from relevant nodes
        relevant_texts = []
        for node in self._flatten_structure(self.doc_structure['structure']):
            if node['node_id'] in relevant_ids:
                relevant_texts.append({
                    'title': node['title'],
                    'text': node.get('text', ''),
                    'summary': node.get('summary', ''),
                    'pages': f"{node['start_index']}-{node['end_index']}"
                })

        return relevant_texts

    def answer(self, query):
        """Answer query using retrieved content"""
        # Retrieve relevant content
        context = self.retrieve(query)

        # Build context string
        context_str = "\n\n".join([
            f"Section: {c['title']} (Pages {c['pages']})\n{c['text']}"
            for c in context
        ])

        # Generate answer
        prompt = f"""
Answer the query based on the following document sections.

Context:
{context_str}

Query: {query}

Provide a detailed answer with specific references to page numbers.
"""

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return response.choices[0].message.content

    def _format_structure(self, structure, indent=0):
        """Format structure for LLM consumption"""
        result = []
        for node in structure:
            result.append(
                "  " * indent +
                f"[{node['node_id']}] {node['title']} " +
                f"(Pages {node['start_index']}-{node['end_index']})"
            )
            if 'summary' in node:
                result.append("  " * (indent + 1) + f"Summary: {node['summary']}")

            if node.get('nodes'):
                result.append(self._format_structure(node['nodes'], indent + 1))

        return "\n".join(result)

    def _flatten_structure(self, structure):
        """Flatten tree to list"""
        nodes = []
        for item in structure:
            nodes.append(item)
            if item.get('nodes'):
                nodes.extend(self._flatten_structure(item['nodes']))
        return nodes

# Usage
rag = PageIndexRAG("financial-report.pdf")

# Query the document
question = "What was the total revenue in Q4 2023?"
answer = rag.answer(question)
print(answer)
```

---

## Tips for Generative AI Developers

### 1. Prompt Design Best Practices

✅ **DO:**

- Be specific and clear
- Provide examples
- Specify output format explicitly
- Use consistent terminology
- Add constraints ("Do not output anything else")

❌ **DON'T:**

- Be vague or ambiguous
- Mix multiple tasks in one prompt
- Assume model knows your format
- Use inconsistent instructions

### 2. Handling Model Limitations

**Context Window:**

```python
# Check if content fits in context
max_context = 128000  # GPT-4o limit
current_tokens = count_tokens(prompt + content)

if current_tokens > max_context * 0.8:  # Leave 20% margin
    # Split content
    content_parts = split_into_chunks(content, max_chunk_size=100000)
    results = []
    for part in content_parts:
        result = process_part(part)
        results.append(result)
    # Combine results
```

**Rate Limits:**

```python
# Implement exponential backoff
import time

def call_with_backoff(func, *args, max_retries=5):
    for i in range(max_retries):
        try:
            return func(*args)
        except RateLimitError:
            wait_time = 2 ** i
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

### 3. Testing & Validation

```python
def validate_llm_output(response, expected_format):
    """Validate LLM response matches expected format"""

    # Check for required fields
    if isinstance(expected_format, dict):
        for key in expected_format.keys():
            if key not in response:
                raise ValueError(f"Missing required field: {key}")

            # Recursively validate nested structures
            if isinstance(expected_format[key], dict):
                validate_llm_output(response[key], expected_format[key])

    elif isinstance(expected_format, list):
        if not isinstance(response, list):
            raise ValueError("Expected list")

        # Validate each item
        for item in response:
            validate_llm_output(item, expected_format[0])

# Use in practice
expected = {
    "structure": str,
    "title": str,
    "physical_index": int
}

response = extract_json(llm_response)
try:
    validate_llm_output(response, expected)
    print("✓ Valid response")
except ValueError as e:
    print(f"✗ Invalid response: {e}")
```

### 4. Monitoring & Debugging

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log prompts and responses
def logged_llm_call(model, prompt):
    logging.info(f"Prompt: {prompt[:100]}...")  # Log first 100 chars

    response = ChatGPT_API(model, prompt)

    logging.info(f"Response: {response[:100]}...")
    logging.info(f"Tokens: ~{count_tokens(prompt + response)}")

    return response
```

### 5. Cost Management

```python
class CostTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0

    def track_call(self, prompt, response, model):
        input_tokens = count_tokens(prompt, model)
        output_tokens = count_tokens(response, model)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_calls += 1

    def get_cost(self, model="gpt-4o-2024-11-20"):
        # Pricing (check current rates)
        input_cost_per_million = 2.50
        output_cost_per_million = 10.00

        input_cost = (self.total_input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (self.total_output_tokens / 1_000_000) * output_cost_per_million

        return {
            'total_cost': input_cost + output_cost,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_calls': self.total_calls,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens
        }

# Usage
tracker = CostTracker()

def tracked_llm_call(prompt, model):
    response = ChatGPT_API(model, prompt)
    tracker.track_call(prompt, response, model)
    return response

# After processing
cost_info = tracker.get_cost()
print(f"Total cost: ${cost_info['total_cost']:.2f}")
print(f"Total API calls: {cost_info['total_calls']}")
```

---

## Summary

Key takeaways for generative AI developers:

1. **Reasoning > Similarity**: Use LLMs for intelligent navigation, not just semantic matching

2. **Prompt Engineering**: Careful prompt design is crucial for reliable outputs

3. **Async is Essential**: Parallel processing dramatically speeds up LLM applications

4. **Token Management**: Always monitor and optimize token usage

5. **Robustness**: Implement retry logic, validation, and fallback strategies

6. **Testing**: Validate LLM outputs programmatically

7. **Cost Awareness**: Track and optimize API costs

### Next Steps

- Experiment with different prompts in `page_index.py`
- Try modifying temperature and sampling parameters
- Build your own RAG system using PageIndex
- Explore advanced tree search algorithms

### Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Tiktoken](https://github.com/openai/tiktoken)
- [Python Asyncio](https://docs.python.org/3/library/asyncio.html)
- [PageIndex GitHub](https://github.com/VectifyAI/PageIndex)

---

**Happy building!** Join our [Discord](https://discord.com/invite/VuXuf29EUj) to discuss generative AI techniques and share your projects.
