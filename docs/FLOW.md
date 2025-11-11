# PageIndex System Flow Documentation

This document provides a comprehensive overview of how PageIndex processes documents from input to output. It focuses on the execution flow, decision trees, and processing pipeline.

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Entry Points](#entry-points)
3. [Main Processing Flow](#main-processing-flow)
4. [TOC Detection Flow](#toc-detection-flow)
5. [Processing Modes](#processing-modes)
6. [Tree Construction Flow](#tree-construction-flow)
7. [Verification and Fixing Flow](#verification-and-fixing-flow)
8. [Post-Processing Flow](#post-processing-flow)
9. [Data Flow Diagram](#data-flow-diagram)
10. [Key Decision Points](#key-decision-points)

---

## High-Level Overview

PageIndex transforms long PDF or Markdown documents into structured hierarchical trees. The system uses LLM-based reasoning to:

1. Detect and extract table of contents (TOC)
2. Generate hierarchical structure if no TOC exists
3. Verify the accuracy of the structure
4. Recursively break down large sections
5. Optionally add summaries and metadata

```
┌─────────────┐
│   PDF/MD    │
│  Document   │
└──────┬──────┘
       │
       v
┌──────────────────┐
│  Parse Document  │
│  Extract Pages   │
└──────┬───────────┘
       │
       v
┌──────────────────┐
│  Detect TOC      │
│  (first 20 pgs)  │
└──────┬───────────┘
       │
       ├──── TOC with page numbers ────┐
       │                               │
       ├──── TOC without page nums ────┤
       │                               │
       └──── No TOC ──────────────────┤
                                       │
                                       v
                            ┌──────────────────┐
                            │  Process Mode    │
                            │  Selection       │
                            └──────┬───────────┘
                                   │
                                   v
                            ┌──────────────────┐
                            │  Generate Tree   │
                            │  Structure       │
                            └──────┬───────────┘
                                   │
                                   v
                            ┌──────────────────┐
                            │  Verify & Fix    │
                            │  Accuracy        │
                            └──────┬───────────┘
                                   │
                                   v
                            ┌──────────────────┐
                            │  Post-Process    │
                            │  (IDs, Summary)  │
                            └──────┬───────────┘
                                   │
                                   v
                            ┌──────────────────┐
                            │  JSON Output     │
                            │  Tree Structure  │
                            └──────────────────┘
```

---

## Entry Points

### 1. CLI Entry Point (`run_pageindex.py`)

**Flow:**
```
User runs command
    │
    ├─> Parse CLI arguments
    │   └─> Validate file path and type
    │
    ├─> Load configuration (config.yaml + user args)
    │
    ├─> For PDF:
    │   └─> Call page_index_main(pdf_path, opt)
    │
    └─> For Markdown:
        └─> Call md_to_tree(md_path, opt)
```

**File:** `run_pageindex.py:7-133`

**Key Arguments:**
- `--pdf_path` or `--md_path`: Input file
- `--model`: LLM model (default: gpt-4o-2024-11-20)
- `--if-add-node-summary`: Add summaries (yes/no)
- `--if-add-node-id`: Add node IDs (yes/no)

### 2. Library Entry Point (`page_index()`)

**Flow:**
```python
from pageindex import page_index

result = page_index(
    doc="document.pdf",
    model="gpt-4o-2024-11-20",
    if_add_node_summary="yes"
)
```

**File:** `pageindex/page_index.py:1103-1112`

---

## Main Processing Flow

### Overview (PDF Processing)

**Function:** `page_index_main(doc, opt)` at `pageindex/page_index.py:1058-1101`

```
┌─────────────────────────────────────────────────────────────┐
│                    page_index_main()                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       v
              ┌────────────────┐
              │  Parse PDF     │
              │  get_page_     │
              │  tokens()      │
              └────────┬───────┘
                       │
                       v
              ┌────────────────┐
              │  tree_parser() │ <--- Main async orchestrator
              └────────┬───────┘
                       │
                       v
              ┌────────────────┐
              │  check_toc()   │
              └────────┬───────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        v                             v
   TOC Found                     No TOC Found
        │                             │
        v                             v
┌───────────────┐            ┌────────────────┐
│ meta_processor│            │ meta_processor │
│ (with TOC)    │            │ (no TOC)       │
└───────┬───────┘            └────────┬───────┘
        │                             │
        └──────────────┬──────────────┘
                       │
                       v
              ┌────────────────┐
              │  verify_toc()  │
              │  (async check) │
              └────────┬───────┘
                       │
              ┌────────┴────────┐
              │                 │
              v                 v
         Accuracy < 60%    Accuracy > 60%
              │                 │
              v                 v
         Try fallback      Fix errors
         mode                  │
              │                 │
              └────────┬────────┘
                       │
                       v
              ┌────────────────┐
              │  post_         │
              │  processing()  │
              └────────┬───────┘
                       │
                       v
              ┌────────────────┐
              │  Recursive     │
              │  processing of │
              │  large nodes   │
              └────────┬───────┘
                       │
                       v
              ┌────────────────┐
              │  Add IDs,      │
              │  summaries,    │
              │  descriptions  │
              └────────┬───────┘
                       │
                       v
              ┌────────────────┐
              │  Return JSON   │
              │  structure     │
              └────────────────┘
```

---

## TOC Detection Flow

**Function:** `check_toc(page_list, opt)` at `pageindex/page_index.py:688-725`

```
┌─────────────────────────────────────────────────────────┐
│                     check_toc()                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       v
              ┌────────────────────┐
              │ find_toc_pages()   │
              │ Check first 20 pgs │
              └─────────┬──────────┘
                        │
             ┌──────────┴──────────┐
             │                     │
             v                     v
        TOC Found              No TOC
             │                     │
             v                     └──> Return: no TOC
    ┌────────────────┐
    │ toc_extractor()│
    │ - Extract text │
    │ - Clean format │
    └────────┬───────┘
             │
             v
    ┌────────────────────┐
    │ detect_page_index()│
    │ Check if TOC has   │
    │ page numbers       │
    └─────────┬──────────┘
             │
      ┌──────┴──────┐
      │             │
      v             v
  Has Numbers   No Numbers
      │             │
      v             v
Return: TOC    Return: TOC
with pages     no pages
```

**Key Functions:**
- `toc_detector_single_page()` at line 104: Uses LLM to detect TOC on each page
- `extract_toc_content()` at line 160: Extracts and cleans TOC content
- `detect_page_index()` at line 199: Detects if page numbers exist in TOC

---

## Processing Modes

PageIndex has three processing modes based on TOC detection:

### Mode 1: TOC with Page Numbers

**Function:** `process_toc_with_page_numbers()` at `pageindex/page_index.py:614-643`

```
TOC with page numbers detected
        │
        v
┌──────────────────┐
│ toc_transformer()│  Transform TOC to JSON
│                  │  Returns: [{"structure": "1", "title": "...", "page": 5}, ...]
└────────┬─────────┘
         │
         v
┌──────────────────────┐
│ toc_index_extractor()│  Map page numbers to physical indices
│                      │  by checking actual content
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Calculate page offset│  offset = physical_index - page_number
│ (most common)        │
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Apply offset to all  │  physical_index = page + offset
│ TOC items            │
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ process_none_page_   │  Fill in missing indices
│ numbers()            │
└──────────────────────┘
```

### Mode 2: TOC without Page Numbers

**Function:** `process_toc_no_page_numbers()` at `pageindex/page_index.py:589-610`

```
TOC without page numbers detected
        │
        v
┌──────────────────┐
│ toc_transformer()│  Transform TOC to JSON
│                  │  Returns: [{"structure": "1", "title": "..."}, ...]
└────────┬─────────┘
         │
         v
┌──────────────────────┐
│ Group pages into     │  Create chunks of ~20k tokens
│ chunks with          │
│ <physical_index_X>   │
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ For each chunk:      │
│ add_page_number_     │  LLM finds which page each
│ to_toc()             │  section starts on
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ convert_physical_    │  Convert tags to integers
│ index_to_int()       │
└──────────────────────┘
```

### Mode 3: No TOC

**Function:** `process_no_toc()` at `pageindex/page_index.py:568-587`

```
No TOC detected
        │
        v
┌──────────────────────┐
│ Add <physical_index> │  Tag each page
│ tags to all pages    │
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Group into chunks    │  ~20k tokens per chunk
│ with overlap         │
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ generate_toc_init()  │  LLM extracts structure
│ for first chunk      │  from first chunk
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ For remaining chunks:│
│ generate_toc_        │  LLM continues structure
│ continue()           │  extraction
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Merge all chunks     │  Combine into single list
└──────────────────────┘
```

---

## Tree Construction Flow

**Function:** `post_processing()` at `pageindex/utils.py` (not shown in excerpt but referenced)

```
Flat TOC list received
        │
        v
┌──────────────────────┐
│ Parse structure      │  "1.2.3" -> determine hierarchy level
│ indices              │
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Build parent-child   │  Create nested structure
│ relationships        │  based on numeric indices
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Calculate end_index  │  end_index = next sibling's start_index - 1
│ for each node        │  or parent's end_index
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Recursively process  │  For nodes > max_page_num:
│ large nodes          │  - Extract sub-structure
└────────┬─────────────┘  - Create child nodes
         │
         v
Output: Nested tree structure
```

**Example:**
```json
[
  {
    "title": "Chapter 1",
    "start_index": 1,
    "end_index": 20,
    "nodes": [
      {
        "title": "Section 1.1",
        "start_index": 1,
        "end_index": 10,
        "nodes": []
      },
      {
        "title": "Section 1.2",
        "start_index": 11,
        "end_index": 20,
        "nodes": []
      }
    ]
  }
]
```

---

## Verification and Fixing Flow

### Verification Flow

**Function:** `verify_toc()` at `pageindex/page_index.py:892-944`

```
TOC structure generated
        │
        v
┌──────────────────────────┐
│ Select sample items      │  Random N items or all items
│ for verification         │
└────────┬─────────────────┘
         │
         v
┌──────────────────────────┐
│ For each item (async):   │
│ check_title_             │  LLM verifies if title appears
│ appearance()             │  at the claimed physical_index
└────────┬─────────────────┘
         │
         v
┌──────────────────────────┐
│ Aggregate results        │  Count correct vs incorrect
└────────┬─────────────────┘
         │
         v
┌──────────────────────────┐
│ Calculate accuracy       │  accuracy = correct / total
└────────┬─────────────────┘
         │
         v
    accuracy value
```

### Fixing Flow

**Function:** `fix_incorrect_toc_with_retries()` at `pageindex/page_index.py:870-886`

```
Incorrect items detected
        │
        v
┌──────────────────────────┐
│ For each incorrect item: │
│                          │
│ 1. Find prev/next        │  Determine search range
│    correct items         │
│                          │
│ 2. Extract page range    │  Get content between boundaries
│                          │
│ 3. single_toc_item_      │  LLM finds correct physical_index
│    index_fixer()         │  within the range
│                          │
│ 4. Verify fix            │  Check if new index is correct
└────────┬─────────────────┘
         │
    ┌────┴────┐
    │         │
    v         v
  Valid    Invalid
    │         │
    v         └──> Add to retry list
Update TOC
    │
    v
┌────────────┐
│ Retry up to│
│ 3 times    │
└────────────┘
```

**File:** `pageindex/page_index.py:752-886`

---

## Post-Processing Flow

**Function:** `page_index_builder()` at `pageindex/page_index.py:1074-1098`

```
Tree structure verified
        │
        v
┌──────────────────────────┐
│ if_add_node_id == 'yes': │
│ write_node_id()          │  Add "0001", "0002", etc.
└────────┬─────────────────┘
         │
         v
┌──────────────────────────┐
│ if_add_node_text == 'yes'│
│ add_node_text()          │  Extract full text for each node
└────────┬─────────────────┘
         │
         v
┌──────────────────────────────┐
│ if_add_node_summary == 'yes':│
│                              │
│ 1. Add text if not present   │
│ 2. generate_summaries_for_   │  Async LLM summarization
│    structure()               │  for all nodes in parallel
│ 3. Remove text if not needed │
└────────┬─────────────────────┘
         │
         v
┌──────────────────────────────────┐
│ if_add_doc_description == 'yes': │
│                                  │
│ 1. Create clean structure        │
│ 2. generate_doc_description()    │  LLM creates doc overview
└────────┬─────────────────────────┘
         │
         v
┌──────────────────────────┐
│ Return final structure   │
│ {                        │
│   "doc_name": "...",     │
│   "doc_description": "...",
│   "structure": [...]     │
│ }                        │
└──────────────────────────┘
```

---

## Data Flow Diagram

### From PDF to Tree

```
Input: document.pdf
    │
    v
┌──────────────────────────────────────────┐
│ Phase 1: Parsing                         │
├──────────────────────────────────────────┤
│ get_page_tokens()                        │
│ Returns: [(page_text, token_count), ...] │
└────────┬─────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────┐
│ Phase 2: TOC Detection                   │
├──────────────────────────────────────────┤
│ check_toc()                              │
│ Returns: {                               │
│   "toc_content": "...",                  │
│   "page_index_given_in_toc": "yes/no"   │
│ }                                        │
└────────┬─────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────┐
│ Phase 3: Structure Extraction            │
├──────────────────────────────────────────┤
│ meta_processor()                         │
│ Returns: [                               │
│   {                                      │
│     "structure": "1",                    │
│     "title": "Introduction",             │
│     "physical_index": 1                  │
│   },                                     │
│   ...                                    │
│ ]                                        │
└────────┬─────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────┐
│ Phase 4: Verification                    │
├──────────────────────────────────────────┤
│ verify_toc()                             │
│ Returns: (accuracy, incorrect_items)     │
└────────┬─────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────┐
│ Phase 5: Fixing (if needed)              │
├──────────────────────────────────────────┤
│ fix_incorrect_toc_with_retries()         │
│ Returns: corrected TOC list              │
└────────┬─────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────┐
│ Phase 6: Tree Construction               │
├──────────────────────────────────────────┤
│ post_processing()                        │
│ Returns: nested tree structure           │
└────────┬─────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────┐
│ Phase 7: Recursive Processing            │
├──────────────────────────────────────────┤
│ process_large_node_recursively()         │
│ Breaks down nodes > max_page_num         │
└────────┬─────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────┐
│ Phase 8: Enhancement                     │
├──────────────────────────────────────────┤
│ - Add node IDs                           │
│ - Add summaries (async, parallel)        │
│ - Add document description               │
└────────┬─────────────────────────────────┘
         │
         v
Output: JSON tree structure
```

---

## Key Decision Points

### 1. TOC Processing Mode Selection

**Location:** `meta_processor()` at `pageindex/page_index.py:951-989`

```
Decision: Which processing mode?

IF TOC exists AND has page numbers:
    → process_toc_with_page_numbers()

ELSE IF TOC exists BUT no page numbers:
    → process_toc_no_page_numbers()

ELSE (no TOC):
    → process_no_toc()
```

### 2. Fallback Chain

**Location:** `meta_processor()` at `pageindex/page_index.py:978-989`

```
After processing, verify accuracy:

IF accuracy == 1.0 AND no errors:
    → Return structure

ELSE IF accuracy > 0.6 AND errors exist:
    → Fix errors with fix_incorrect_toc_with_retries()
    → Return fixed structure

ELSE IF accuracy ≤ 0.6:
    IF current_mode == 'process_toc_with_page_numbers':
        → Fallback to 'process_toc_no_page_numbers'
    ELSE IF current_mode == 'process_toc_no_page_numbers':
        → Fallback to 'process_no_toc'
    ELSE:
        → Raise exception (processing failed)
```

### 3. Large Node Processing

**Location:** `process_large_node_recursively()` at `pageindex/page_index.py:992-1019`

```
For each node in tree:

IF (node.pages > max_page_num) AND (node.tokens > max_token_num):
    → Extract sub-structure from node content
    → Create child nodes
    → Recursively process each child node

ELSE:
    → Keep node as-is
```

### 4. Summary Generation

**Location:** `page_index_builder()` at `pageindex/page_index.py:1080-1085`

```
IF if_add_node_summary == 'yes':
    IF if_add_node_text == 'no':
        → Temporarily add text to nodes

    → Generate summaries (async, parallel)

    IF if_add_node_text == 'no':
        → Remove text from nodes (keep summaries)
```

---

## Execution Time Characteristics

### Sequential Operations
- PDF parsing
- TOC detection (page by page)
- Structure extraction (per chunk)

### Parallel Operations (async)
- Title verification (`verify_toc()`)
- Error fixing (`fix_incorrect_toc()`)
- Summary generation (`generate_summaries_for_structure()`)
- Large node processing (`process_large_node_recursively()`)

### Typical Processing Time

For a 100-page PDF:
```
- PDF parsing: ~5-10 seconds
- TOC detection: ~30-60 seconds (20 pages × 2-3s per LLM call)
- Structure extraction: ~60-120 seconds (depends on mode)
- Verification: ~30-60 seconds (parallel)
- Summary generation: ~120-180 seconds (parallel, all nodes)

Total: ~4-7 minutes with summaries
       ~2-4 minutes without summaries
```

---

## Configuration Flow

**File:** `pageindex/config.yaml` + `pageindex/utils.py` (ConfigLoader)

```
User provides arguments
    │
    v
┌──────────────────────┐
│ Load config.yaml     │  Default values
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Merge with user args │  User args override defaults
└────────┬─────────────┘
         │
         v
┌──────────────────────┐
│ Create config object │  SimpleNamespace
│ opt.model            │
│ opt.toc_check_page_  │
│ num                  │
│ ...                  │
└────────┬─────────────┘
         │
         v
Pass to processing functions
```

**Default Configuration:**
```yaml
model: "gpt-4o-2024-11-20"
toc_check_page_num: 20
max_page_num_each_node: 10
max_token_num_each_node: 20000
if_add_node_id: "yes"
if_add_node_summary: "yes"
if_add_doc_description: "no"
if_add_node_text: "no"
```

---

## Error Handling Flow

### LLM API Calls

**File:** `pageindex/utils.py:29-86`

```
Make LLM API call
    │
    v
Try (up to 10 retries):
    │
    ├─> Success → Return response
    │
    └─> Error → Wait 1 second → Retry

After 10 retries:
    → Log error
    → Return "Error"
```

### TOC Processing Failures

```
Try Mode 1: TOC with page numbers
    │
    ├─> Accuracy < 60% → Fallback to Mode 2
    │
Mode 2: TOC without page numbers
    │
    ├─> Accuracy < 60% → Fallback to Mode 3
    │
Mode 3: No TOC (generate from scratch)
    │
    └─> If still fails → Raise Exception
```

---

## Output Structure

### Final JSON Format

```json
{
  "doc_name": "document.pdf",
  "doc_description": "This document discusses...",
  "structure": [
    {
      "title": "Introduction",
      "node_id": "0001",
      "start_index": 1,
      "end_index": 5,
      "summary": "This section introduces the main concepts...",
      "nodes": [
        {
          "title": "Background",
          "node_id": "0002",
          "start_index": 1,
          "end_index": 3,
          "summary": "Historical context and motivation...",
          "nodes": []
        },
        {
          "title": "Scope",
          "node_id": "0003",
          "start_index": 4,
          "end_index": 5,
          "summary": "This document covers...",
          "nodes": []
        }
      ]
    }
  ]
}
```

### Saving Output

**File:** `run_pageindex.py:71-79` (PDF) and `run_pageindex.py:125-133` (Markdown)

```
Process document
    │
    v
Get JSON structure
    │
    v
Create ./results/ directory
    │
    v
Save to ./results/{filename}_structure.json
```

---

## Summary of Key Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `run_pageindex.py` | CLI entry point | Argument parsing, file validation |
| `pageindex/page_index.py` | PDF processing engine | `page_index_main()`, `tree_parser()`, `meta_processor()` |
| `pageindex/page_index_md.py` | Markdown processing | `md_to_tree()` |
| `pageindex/utils.py` | Utilities | `ChatGPT_API()`, `get_page_tokens()`, `ConfigLoader` |
| `pageindex/config.yaml` | Default configuration | All default settings |

---

## Quick Reference

### Start Processing
```bash
python run_pageindex.py --pdf_path document.pdf
```

### Main Function Call Chain
```
page_index_main()
  → tree_parser()
    → check_toc()
    → meta_processor()
      → verify_toc()
      → fix_incorrect_toc_with_retries() (if needed)
    → post_processing()
    → process_large_node_recursively()
  → write_node_id()
  → generate_summaries_for_structure()
```

### Key Async Points
- `verify_toc()`: Parallel title verification
- `fix_incorrect_toc()`: Parallel error fixing
- `generate_summaries_for_structure()`: Parallel summary generation
- `process_large_node_recursively()`: Parallel node processing

---

## Conclusion

PageIndex follows a sophisticated multi-stage pipeline:

1. **Parse** the document into pages
2. **Detect** TOC and determine processing mode
3. **Extract** hierarchical structure
4. **Verify** accuracy with LLM-based checking
5. **Fix** errors through intelligent retry
6. **Construct** nested tree from flat list
7. **Process** large nodes recursively
8. **Enhance** with IDs, summaries, descriptions

The system uses intelligent fallback strategies and parallel processing to ensure robust, accurate document structure extraction.

---

**For more detailed information:**
- Architecture: `docs/ARCHITECTURE.md`
- Developer Guide: `docs/DEVELOPER_GUIDE.md`
- Quick Start: `docs/QUICK_START.md`
- AI Concepts: `docs/GENERATIVE_AI_CONCEPTS.md`

**Last updated:** November 2025
