# PageIndex Architecture Overview

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐              ┌─────────────────┐              │
│  │   PDF File   │              │  Markdown File  │              │
│  └──────┬───────┘              └────────┬────────┘              │
│         │                               │                        │
│         └───────────────┬───────────────┘                        │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PARSING LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Text Extraction Module                       │   │
│  │  • PyPDF2 / PyMuPDF for PDF                              │   │
│  │  • Regex parsing for Markdown                            │   │
│  │  • Token counting (tiktoken)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TOC DETECTION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  Has TOC with   │    │  Has TOC only   │                     │
│  │  Page Numbers?  │    │  (no numbers)?  │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           ├──────────────────────┼──────────┐                    │
│           │                      │          │                    │
│           ▼                      ▼          ▼                    │
│      ┌─────────┐          ┌──────────┐ ┌────────┐               │
│      │ Mode 1  │          │  Mode 2  │ │ Mode 3 │               │
│      │TOC+Pages│          │ TOC only │ │ No TOC │               │
│      └────┬────┘          └─────┬────┘ └───┬────┘               │
│           │                     │           │                    │
└───────────┼─────────────────────┼───────────┼────────────────────┘
            │                     │           │
            └─────────┬───────────┴───────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STRUCTURE EXTRACTION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             LLM Processing Pipeline                       │   │
│  │                                                           │   │
│  │  1. TOC Transformation (list → JSON hierarchy)           │   │
│  │  2. Page Number Mapping (logical → physical)             │   │
│  │  3. Structure Generation (if no TOC)                     │   │
│  │  4. Physical Index Extraction                            │   │
│  │                                                           │   │
│  │  OpenAI API (gpt-4o) with retry logic                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  VERIFICATION & FIXING LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Verify TOC Accuracy (async parallel checks)             │   │
│  │  • Sample N entries                                       │   │
│  │  • Check title appearance on claimed page                │   │
│  │  • Calculate accuracy score                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Decision Point: Accuracy >= 0.6?                        │   │
│  │  • YES: Fix incorrect entries                            │   │
│  │  • NO: Fallback to next method                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TREE CONSTRUCTION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Build Hierarchical Tree                                  │   │
│  │  • Convert flat list to tree (based on structure index)  │   │
│  │  • Set start_index and end_index for each node           │   │
│  │  • Identify parent-child relationships                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Process Large Nodes (recursive subdivision)             │   │
│  │  • Check node size (pages & tokens)                      │   │
│  │  • If too large: subdivide                               │   │
│  │  • Generate sub-structure                                │   │
│  │  • Attach as child nodes                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Optional Enhancements (user configurable)               │   │
│  │                                                           │   │
│  │  • Add Node IDs (sequential, zero-padded)                │   │
│  │  • Add Full Text (extract from pages)                    │   │
│  │  • Generate Summaries (async parallel LLM calls)         │   │
│  │  • Generate Document Description                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              JSON Structure Output                        │   │
│  │  {                                                        │   │
│  │    "doc_name": "...",                                     │   │
│  │    "doc_description": "...",                              │   │
│  │    "structure": [...]                                     │   │
│  │  }                                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         run_pageindex.py                         │
│                       (CLI Entry Point)                          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │      Config Loading          │
              │  (config.yaml + CLI args)    │
              └──────────────┬───────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  page_index.py  │  │page_index_md.py │  │    utils.py     │
│  (PDF handling) │  │(MD handling)    │  │  (Utilities)    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                     │
         │  ┌─────────────────┼─────────────────────┤
         │  │                 │                     │
         │  │  ┌──────────────▼──────────────┐      │
         │  │  │   ChatGPT_API / Async       │◄─────┘
         │  │  │   (OpenAI API wrapper)      │
         │  │  └─────────────────────────────┘
         │  │
         │  │  ┌─────────────────────────────┐
         │  └─►│  Token Counting (tiktoken)  │
         │     └─────────────────────────────┘
         │
         │     ┌─────────────────────────────┐
         └────►│  PDF Parsing (PyPDF2/PyMuPDF)│
               └─────────────────────────────┘
```

---

## Processing Flow for PDF Documents

```
START
  │
  ▼
┌─────────────────────────┐
│ Load PDF & Extract Text │
│ • get_page_tokens()     │
│ • Count tokens per page │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Detect TOC Pages      │
│ • find_toc_pages()      │
│ • Check first N pages   │
└───────────┬─────────────┘
            │
            ▼
      ┌─────────┐
      │ Has TOC? │
      └────┬─────┘
           │
    ┌──────┴──────┐
    │             │
   YES            NO
    │             │
    ▼             ▼
┌────────────┐  ┌──────────────────┐
│Extract TOC │  │ Generate Structure│
│& Check for │  │ from Document Text│
│Page Numbers│  │ • generate_toc_  │
└─────┬──────┘  │   init()         │
      │         └──────────┬────────┘
      ▼                    │
┌──────────────┐           │
│Has Page Nums?│           │
└──────┬───────┘           │
       │                   │
  ┌────┴────┐              │
  │         │              │
 YES        NO             │
  │         │              │
  ▼         ▼              │
┌─────┐ ┌─────────┐        │
│Mode │ │ Mode 2  │        │
│ 1   │ │ TOC no  │        │
│     │ │ numbers │        │
└──┬──┘ └────┬────┘        │
   │         │             │
   │    ┌────┴─────────────┘
   │    │
   ▼    ▼
┌──────────────────────┐
│  Transform TOC to    │
│  JSON Structure      │
│  • toc_transformer() │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Map Page Numbers    │
│  to Physical Indices │
│  • calculate_page_   │
│    offset()          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Verify Accuracy    │
│   • verify_toc()     │
│   • async parallel   │
└──────────┬───────────┘
           │
           ▼
      ┌────────────┐
      │Accuracy OK?│
      └─────┬──────┘
            │
      ┌─────┴─────┐
      │           │
     YES          NO
      │           │
      │           ▼
      │    ┌──────────────┐
      │    │Fix Incorrect │
      │    │or Fallback   │
      │    └──────┬───────┘
      │           │
      └───────┬───┘
              │
              ▼
┌──────────────────────────┐
│  Build Tree Structure    │
│  • list_to_tree()        │
│  • post_processing()     │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Process Large Nodes     │
│  (recursive subdivision) │
│  • Parallel processing   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Add Enhancements        │
│  • Node IDs              │
│  • Summaries (async)     │
│  • Text content          │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Save JSON Output        │
└──────────────────────────┘
           │
           ▼
          END
```

---

## Data Flow: Flat List to Tree

```
FLAT LIST (from TOC)
┌─────────────────────────────────────┐
│ [                                   │
│   {structure: "1", title: "Intro"}, │
│   {structure: "1.1", title: "..."},│
│   {structure: "1.2", title: "..."},│
│   {structure: "2", title: "Body"},  │
│   {structure: "2.1", title: "..."},│
│ ]                                   │
└─────────────────────────────────────┘
              │
              ▼ list_to_tree()
TREE STRUCTURE
┌─────────────────────────────────────┐
│ [                                   │
│   {                                 │
│     structure: "1",                 │
│     title: "Intro",                 │
│     nodes: [                        │
│       {structure: "1.1", ...},      │
│       {structure: "1.2", ...}       │
│     ]                               │
│   },                                │
│   {                                 │
│     structure: "2",                 │
│     title: "Body",                  │
│     nodes: [                        │
│       {structure: "2.1", ...}       │
│     ]                               │
│   }                                 │
│ ]                                   │
└─────────────────────────────────────┘
              │
              ▼ post_processing()
ENRICHED TREE
┌─────────────────────────────────────┐
│ [                                   │
│   {                                 │
│     structure: "1",                 │
│     title: "Intro",                 │
│     start_index: 1,                 │
│     end_index: 10,                  │
│     nodes: [...]                    │
│   },                                │
│   ...                               │
│ ]                                   │
└─────────────────────────────────────┘
              │
              ▼ write_node_id()
FINAL OUTPUT
┌─────────────────────────────────────┐
│ {                                   │
│   doc_name: "document",             │
│   structure: [                      │
│     {                               │
│       title: "Intro",               │
│       node_id: "0001",              │
│       start_index: 1,               │
│       end_index: 10,                │
│       summary: "...",               │
│       nodes: [                      │
│         {                           │
│           node_id: "0002",          │
│           ...                       │
│         }                           │
│       ]                             │
│     }                               │
│   ]                                 │
│ }                                   │
└─────────────────────────────────────┘
```

---

## Async Processing Architecture

```
SEQUENTIAL (Slow)
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Node 1  │ -> │ Node 2  │ -> │ Node 3  │ -> ... -> End
│ 2 sec   │    │ 2 sec   │    │ 2 sec   │
└─────────┘    └─────────┘    └─────────┘
Total: 50 nodes × 2 sec = 100 seconds


PARALLEL (Fast)
┌─────────┐
│ Node 1  │
│ 2 sec   │
└─────────┘
┌─────────┐
│ Node 2  │
│ 2 sec   │
└─────────┘
┌─────────┐
│ Node 3  │ All execute concurrently
│ 2 sec   │
└─────────┘
┌─────────┐
│  ...    │
└─────────┘
┌─────────┐
│ Node 50 │
│ 2 sec   │
└─────────┘
Total: ~2-5 seconds (limited by API rate limits)


IMPLEMENTATION
┌──────────────────────────────────────┐
│  async def process_all_nodes():     │
│                                      │
│    # Create tasks                   │
│    tasks = [                         │
│      process_node_async(node)       │
│      for node in nodes              │
│    ]                                 │
│                                      │
│    # Execute concurrently           │
│    results = await asyncio.gather(  │
│      *tasks                          │
│    )                                 │
│                                      │
│    return results                    │
└──────────────────────────────────────┘
```

---

## Token Management Strategy

```
DOCUMENT (1000 pages, 500k tokens)
             │
             ▼
┌────────────────────────────┐
│  Split into Processable    │
│  Chunks                    │
│                            │
│  max_token_num_each_node   │
│  = 20,000 tokens           │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Node 1: Pages 1-40        │
│  (18,000 tokens)           │ ✓ Fits in context
└────────────────────────────┘
┌────────────────────────────┐
│  Node 2: Pages 41-80       │
│  (19,500 tokens)           │ ✓ Fits in context
└────────────────────────────┘
┌────────────────────────────┐
│  Node 3: Pages 81-150      │
│  (35,000 tokens)           │ ✗ Too large!
│                            │
│  ▼ Recursive subdivision   │
│                            │
│  ┌──────────────────────┐  │
│  │ Node 3.1: 81-110     │  │
│  │ (17,000 tokens) ✓    │  │
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ Node 3.2: 111-150    │  │
│  │ (18,000 tokens) ✓    │  │
│  └──────────────────────┘  │
└────────────────────────────┘
```

---

## Error Handling & Fallback Chain

```
┌──────────────────────────┐
│  Try: TOC with page nums │
└───────────┬──────────────┘
            │
            ▼
       ┌────────┐
       │Verify  │
       └───┬────┘
           │
     ┌─────┴─────┐
     │           │
  Success     Failure
     │        (accuracy < 0.6)
     │           │
     ▼           ▼
   Done   ┌───────────────────┐
          │ Fallback: TOC     │
          │ without page nums │
          └────────┬──────────┘
                   │
                   ▼
              ┌────────┐
              │Verify  │
              └───┬────┘
                  │
            ┌─────┴─────┐
            │           │
         Success    Failure
            │           │
            ▼           ▼
          Done   ┌───────────────┐
                 │ Fallback:     │
                 │ Generate from │
                 │ scratch       │
                 └───────┬───────┘
                         │
                         ▼
                       Done
                   (always succeeds)
```

---

## Key Design Patterns

### 1. Retry with Exponential Backoff

```python
for i in range(max_retries):
    try:
        return api_call()
    except RateLimitError:
        wait_time = 2 ** i  # 1s, 2s, 4s, 8s, ...
        time.sleep(wait_time)
```

### 2. Async Parallel Processing

```python
tasks = [async_func(item) for item in items]
results = await asyncio.gather(*tasks)
```

### 3. Validation & Fallback

```python
result = try_method_1()
if not validate(result):
    result = try_method_2()
    if not validate(result):
        result = try_method_3()  # Last resort
```

### 4. Recursive Subdivision

```python
def process_node(node):
    if node_too_large(node):
        sub_nodes = subdivide(node)
        for sub_node in sub_nodes:
            process_node(sub_node)  # Recursive
```

### 5. Tree Traversal

```python
def traverse(node, func):
    func(node)  # Process current
    if node.get('nodes'):
        for child in node['nodes']:
            traverse(child, func)  # Recurse
```

---

## Performance Characteristics

### Time Complexity

| Operation          | Complexity | Notes                            |
| ------------------ | ---------- | -------------------------------- |
| PDF Parsing        | O(n)       | n = number of pages              |
| TOC Detection      | O(k)       | k = pages checked (typically 20) |
| Structure Building | O(m)       | m = number of sections           |
| Verification       | O(s)       | s = sample size                  |
| Summary Generation | O(m)       | Parallelized                     |

### Space Complexity

| Component              | Space | Notes             |
| ---------------------- | ----- | ----------------- |
| Page Text Storage      | O(n)  | n = pages         |
| Tree Structure         | O(m)  | m = sections      |
| Summaries              | O(m)  | One per node      |
| Full Text (if enabled) | O(n)  | Can be very large |

### API Calls

| Operation            | Calls | Notes                   |
| -------------------- | ----- | ----------------------- |
| TOC Detection        | k     | k = pages checked       |
| Structure Extraction | 1-5   | Depends on size         |
| Verification         | s     | s = sample size (10-50) |
| Fixing               | f     | f = incorrect entries   |
| Summaries            | m     | m = nodes               |

**Typical Document (50 pages, 30 sections):**

- TOC Detection: ~20 calls
- Structure: ~3 calls
- Verification: ~30 calls
- Summaries: ~30 calls
- **Total: ~83 API calls**

---

## Configuration & Extensibility

### Configuration Hierarchy

```
1. Default (config.yaml)
       ↓
2. User Config (custom yaml)
       ↓
3. CLI Arguments
       ↓
4. Function Parameters
```

Later values override earlier ones.

### Extension Points

1. **Custom PDF Parser**: Replace `get_page_tokens()`
2. **Custom LLM**: Replace `ChatGPT_API()`
3. **Custom Verification**: Modify `verify_toc()`
4. **Custom Summary**: Replace `generate_node_summary()`

---

This architecture document provides a complete overview of how PageIndex works internally. Use it as a reference when:

- Understanding code flow
- Debugging issues
- Adding new features
- Optimizing performance
- Explaining the system to others

For detailed code-level documentation, see the [Developer Guide](DEVELOPER_GUIDE.md).
