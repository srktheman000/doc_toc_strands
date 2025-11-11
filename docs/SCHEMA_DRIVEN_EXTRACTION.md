# Schema-Driven JSON Extraction with PageIndex

## Overview

This guide shows you how to extract structured JSON from long documents when you have an **expected schema** or structure in advance. This approach combines PageIndex's intelligent document navigation with schema-guided extraction for highly accurate results.

---

## Table of Contents

1. [Why Schema-Driven Extraction?](#why-schema-driven-extraction)
2. [Basic Approach](#basic-approach)
3. [Implementation Strategies](#implementation-strategies)
4. [Complete Examples](#complete-examples)
5. [Best Practices](#best-practices)
6. [Advanced Techniques](#advanced-techniques)

---

## Why Schema-Driven Extraction?

### The Problem

Traditional approaches to extracting structured data from long documents:

- **Chunking + Extraction**: Loses context, misses relationships
- **Full Document Extraction**: Exceeds LLM context limits
- **Template Matching**: Too rigid, fails on variations

### The PageIndex Solution

PageIndex + Schema = **Smart Navigation + Structured Extraction**

```
Expected Schema → Guide PageIndex → Navigate Document → Extract Precisely
```

**Benefits:**

- ✅ Handles documents beyond context limits
- ✅ Maintains document context and relationships
- ✅ Validates extraction against schema
- ✅ Handles missing or optional fields gracefully
- ✅ Cost-effective (only processes relevant sections)

---

## Basic Approach

### Step 1: Define Your Schema

```python
# Example: Financial Report Schema
financial_report_schema = {
    "company_name": str,
    "fiscal_year": int,
    "revenue": {
        "total": float,
        "by_quarter": {
            "Q1": float,
            "Q2": float,
            "Q3": float,
            "Q4": float
        },
        "by_segment": [
            {
                "name": str,
                "amount": float,
                "percentage": float
            }
        ]
    },
    "expenses": {
        "operating": float,
        "research_development": float,
        "sales_marketing": float
    },
    "net_income": float,
    "key_metrics": {
        "earnings_per_share": float,
        "profit_margin": float,
        "return_on_equity": float
    }
}
```

### Step 2: Index the Document

```python
from pageindex import page_index

# Create the document index
result = page_index(
    doc="annual_report_2023.pdf",
    model="gpt-4o-2024-11-20",
    if_add_node_summary="yes",
    if_add_node_text="yes"  # Include text for extraction
)

document_tree = result['structure']
```

### Step 3: Map Schema to Tree Sections

```python
def map_schema_to_sections(schema, document_tree):
    """
    Map schema fields to relevant document sections using LLM reasoning
    """
    import openai

    # Create section summaries
    section_list = []
    def extract_sections(nodes, path=""):
        for node in nodes:
            section_list.append({
                'node_id': node['node_id'],
                'title': node['title'],
                'path': f"{path}/{node['title']}" if path else node['title'],
                'summary': node.get('summary', ''),
                'pages': f"{node['start_index']}-{node['end_index']}"
            })
            if node.get('nodes'):
                extract_sections(node['nodes'], section_list[-1]['path'])

    extract_sections(document_tree)

    # Map schema fields to sections
    client = openai.OpenAI()

    prompt = f"""
You are an expert at mapping data schema fields to document sections.

Schema fields to extract:
{list(schema.keys())}

Available document sections:
{chr(10).join([f"- [{s['node_id']}] {s['title']} (Pages {s['pages']}): {s['summary']}" for s in section_list])}

Task: For each schema field, identify which section(s) would contain that information.

Return JSON format:
{{
    "field_name": {{
        "relevant_node_ids": ["node_id1", "node_id2"],
        "reasoning": "why these sections are relevant"
    }},
    ...
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    import json
    mapping = json.loads(response.choices[0].message.content)
    return mapping, section_list
```

### Step 4: Extract Data with Schema Validation

```python
def extract_with_schema(schema, mapping, document_tree, section_list):
    """
    Extract data using schema guidance
    """
    import openai
    client = openai.OpenAI()

    extracted_data = {}

    # Get node text by ID
    def get_node_by_id(nodes, node_id):
        for node in nodes:
            if node['node_id'] == node_id:
                return node
            if node.get('nodes'):
                result = get_node_by_id(node['nodes'], node_id)
                if result:
                    return result
        return None

    # Extract each field
    for field_name, field_info in mapping.items():
        relevant_node_ids = field_info['relevant_node_ids']

        # Gather text from relevant sections
        context_text = ""
        for node_id in relevant_node_ids:
            node = get_node_by_id(document_tree, node_id)
            if node and 'text' in node:
                context_text += f"\n\n--- {node['title']} ---\n{node['text']}"

        # Get expected type for this field
        field_type = schema.get(field_name, "any")

        # Extract with schema guidance
        extraction_prompt = f"""
Extract the value for the field "{field_name}" from the following document sections.

Expected field type: {field_type}

Document sections:
{context_text}

Instructions:
1. Find the exact value for "{field_name}"
2. Return in the expected type/format: {field_type}
3. If the value is not found, return null
4. If the value is ambiguous, return the most likely value

Return JSON format:
{{
    "value": <extracted value in correct type>,
    "confidence": <"high" | "medium" | "low">,
    "source_location": <where you found it>,
    "reasoning": <brief explanation>
}}
"""

        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0
        )

        import json
        extraction_result = json.loads(response.choices[0].message.content)
        extracted_data[field_name] = extraction_result['value']

    return extracted_data
```

---

## Implementation Strategies

### Strategy 1: Two-Phase Extraction (Recommended)

**Phase 1**: Map schema to sections using PageIndex structure
**Phase 2**: Extract field values from mapped sections

```python
class SchemaGuidedExtractor:
    def __init__(self, schema, model="gpt-4o-2024-11-20"):
        self.schema = schema
        self.model = model
        self.document_tree = None
        self.mapping = None

    def index_document(self, pdf_path):
        """Phase 1: Index the document"""
        from pageindex import page_index

        print("📄 Indexing document...")
        result = page_index(
            doc=pdf_path,
            model=self.model,
            if_add_node_summary="yes",
            if_add_node_text="yes"
        )

        self.document_tree = result['structure']
        print(f"✓ Indexed {len(self._flatten_tree(self.document_tree))} sections")
        return self

    def map_schema_to_tree(self):
        """Phase 2: Map schema fields to tree sections"""
        print("\n🗺️  Mapping schema to document sections...")

        sections = self._flatten_tree(self.document_tree)
        self.mapping = self._create_mapping(sections)

        print(f"✓ Mapped {len(self.mapping)} schema fields")
        return self

    def extract(self):
        """Phase 3: Extract data with validation"""
        print("\n📊 Extracting structured data...")

        extracted = {}
        for field_name, field_schema in self.schema.items():
            value = self._extract_field(field_name, field_schema)
            extracted[field_name] = value
            print(f"  ✓ {field_name}: {value}")

        # Validate against schema
        self._validate_extracted_data(extracted)

        print("\n✅ Extraction complete!")
        return extracted

    def _flatten_tree(self, nodes, result=None):
        """Flatten tree structure to list"""
        if result is None:
            result = []

        for node in nodes:
            result.append(node)
            if node.get('nodes'):
                self._flatten_tree(node['nodes'], result)

        return result

    def _create_mapping(self, sections):
        """Create mapping between schema and sections"""
        import openai
        import json

        client = openai.OpenAI()

        # Build section descriptions
        section_desc = "\n".join([
            f"[{s['node_id']}] {s['title']} (Pages {s['start_index']}-{s['end_index']})"
            + (f": {s.get('summary', '')}" if s.get('summary') else "")
            for s in sections
        ])

        prompt = f"""
Map each schema field to the most relevant document sections.

Schema fields:
{json.dumps(list(self.schema.keys()), indent=2)}

Document sections:
{section_desc}

Return JSON mapping:
{{
    "field_name": ["node_id1", "node_id2"],
    ...
}}
"""

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return json.loads(response.choices[0].message.content)

    def _extract_field(self, field_name, field_schema):
        """Extract a single field value"""
        import openai
        import json

        # Get relevant sections
        node_ids = self.mapping.get(field_name, [])
        if not node_ids:
            return None

        # Gather context
        context = self._gather_context(node_ids)

        # Extract value
        client = openai.OpenAI()

        prompt = f"""
Extract "{field_name}" from the document sections below.

Expected type: {field_schema}

Document sections:
{context}

Return only the extracted value in JSON format:
{{"value": <extracted_value>}}

If not found, return {{"value": null}}
"""

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        result = json.loads(response.choices[0].message.content)
        return result['value']

    def _gather_context(self, node_ids):
        """Gather text from specified nodes"""
        sections = self._flatten_tree(self.document_tree)

        context = ""
        for node_id in node_ids:
            for section in sections:
                if section['node_id'] == node_id:
                    context += f"\n\n=== {section['title']} ===\n"
                    context += section.get('text', section.get('summary', ''))
                    break

        return context

    def _validate_extracted_data(self, data):
        """Validate extracted data against schema"""
        for field, expected_type in self.schema.items():
            if field not in data:
                print(f"  ⚠️  Missing field: {field}")
            elif data[field] is None:
                print(f"  ⚠️  Null value: {field}")
```

### Strategy 2: Progressive Refinement

Start with coarse extraction, refine iteratively:

```python
def progressive_extraction(document_tree, schema, max_iterations=3):
    """
    Progressively refine extraction with validation loops
    """
    import openai
    import json

    client = openai.OpenAI()
    extracted = {}
    confidence_scores = {}

    for iteration in range(max_iterations):
        print(f"\n🔄 Iteration {iteration + 1}/{max_iterations}")

        # Identify low-confidence or missing fields
        fields_to_extract = []

        if iteration == 0:
            # First iteration: extract all
            fields_to_extract = list(schema.keys())
        else:
            # Subsequent iterations: focus on low-confidence
            fields_to_extract = [
                field for field, conf in confidence_scores.items()
                if conf < 0.8 or extracted.get(field) is None
            ]

        if not fields_to_extract:
            print("✓ All fields extracted with high confidence")
            break

        # Extract with more targeted prompts
        for field in fields_to_extract:
            result = extract_field_with_validation(
                field,
                schema[field],
                document_tree,
                previous_value=extracted.get(field)
            )

            extracted[field] = result['value']
            confidence_scores[field] = result['confidence']

            print(f"  {field}: {result['value']} (confidence: {result['confidence']:.2f})")

    return extracted, confidence_scores
```

### Strategy 3: Hierarchical Schema Extraction

For nested/complex schemas:

```python
def hierarchical_extraction(document_tree, nested_schema, current_path=""):
    """
    Extract nested/hierarchical schemas recursively
    """
    extracted = {}

    for field_name, field_schema in nested_schema.items():
        full_path = f"{current_path}.{field_name}" if current_path else field_name

        if isinstance(field_schema, dict):
            # Nested object - recurse
            print(f"📦 Extracting nested: {full_path}")
            extracted[field_name] = hierarchical_extraction(
                document_tree,
                field_schema,
                full_path
            )

        elif isinstance(field_schema, list) and len(field_schema) > 0:
            # Array of objects
            print(f"📋 Extracting array: {full_path}")
            extracted[field_name] = extract_array_field(
                document_tree,
                field_name,
                field_schema[0]
            )

        else:
            # Simple field
            print(f"📝 Extracting field: {full_path}")
            extracted[field_name] = extract_simple_field(
                document_tree,
                field_name,
                field_schema
            )

    return extracted
```

---

## Complete Examples

### Example 1: Financial Report Extraction

```python
from pageindex import page_index
import json

# Define schema
financial_schema = {
    "company_name": str,
    "fiscal_year": int,
    "total_revenue": float,
    "revenue_by_quarter": {
        "Q1": float,
        "Q2": float,
        "Q3": float,
        "Q4": float
    },
    "net_income": float,
    "earnings_per_share": float,
    "total_assets": float,
    "total_liabilities": float,
    "shareholder_equity": float
}

# Use the extractor
extractor = SchemaGuidedExtractor(financial_schema)

# Process
result = (extractor
    .index_document("annual_report_2023.pdf")
    .map_schema_to_tree()
    .extract())

# Save result
with open("extracted_financials.json", "w") as f:
    json.dump(result, f, indent=2)

print("\n📄 Extracted Data:")
print(json.dumps(result, indent=2))
```

**Output:**

```json
{
  "company_name": "Acme Corporation",
  "fiscal_year": 2023,
  "total_revenue": 45600000000,
  "revenue_by_quarter": {
    "Q1": 10200000000,
    "Q2": 11500000000,
    "Q3": 11800000000,
    "Q4": 12100000000
  },
  "net_income": 8900000000,
  "earnings_per_share": 5.67,
  "total_assets": 123400000000,
  "total_liabilities": 78900000000,
  "shareholder_equity": 44500000000
}
```

### Example 2: Research Paper Extraction

```python
# Define research paper schema
research_schema = {
    "title": str,
    "authors": [str],
    "abstract": str,
    "keywords": [str],
    "research_questions": [str],
    "methodology": {
        "approach": str,
        "data_sources": [str],
        "sample_size": int,
        "tools_used": [str]
    },
    "key_findings": [str],
    "conclusions": str,
    "limitations": [str],
    "future_work": [str],
    "references_count": int
}

# Extract
extractor = SchemaGuidedExtractor(research_schema)
result = (extractor
    .index_document("research_paper.pdf")
    .map_schema_to_tree()
    .extract())

print(json.dumps(result, indent=2))
```

### Example 3: Contract Extraction

```python
# Define contract schema
contract_schema = {
    "contract_type": str,
    "effective_date": str,
    "expiration_date": str,
    "parties": [
        {
            "name": str,
            "role": str,
            "address": str
        }
    ],
    "payment_terms": {
        "total_amount": float,
        "currency": str,
        "payment_schedule": [
            {
                "due_date": str,
                "amount": float,
                "description": str
            }
        ]
    },
    "obligations": {
        "party1": [str],
        "party2": [str]
    },
    "termination_conditions": [str],
    "governing_law": str,
    "signatures": [
        {
            "party": str,
            "signatory": str,
            "date": str
        }
    ]
}

# Extract with validation
extractor = SchemaGuidedExtractor(contract_schema)
result = (extractor
    .index_document("contract.pdf")
    .map_schema_to_tree()
    .extract())

# Validate critical fields
required_fields = ["effective_date", "parties", "payment_terms"]
missing = [f for f in required_fields if not result.get(f)]

if missing:
    print(f"⚠️  Missing required fields: {missing}")
else:
    print("✅ All required fields extracted")

# Save
with open("extracted_contract.json", "w") as f:
    json.dump(result, f, indent=2)
```

---

## Best Practices

### 1. Schema Design

✅ **DO:**

- Define explicit types for each field
- Include optional fields with defaults
- Use nested structures for related data
- Document expected formats (dates, currencies, etc.)

❌ **DON'T:**

- Use overly generic field names
- Create deeply nested schemas (>4 levels)
- Mix different data granularities

### 2. Mapping Optimization

```python
def optimize_mapping(schema, document_tree):
    """
    Pre-filter sections to reduce LLM calls
    """
    # Group related fields
    field_groups = {
        "financial": ["revenue", "expenses", "profit", "assets"],
        "temporal": ["date", "year", "quarter", "period"],
        "identity": ["name", "id", "number", "reference"]
    }

    # Map groups instead of individual fields
    group_mappings = {}
    for group_name, fields in field_groups.items():
        relevant_fields = [f for f in fields if f in schema]
        if relevant_fields:
            group_mappings[group_name] = map_field_group(
                relevant_fields,
                document_tree
            )

    return group_mappings
```

### 3. Error Handling

```python
def robust_extraction(field_name, field_schema, context, max_retries=3):
    """
    Extract with retries and fallbacks
    """
    for attempt in range(max_retries):
        try:
            value = extract_field(field_name, field_schema, context)

            # Validate
            if validate_value(value, field_schema):
                return value
            else:
                print(f"  ⚠️  Validation failed for {field_name}, retrying...")

        except Exception as e:
            print(f"  ❌ Error extracting {field_name}: {e}")
            if attempt == max_retries - 1:
                return None

    return None

def validate_value(value, expected_schema):
    """
    Validate extracted value against schema
    """
    if value is None:
        return True  # Allow null values

    if expected_schema == int:
        return isinstance(value, int)
    elif expected_schema == float:
        return isinstance(value, (int, float))
    elif expected_schema == str:
        return isinstance(value, str)
    elif isinstance(expected_schema, list):
        return isinstance(value, list)
    elif isinstance(expected_schema, dict):
        return isinstance(value, dict)

    return True
```

### 4. Caching Strategy

```python
import hashlib
import pickle
import os

def cache_extraction(pdf_path, schema, extractor_func):
    """
    Cache extraction results to avoid reprocessing
    """
    # Create cache key
    cache_key = hashlib.md5(
        f"{pdf_path}_{str(schema)}".encode()
    ).hexdigest()

    cache_file = f".cache/extraction_{cache_key}.pkl"

    # Check cache
    if os.path.exists(cache_file):
        print("📦 Loading from cache...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)

    # Extract
    print("🔄 Extracting (will cache)...")
    result = extractor_func(pdf_path, schema)

    # Save to cache
    os.makedirs(".cache", exist_ok=True)
    with open(cache_file, 'wb') as f:
        pickle.dump(result, f)

    return result
```

### 5. Quality Assurance

```python
def qa_extracted_data(extracted_data, schema, document_tree):
    """
    Quality assurance checks
    """
    qa_report = {
        "completeness": 0.0,
        "missing_fields": [],
        "type_mismatches": [],
        "confidence_score": 0.0
    }

    # Completeness check
    total_fields = len(schema)
    extracted_fields = len([v for v in extracted_data.values() if v is not None])
    qa_report["completeness"] = extracted_fields / total_fields

    # Missing fields
    qa_report["missing_fields"] = [
        field for field in schema.keys()
        if field not in extracted_data or extracted_data[field] is None
    ]

    # Type validation
    for field, expected_type in schema.items():
        if field in extracted_data and extracted_data[field] is not None:
            if not validate_value(extracted_data[field], expected_type):
                qa_report["type_mismatches"].append({
                    "field": field,
                    "expected": str(expected_type),
                    "actual": type(extracted_data[field]).__name__
                })

    # Calculate confidence
    confidence = 1.0
    confidence *= qa_report["completeness"]
    confidence *= (1.0 - len(qa_report["type_mismatches"]) / total_fields)
    qa_report["confidence_score"] = confidence

    return qa_report
```

---

## Advanced Techniques

### 1. Multi-Document Aggregation

Extract schema from multiple documents and aggregate:

```python
def aggregate_multi_document(pdf_paths, schema):
    """
    Extract schema from multiple documents and combine
    """
    all_results = []

    for pdf_path in pdf_paths:
        print(f"\n📄 Processing: {pdf_path}")
        extractor = SchemaGuidedExtractor(schema)
        result = (extractor
            .index_document(pdf_path)
            .map_schema_to_tree()
            .extract())

        all_results.append({
            "source": pdf_path,
            "data": result
        })

    # Aggregate (example: sum numerical fields)
    aggregated = {}
    for field in schema.keys():
        if schema[field] in [int, float]:
            aggregated[field] = sum(
                r["data"].get(field, 0) for r in all_results
            )
        elif schema[field] == list:
            aggregated[field] = []
            for r in all_results:
                if field in r["data"]:
                    aggregated[field].extend(r["data"][field])

    return aggregated, all_results
```

### 2. Confidence-Based Extraction

```python
def extract_with_confidence(field_name, field_schema, context):
    """
    Extract with confidence scoring
    """
    import openai
    import json

    client = openai.OpenAI()

    prompt = f"""
Extract "{field_name}" from the context below.

Expected type: {field_schema}

Context:
{context}

Return JSON with:
{{
    "value": <extracted value>,
    "confidence": <0.0 to 1.0>,
    "reasoning": <brief explanation>,
    "alternative_values": [<other possible values if uncertain>]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
```

### 3. Schema Evolution

Handle schema changes over time:

```python
class EvolvingSchemaExtractor:
    def __init__(self, schema_versions):
        """
        schema_versions: dict of {version: schema}
        """
        self.schema_versions = schema_versions

    def detect_schema_version(self, document_tree):
        """
        Automatically detect which schema version to use
        """
        import openai
        import json

        # Get document characteristics
        sections = [node['title'] for node in self._flatten_tree(document_tree)]

        client = openai.OpenAI()
        prompt = f"""
Given these document sections, which schema version best matches?

Sections:
{chr(10).join(sections)}

Available schema versions:
{list(self.schema_versions.keys())}

Return: {{"version": "<version_name>"}}
"""

        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        result = json.loads(response.choices[0].message.content)
        return result["version"]

    def extract_with_auto_version(self, pdf_path):
        """
        Extract with automatic schema version detection
        """
        from pageindex import page_index

        # Index document
        result = page_index(doc=pdf_path, if_add_node_summary="yes", if_add_node_text="yes")
        document_tree = result['structure']

        # Detect version
        version = self.detect_schema_version(document_tree)
        print(f"📋 Detected schema version: {version}")

        # Extract with correct schema
        schema = self.schema_versions[version]
        extractor = SchemaGuidedExtractor(schema)
        # ... continue extraction
```

### 4. Interactive Refinement

```python
def interactive_extraction(pdf_path, schema):
    """
    Allow user to refine extraction interactively
    """
    extractor = SchemaGuidedExtractor(schema)
    result = (extractor
        .index_document(pdf_path)
        .map_schema_to_tree()
        .extract())

    # Review and refine
    while True:
        print("\n📊 Current extraction:")
        for field, value in result.items():
            print(f"  {field}: {value}")

        field_to_fix = input("\nEnter field to refine (or 'done'): ").strip()

        if field_to_fix.lower() == 'done':
            break

        if field_to_fix in result:
            print(f"\n🔍 Re-extracting {field_to_fix}...")
            # Re-extract with user guidance
            user_hint = input("Provide hint/context: ")
            new_value = re_extract_field(
                field_to_fix,
                schema[field_to_fix],
                extractor.document_tree,
                hint=user_hint
            )
            result[field_to_fix] = new_value
            print(f"✓ Updated to: {new_value}")

    return result
```

---

## Performance Optimization

### Reduce API Calls

```python
# Bad: Extract each field individually
for field in schema:
    value = extract_field(field, document_tree)  # N API calls

# Good: Batch extract related fields
financial_fields = ["revenue", "expenses", "profit"]
financial_data = batch_extract_fields(
    financial_fields,
    document_tree
)  # 1 API call
```

### Parallel Extraction

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_schema_extraction(schema, document_tree):
    """
    Extract multiple fields in parallel
    """
    async def extract_field_async(field, field_schema):
        # Async extraction logic
        return await extract_field(field, field_schema, document_tree)

    # Create tasks
    tasks = [
        extract_field_async(field, field_schema)
        for field, field_schema in schema.items()
    ]

    # Execute in parallel
    results = await asyncio.gather(*tasks)

    # Combine results
    return dict(zip(schema.keys(), results))
```

---

## Advanced: Multi-Level Nested JSON Extraction

### The Complex Nested Schema Challenge

**Problem:** You have a 200-page document and need to extract a complex nested structure like:

```python
complex_schema = {
    "processes": [
        {
            "process_id": str,
            "process_name": str,
            "description": str,
            "operations": [
                {
                    "operation_id": str,
                    "operation_name": str,
                    "items": [
                        {
                            "item_id": str,
                            "item_name": str,
                            "properties": {...}
                        }
                    ]
                }
            ]
        }
    ]
}
```

**Challenge:** Maintaining accurate relationships across 3+ levels of nesting with hundreds of entities.

---

### Strategy: Hierarchical Extraction with Relationship Tracking

This algorithm extracts nested structures in phases, maintaining parent-child relationships:

```python
class HierarchicalExtractor:
    """
    Multi-level nested extraction with relationship tracking
    """

    def __init__(self, schema, model="gpt-4o-2024-11-20"):
        self.schema = schema
        self.model = model
        self.document_tree = None
        self.extraction_map = {}  # Track what's extracted where

    def extract_nested_structure(self, pdf_path):
        """
        Main orchestrator for hierarchical extraction
        """
        from pageindex import page_index

        # Phase 1: Index document
        print("📄 Phase 1: Indexing document...")
        result = page_index(
            doc=pdf_path,
            model=self.model,
            if_add_node_summary="yes",
            if_add_node_text="yes"
        )
        self.document_tree = result['structure']

        # Phase 2: Discover entity locations
        print("\n🔍 Phase 2: Discovering entity locations...")
        entity_map = self._discover_entity_locations()

        # Phase 3: Extract top-level entities (processes)
        print("\n📊 Phase 3: Extracting top-level entities...")
        processes = self._extract_top_level_entities(entity_map)

        # Phase 4: Extract nested children recursively
        print("\n🔗 Phase 4: Extracting nested relationships...")
        complete_structure = self._extract_nested_children(processes, entity_map)

        # Phase 5: Validate and reconcile
        print("\n✅ Phase 5: Validating relationships...")
        validated_structure = self._validate_relationships(complete_structure)

        return validated_structure

    def _discover_entity_locations(self):
        """
        Discover where each entity type is located in the document
        Uses LLM to identify patterns and locations
        """
        import openai
        import json

        client = openai.OpenAI()

        # Build section index
        sections = self._flatten_tree_with_metadata(self.document_tree)

        prompt = f"""
Analyze this document structure and identify where different entity types are located.

Document sections:
{json.dumps(sections[:50], indent=2)}  # Show first 50 sections

Entity types to find:
1. Processes (top-level entities)
2. Operations (nested under processes)
3. Items (nested under operations)

For each entity type, identify:
- Which sections contain them
- How they're structured (tables, lists, paragraphs)
- Identifying patterns (headers, numbering, keywords)
- Relationship indicators (how children link to parents)

Return JSON:
{{
    "processes": {{
        "node_ids": ["list of node IDs containing processes"],
        "pattern": "description of how processes appear",
        "identifiers": ["keywords or patterns that mark processes"],
        "count_estimate": <estimated number of processes>
    }},
    "operations": {{
        "node_ids": ["list of node IDs containing operations"],
        "pattern": "description of how operations appear",
        "parent_link_pattern": "how operations link to processes",
        "count_estimate": <estimated number>
    }},
    "items": {{
        "node_ids": ["list of node IDs containing items"],
        "pattern": "description of how items appear",
        "parent_link_pattern": "how items link to operations",
        "count_estimate": <estimated number>
    }},
    "extraction_strategy": "recommended strategy (table-based, list-based, paragraph-based)"
}}
"""

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        entity_map = json.loads(response.choices[0].message.content)

        print(f"  ✓ Found ~{entity_map['processes']['count_estimate']} processes")
        print(f"  ✓ Found ~{entity_map['operations']['count_estimate']} operations")
        print(f"  ✓ Found ~{entity_map['items']['count_estimate']} items")
        print(f"  ✓ Strategy: {entity_map['extraction_strategy']}")

        return entity_map

    def _extract_top_level_entities(self, entity_map):
        """
        Extract all top-level processes with metadata for child extraction
        """
        import openai
        import json

        client = openai.OpenAI()
        processes = []

        # Get relevant sections
        process_nodes = self._get_nodes_by_ids(entity_map['processes']['node_ids'])

        # Extract processes from each relevant section
        for node in process_nodes:
            prompt = f"""
Extract all PROCESSES from this section. Each process should include identifiers for finding its child operations.

Section: {node['title']}
Content:
{node.get('text', '')[:8000]}  # Limit context

Patterns to look for:
{entity_map['processes']['pattern']}
Identifiers:
{entity_map['processes']['identifiers']}

Return JSON array:
[
    {{
        "process_id": "unique identifier",
        "process_name": "name",
        "description": "description",
        "location_hint": "page numbers, section numbers, or keywords for finding operations",
        "source_node_id": "{node['node_id']}",
        "page_range": "{node.get('start_index', 0)}-{node.get('end_index', 0)}"
    }}
]
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            extracted = json.loads(response.choices[0].message.content)
            processes.extend(extracted)
            print(f"  ✓ Extracted {len(extracted)} processes from {node['title']}")

        return processes

    def _extract_nested_children(self, parent_entities, entity_map):
        """
        Recursively extract children for each parent entity
        """
        import openai
        import json

        client = openai.OpenAI()

        for process in parent_entities:
            print(f"\n  🔄 Processing: {process['process_name']}")

            # Find sections likely containing this process's operations
            operation_nodes = self._find_related_sections(
                process,
                entity_map['operations']
            )

            # Extract operations for this specific process
            operations = []
            for node in operation_nodes:
                prompt = f"""
Extract OPERATIONS that belong to the process: "{process['process_name']}" (ID: {process['process_id']})

Section: {node['title']}
Content:
{node.get('text', '')[:8000]}

Parent process context:
- Process ID: {process['process_id']}
- Process Name: {process['process_name']}
- Location hint: {process.get('location_hint', '')}

Extraction rules:
1. Only extract operations that clearly belong to this process
2. Look for: {entity_map['operations']['pattern']}
3. Link pattern: {entity_map['operations']['parent_link_pattern']}

Return JSON array:
[
    {{
        "operation_id": "unique identifier",
        "operation_name": "name",
        "description": "description",
        "parent_process_id": "{process['process_id']}",
        "location_hint": "hints for finding items",
        "source_node_id": "{node['node_id']}"
    }}
]

If no operations for this process in this section, return empty array [].
"""

                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )

                extracted = json.loads(response.choices[0].message.content)
                operations.extend(extracted)

            print(f"    ✓ Found {len(operations)} operations")

            # Extract items for each operation (third level)
            for operation in operations:
                items = self._extract_items_for_operation(operation, entity_map)
                operation['items'] = items
                print(f"      ✓ Found {len(items)} items for {operation['operation_name']}")

            process['operations'] = operations

        return parent_entities

    def _extract_items_for_operation(self, operation, entity_map):
        """
        Extract items (deepest level) for a specific operation
        """
        import openai
        import json

        client = openai.OpenAI()

        # Find sections containing this operation's items
        item_nodes = self._find_related_sections(
            operation,
            entity_map['items']
        )

        items = []
        for node in item_nodes:
            prompt = f"""
Extract ITEMS that belong to operation: "{operation['operation_name']}" (ID: {operation['operation_id']})

Section: {node['title']}
Content:
{node.get('text', '')[:6000]}

Parent context:
- Operation ID: {operation['operation_id']}
- Operation Name: {operation['operation_name']}
- Process: {operation.get('parent_process_id', '')}

Extraction rules:
1. Only extract items belonging to this specific operation
2. Look for: {entity_map['items']['pattern']}
3. Link pattern: {entity_map['items']['parent_link_pattern']}

Return JSON array:
[
    {{
        "item_id": "unique identifier",
        "item_name": "name",
        "properties": {{
            // any relevant properties
        }},
        "parent_operation_id": "{operation['operation_id']}"
    }}
]

If no items found, return [].
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            extracted = json.loads(response.choices[0].message.content)
            items.extend(extracted)

        return items

    def _validate_relationships(self, structure):
        """
        Validate that all parent-child relationships are correct
        """
        print("\n  🔍 Validating relationships...")

        total_operations = 0
        total_items = 0
        orphaned_operations = []
        orphaned_items = []

        # Build ID maps
        process_ids = {p['process_id'] for p in structure}

        for process in structure:
            operation_ids = set()

            for operation in process.get('operations', []):
                total_operations += 1

                # Check if operation links to valid process
                if operation.get('parent_process_id') != process['process_id']:
                    orphaned_operations.append(operation)

                operation_ids.add(operation['operation_id'])

                # Check items
                for item in operation.get('items', []):
                    total_items += 1

                    # Check if item links to valid operation
                    if item.get('parent_operation_id') != operation['operation_id']:
                        orphaned_items.append(item)

        print(f"  ✓ Total processes: {len(structure)}")
        print(f"  ✓ Total operations: {total_operations}")
        print(f"  ✓ Total items: {total_items}")

        if orphaned_operations:
            print(f"  ⚠️  Found {len(orphaned_operations)} orphaned operations - attempting reconciliation...")
            structure = self._reconcile_orphans(structure, orphaned_operations, 'operation')

        if orphaned_items:
            print(f"  ⚠️  Found {len(orphaned_items)} orphaned items - attempting reconciliation...")
            structure = self._reconcile_orphans(structure, orphaned_items, 'item')

        return structure

    def _reconcile_orphans(self, structure, orphans, entity_type):
        """
        Use LLM to reconcile orphaned entities with correct parents
        """
        import openai
        import json

        client = openai.OpenAI()

        # Build parent map
        if entity_type == 'operation':
            parent_map = {p['process_id']: p['process_name'] for p in structure}
        else:  # items
            parent_map = {}
            for p in structure:
                for op in p.get('operations', []):
                    parent_map[op['operation_id']] = op['operation_name']

        for orphan in orphans:
            prompt = f"""
This {entity_type} seems to have incorrect parent linkage. Help identify the correct parent.

Orphan {entity_type}:
{json.dumps(orphan, indent=2)}

Available parents:
{json.dumps(parent_map, indent=2)}

Based on the {entity_type}'s name, description, and context, which parent does it most likely belong to?

Return JSON:
{{
    "correct_parent_id": "ID of correct parent",
    "confidence": 0.0-1.0,
    "reasoning": "why this parent makes sense"
}}
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            result = json.loads(response.choices[0].message.content)

            if result['confidence'] > 0.7:
                if entity_type == 'operation':
                    orphan['parent_process_id'] = result['correct_parent_id']
                else:
                    orphan['parent_operation_id'] = result['correct_parent_id']
                print(f"    ✓ Reconciled: {orphan.get(f'{entity_type}_name', 'unnamed')}")

        return structure

    def _find_related_sections(self, parent_entity, child_entity_map):
        """
        Find document sections most likely containing children of this parent
        """
        import openai
        import json

        # Get candidate nodes
        candidate_nodes = self._get_nodes_by_ids(child_entity_map['node_ids'])

        # Use location hints to narrow down
        location_hint = parent_entity.get('location_hint', '')
        page_range = parent_entity.get('page_range', '')

        # Filter by proximity if page range is available
        if page_range:
            try:
                start, end = map(int, page_range.split('-'))
                # Get nodes within +/- 20 pages
                candidate_nodes = [
                    n for n in candidate_nodes
                    if abs(n.get('start_index', 0) - start) <= 20
                ]
            except:
                pass

        return candidate_nodes[:5]  # Limit to top 5 most relevant

    def _flatten_tree_with_metadata(self, nodes, result=None):
        """
        Flatten tree structure with full metadata
        """
        if result is None:
            result = []

        for node in nodes:
            result.append({
                'node_id': node.get('node_id', ''),
                'title': node.get('title', ''),
                'summary': node.get('summary', ''),
                'start_index': node.get('start_index', 0),
                'end_index': node.get('end_index', 0),
                'level': node.get('level', 0)
            })

            if node.get('nodes'):
                self._flatten_tree_with_metadata(node['nodes'], result)

        return result

    def _get_nodes_by_ids(self, node_ids):
        """
        Retrieve full node data by IDs
        """
        def find_nodes(tree, target_ids):
            results = []
            for node in tree:
                if node.get('node_id') in target_ids:
                    results.append(node)
                if node.get('nodes'):
                    results.extend(find_nodes(node['nodes'], target_ids))
            return results

        return find_nodes(self.document_tree, node_ids)
```

### Usage Example

```python
# Define your complex nested schema
schema = {
    "processes": [
        {
            "process_id": str,
            "process_name": str,
            "description": str,
            "operations": [
                {
                    "operation_id": str,
                    "operation_name": str,
                    "description": str,
                    "items": [
                        {
                            "item_id": str,
                            "item_name": str,
                            "properties": dict
                        }
                    ]
                }
            ]
        }
    ]
}

# Extract the complete nested structure
extractor = HierarchicalExtractor(schema)
result = extractor.extract_nested_structure("200_page_document.pdf")

# Save to file
import json
with open("complete_extraction.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"\n✅ Extraction complete!")
print(f"Total processes: {len(result)}")
print(f"Total operations: {sum(len(p['operations']) for p in result)}")
print(f"Total items: {sum(sum(len(op['items']) for op in p['operations']) for p in result)}")
```

### Output Format

```json
[
  {
    "process_id": "P001",
    "process_name": "Manufacturing Process A",
    "description": "Primary manufacturing workflow",
    "operations": [
      {
        "operation_id": "OP001",
        "operation_name": "Assembly Operation",
        "parent_process_id": "P001",
        "items": [
          {
            "item_id": "ITEM001",
            "item_name": "Component X",
            "parent_operation_id": "OP001",
            "properties": {
              "quantity": 100,
              "unit": "pieces"
            }
          }
        ]
      }
    ]
  }
]
```

### Key Algorithm Features

1. **📍 Location Discovery**: Intelligently identifies where each entity type lives in the document
2. **🎯 Contextual Extraction**: Extracts children with parent context to maintain relationships
3. **🔗 Relationship Tracking**: Uses ID linking at every level (process_id → operation → item)
4. **✅ Validation & Reconciliation**: Detects and fixes orphaned entities
5. **📊 Progress Tracking**: Shows extraction progress at each level
6. **🎨 Adaptive Strategy**: LLM determines best extraction approach (tables, lists, paragraphs)

### Performance Optimization

```python
# For very large documents, use parallel extraction
import asyncio

async def parallel_process_extraction(processes, entity_map):
    """
    Extract operations for multiple processes in parallel
    """
    async def extract_operations_async(process):
        # Async extraction logic
        return await extract_operations_for_process(process, entity_map)

    tasks = [extract_operations_async(p) for p in processes]
    results = await asyncio.gather(*tasks)

    for process, operations in zip(processes, results):
        process['operations'] = operations

    return processes
```

---

## Summary

**Key Takeaways:**

1. ✅ **Use PageIndex for Navigation** - Let it find relevant sections
2. ✅ **Schema Guides Extraction** - Clear schema = better results
3. ✅ **Validate and Refine** - Iterative extraction improves accuracy
4. ✅ **Cache Aggressively** - Avoid re-processing same documents
5. ✅ **Batch Related Fields** - Reduce API calls and costs
6. ✅ **Hierarchical Extraction** - Extract nested structures level-by-level with relationship tracking

**When to Use Schema-Driven Extraction:**

- ✅ You have a clear expected structure
- ✅ Document exceeds LLM context limits
- ✅ Need high accuracy and validation
- ✅ Processing multiple similar documents
- ✅ Want to minimize manual review

**When to Use Alternative Approaches:**

- ❌ Document is small (<10 pages)
- ❌ Schema is unknown or highly variable
- ❌ Need exploratory analysis
- ❌ Real-time/streaming extraction required

---

## Next Steps

1. Try the complete examples with your documents
2. Adapt the `SchemaGuidedExtractor` to your use case
3. Experiment with different extraction strategies
4. Implement caching and QA checks
5. Share your results with the community!

**Need help?** Join our [Discord](https://discord.com/invite/VuXuf29EUj) or check the [main documentation](README.md).

Happy extracting! 🎯
