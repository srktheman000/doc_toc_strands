# Quick Start Guide for New Developers

## Welcome! 👋

This guide will get you from zero to running PageIndex in under 10 minutes.

---

## Prerequisites

- **Python 3.8+** installed
- **OpenAI API key** (get one at [platform.openai.com](https://platform.openai.com))
- Basic understanding of Python

---

## 5-Minute Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/VectifyAI/PageIndex.git
cd PageIndex
```

### Step 2: Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 3: Set Your API Key

Create a `.env` file in the project root:

```bash
# On Windows PowerShell:
echo "CHATGPT_API_KEY=your_actual_api_key_here" > .env

# On Mac/Linux:
echo "CHATGPT_API_KEY=your_actual_api_key_here" > .env
```

Replace `your_actual_api_key_here` with your OpenAI API key.

### Step 4: Run Your First Example

```bash
# Process a sample PDF
python run_pageindex.py --pdf_path tests/pdfs/2023-annual-report.pdf
```

**Output**: You'll see a JSON file in `results/` with the hierarchical structure!

---

## Understanding the Output

Open the generated file `results/2023-annual-report_structure.json`:

```json
{
  "doc_name": "2023-annual-report",
  "structure": [
    {
      "title": "Letter from the Chairman",
      "node_id": "0001",
      "start_index": 3,
      "end_index": 5,
      "summary": "The chairman discusses...",
      "nodes": []
    },
    {
      "title": "Financial Results",
      "node_id": "0002",
      "start_index": 6,
      "end_index": 25,
      "summary": "This section covers...",
      "nodes": [
        {
          "title": "Revenue Analysis",
          "node_id": "0003",
          "start_index": 6,
          "end_index": 15,
          "summary": "Detailed revenue breakdown...",
          "nodes": []
        }
      ]
    }
  ]
}
```

**Key Fields:**

- `title`: Section name
- `node_id`: Unique identifier
- `start_index`: First page of section
- `end_index`: Last page of section
- `summary`: AI-generated summary
- `nodes`: Child sections (recursive)

---

## Your First Custom Script

Create `my_first_script.py`:

```python
from pageindex import page_index
import json

# Process a document
result = page_index(
    doc="tests/pdfs/2023-annual-report.pdf",
    model="gpt-4o-2024-11-20",
    if_add_node_summary="yes"
)

# Print document info
print(f"Document: {result['doc_name']}")
print(f"Number of sections: {len(result['structure'])}")

# Print all section titles
def print_titles(structure, indent=0):
    for node in structure:
        print("  " * indent + f"- {node['title']}")
        if node.get('nodes'):
            print_titles(node['nodes'], indent + 1)

print("\nTable of Contents:")
print_titles(result['structure'])

# Save to file
with open('my_output.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("\n✓ Saved to my_output.json")
```

Run it:

```bash
python my_first_script.py
```

---

## Common Use Cases

### Use Case 1: Process Your Own PDF

```bash
python run_pageindex.py --pdf_path /path/to/your/document.pdf
```

### Use Case 2: Process a Markdown File

```bash
python run_pageindex.py --md_path /path/to/your/document.md
```

### Use Case 3: Get Detailed Summaries

```bash
python run_pageindex.py \
    --pdf_path your_document.pdf \
    --if-add-node-summary yes \
    --if-add-doc-description yes
```

### Use Case 4: Include Full Text

```bash
python run_pageindex.py \
    --pdf_path your_document.pdf \
    --if-add-node-text yes
```

**Warning**: Including full text creates very large JSON files!

---

## Troubleshooting

### Problem: `ModuleNotFoundError`

**Solution**: Make sure you installed dependencies:

```bash
pip install -r requirements.txt
```

### Problem: `API key not found`

**Solution**: Check your `.env` file:

```bash
# View your .env file
cat .env  # Mac/Linux
type .env  # Windows

# Make sure it contains:
CHATGPT_API_KEY=sk-...
```

### Problem: `Rate limit exceeded`

**Solution**: You're making too many API calls. Wait a few minutes or upgrade your OpenAI plan.

### Problem: Processing takes too long

**Solution**: Start with smaller documents or use the mini model for testing:

```bash
python run_pageindex.py \
    --pdf_path small_doc.pdf \
    --model gpt-4o-mini
```

### Problem: JSON parsing error

**Solution**: The LLM response format was unexpected. This is usually transient. Try running again.

---

## Understanding Costs

PageIndex uses the OpenAI API, which charges per token.

**Rough estimates** (for reference only):

| Document Size  | Estimated Cost (GPT-4o) |
| -------------- | ----------------------- |
| 10-page report | $0.10 - $0.30           |
| 50-page report | $0.50 - $1.50           |
| 200-page book  | $2.00 - $5.00           |

**Tips to reduce costs:**

1. Use `gpt-4o-mini` for testing:

   ```python
   result = page_index(doc="test.pdf", model="gpt-4o-mini")
   ```

2. Disable summaries during development:

   ```python
   result = page_index(doc="test.pdf", if_add_node_summary="no")
   ```

3. Cache results (don't reprocess the same document):

   ```python
   import os

   if os.path.exists('cached_result.json'):
       with open('cached_result.json') as f:
           result = json.load(f)
   else:
       result = page_index(doc="document.pdf")
       with open('cached_result.json', 'w') as f:
           json.dump(result, f)
   ```

---

## Next Steps

### Learn More

1. **Developer Guide**: Deep dive into the codebase

   - Read: `docs/DEVELOPER_GUIDE.md`

2. **Generative AI Concepts**: Understand the AI techniques

   - Read: `docs/GENERATIVE_AI_CONCEPTS.md`

3. **Examples**: See real-world applications
   - Check: `cookbook/pageindex_RAG_simple.ipynb`
   - Check: `tutorials/` directory

### Try These Exercises

**Exercise 1**: Process 3 different PDFs and compare their structures

**Exercise 2**: Write a script that finds all sections mentioning "revenue"

```python
def find_sections_with_keyword(structure, keyword):
    results = []
    for node in structure:
        if keyword.lower() in node['title'].lower():
            results.append(node)
        if node.get('summary') and keyword.lower() in node['summary'].lower():
            results.append(node)
        if node.get('nodes'):
            results.extend(find_sections_with_keyword(node['nodes'], keyword))
    return results

# Use it
result = page_index(doc="report.pdf", if_add_node_summary="yes")
revenue_sections = find_sections_with_keyword(result['structure'], "revenue")

for section in revenue_sections:
    print(f"- {section['title']} (pages {section['start_index']}-{section['end_index']})")
```

**Exercise 3**: Build a simple search interface

```python
def search_document(doc_path, query):
    """Search a document for relevant sections"""

    # Process document
    result = page_index(
        doc=doc_path,
        if_add_node_summary="yes"
    )

    # Simple keyword search
    matches = []

    def search_node(node):
        # Check title
        if query.lower() in node['title'].lower():
            matches.append({
                'title': node['title'],
                'pages': f"{node['start_index']}-{node['end_index']}",
                'summary': node.get('summary', '')
            })

        # Check summary
        if node.get('summary') and query.lower() in node['summary'].lower():
            matches.append({
                'title': node['title'],
                'pages': f"{node['start_index']}-{node['end_index']}",
                'summary': node.get('summary', '')
            })

        # Recurse
        if node.get('nodes'):
            for child in node['nodes']:
                search_node(child)

    for node in result['structure']:
        search_node(node)

    return matches

# Test it
results = search_document("report.pdf", "financial")
for r in results:
    print(f"\n{r['title']} (pages {r['pages']})")
    print(f"Summary: {r['summary']}")
```

---

## Tips for Success

### 1. Start Small

Begin with short documents (10-20 pages) to understand the system.

### 2. Use Test Documents

PageIndex provides sample PDFs in `tests/pdfs/`. Use these for learning.

### 3. Check the Logs

When something goes wrong, check the console output. PageIndex logs helpful information.

### 4. Experiment with Parameters

Try different settings:

```bash
# More pages per node
python run_pageindex.py --pdf_path doc.pdf --max-pages-per-node 15

# Check more pages for TOC
python run_pageindex.py --pdf_path doc.pdf --toc-check-pages 30

# Different model
python run_pageindex.py --pdf_path doc.pdf --model gpt-4o-mini
```

### 5. Cache Expensive Operations

Processing large documents is expensive. Save results:

```python
import os
import json
from pageindex import page_index

def get_or_create_structure(pdf_path, force_refresh=False):
    """Get structure from cache or create new"""

    cache_file = pdf_path.replace('.pdf', '_cache.json')

    if os.path.exists(cache_file) and not force_refresh:
        print("Loading from cache...")
        with open(cache_file) as f:
            return json.load(f)

    print("Processing document...")
    result = page_index(doc=pdf_path)

    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(result, f, indent=2)

    return result

# Use it
structure = get_or_create_structure("large_report.pdf")
```

---

## Getting Help

### Documentation

- **Main README**: `README.md` - Overview and installation
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md` - Detailed code walkthrough
- **AI Concepts**: `docs/GENERATIVE_AI_CONCEPTS.md` - Generative AI techniques

### Community

- **Discord**: [Join our community](https://discord.com/invite/VuXuf29EUj)
- **GitHub Issues**: [Report bugs or ask questions](https://github.com/VectifyAI/PageIndex/issues)
- **Twitter/X**: [@VectifyAI](https://x.com/VectifyAI)

### Common Questions

**Q: Can I use a different LLM (not OpenAI)?**

A: Currently, PageIndex is built for OpenAI's API. You could modify `utils.py` to use other APIs, but you'd need to adjust the code.

**Q: Does this work with scanned PDFs?**

A: No, you need text-based PDFs. For scanned documents, use [PageIndex OCR](https://dash.pageindex.ai/) first.

**Q: Can I process Word documents?**

A: Not directly. Convert to PDF first, or convert to Markdown and use `--md_path`.

**Q: How accurate is the structure extraction?**

A: Very high for well-formatted documents with clear TOC. PageIndex achieved 98.7% accuracy on FinanceBench.

**Q: Is my data sent to OpenAI?**

A: Yes, when using the OpenAI API, your document text is sent to their servers. Don't process confidential documents unless you have appropriate agreements with OpenAI.

---

## What You've Learned

✅ How to install and run PageIndex

✅ How to process PDF and Markdown files

✅ How to read and understand the output structure

✅ How to write basic scripts using PageIndex

✅ How to troubleshoot common issues

✅ How to manage costs and cache results

---

## Ready for More?

**Dive deeper:**

- Build a complete RAG system (see `GENERATIVE_AI_CONCEPTS.md`)
- Understand the architecture (see `DEVELOPER_GUIDE.md`)
- Explore advanced features in the tutorials

**Contribute:**

- Found a bug? [Open an issue](https://github.com/VectifyAI/PageIndex/issues)
- Have an idea? Start a discussion on Discord
- Want to contribute code? Check out the contribution guidelines

---

**Happy coding!** 🚀

Don't forget to ⭐ star the repo if you find it useful!
