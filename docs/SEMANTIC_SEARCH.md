# Semantic Search User Guide

TableTalk now includes powerful semantic search capabilities that understand the meaning behind your queries, not just exact text matches.

## 🎯 What is Semantic Search?

Semantic search uses AI to understand the **meaning** of your queries, allowing you to find related columns even when they don't have exact name matches.

### Traditional vs Semantic Search

| **Traditional Search** | **Semantic Search** |
|----------------------|-------------------|
| "customer" → finds only `customer_id` | "user identifier" → finds `user_id`, `customer_id`, `review_id` |
| "timestamp" → no results | "timestamps" → finds `created_date`, `order_date`, `signup_date` |
| Exact substring matching | Intelligent concept understanding |

## 🚀 How to Use Semantic Search

### Automatic Activation
The AI agent automatically enables semantic search when you use phrases like:
- "semantically"
- "semantic search"  
- "semantic analysis"
- "find similar"
- "related columns"

### Examples

```bash
# These automatically use semantic search:
search for user identifiers using semantic analysis
find timestamp columns with semantic search
search metadata for customer related fields semantically

# These use traditional search:
search customer
find columns containing "date"
```

### Manual Control
For advanced users, semantic search can be controlled via function parameters:
```python
search_metadata("user identifier", semantic=True)
find_relationships(analysis_type="similar_schemas", semantic=True)
detect_inconsistencies(check_type="semantic_naming")
```

## 🔍 Enhanced Search Capabilities

### 1. Smart Column Discovery
Find columns by concept, not just name:

```bash
Query: "find user identifiers"
Results:
📍 reviews.csv → user_id (similarity: 0.679)
📍 customers.csv → customer_id (similarity: 0.593)
```

### 2. Temporal Column Detection
Discover all date/time related columns:

```bash  
Query: "show me timestamp columns"
Results:
📍 reviews.csv → created_date (similarity: 0.687)
📍 orders.csv → order_date (similarity: 0.676)  
📍 customers.csv → signup_date (similarity: 0.596)
```

### 3. Concept-Based Grouping
Group columns by semantic concepts:

```bash
Query: "group columns by semantic concepts"
Results:
IDENTIFIERS (4 columns):
• reviews.csv: user_id (0.892)
• customers.csv: customer_id (0.878)
• orders.csv: order_id (0.845)

TIMESTAMPS (3 columns):  
• reviews.csv: created_date (0.911)
• orders.csv: order_date (0.887)
```

## 🔧 Advanced Semantic Analysis

### Schema Similarity Analysis
Find files with conceptually similar structures:

```bash
Query: "find similar schemas using semantic analysis"
```

### Naming Inconsistency Detection  
Identify similar concepts with different names:

```bash
Query: "detect semantic naming inconsistencies"
Results:
⚠️ IDENTIFIER CONCEPT (similarity: 0.832)
Suggested name: user_id
Current variations:
• reviews.csv: user_id
• customers.csv: customer_id  
```

### Abbreviation Detection
Find abbreviated vs full column names:

```bash
Query: "detect abbreviation inconsistencies"
Results:
📝 cust_id ↔ customer_id (similarity: 0.891)
Files: legacy.csv → customers.csv
Suggestion: Use consistent naming (customer_id)
```

## 📊 Understanding Similarity Scores

Semantic search provides similarity scores (0.0 to 1.0):

- **0.9-1.0**: 🎯 Very high confidence match
- **0.7-0.9**: 📍 Good semantic match  
- **0.6-0.7**: 📍 Moderate match
- **Below 0.6**: Usually filtered out

## ⚡ Performance & Availability

### First Use
- Model downloads automatically (~80MB)
- Initial loading takes ~5 seconds
- Subsequent queries are fast (<50ms)

### Fallback Behavior
- If semantic models aren't available, falls back to traditional search
- No functionality is lost
- Graceful error handling

### Memory Usage
- Adds ~200MB RAM when semantic model is loaded
- Model stays loaded for session efficiency
- Column embeddings are cached for speed

## 🛠️ Installation Requirements

Semantic search requires optional dependencies:

```bash
pip install sentence-transformers scikit-learn
```

If not installed, TableTalk works normally with traditional search only.

## 💡 Tips for Best Results

### 1. Use Descriptive Terms
Instead of: "find id"  
Try: "find user identifiers" or "show me primary keys"

### 2. Think Conceptually  
Instead of: "columns with date"
Try: "timestamp columns" or "temporal fields"

### 3. Leverage Natural Language
- "customer related columns"
- "financial fields"  
- "status indicators"
- "rating columns"

### 4. Combine with Traditional Search
Use semantic search for discovery, traditional for precision:

```bash
# Discover concept
search for user identifiers semantically

# Then get exact matches  
search customer_id
```

## 🚨 Troubleshooting

### No Semantic Results
If semantic search returns no results:
1. Check similarity threshold (default 0.6)
2. Try broader terms ("identifiers" vs "user id")
3. System automatically falls back to traditional search

### Performance Issues  
If queries seem slow:
1. First query loads model (5s), subsequent queries are fast
2. Restart application to reload model if needed
3. Traditional search is always available as backup

### Missing Dependencies
If you see "Semantic analysis not available":
```bash
pip install sentence-transformers scikit-learn
```

## 🎉 Getting Started

Try these example queries to explore semantic capabilities:

```bash
# Start with scanning your data
/scan data/your-directory

# Try semantic searches
search for user identifiers using semantic analysis
find all timestamp related columns  
show me customer related fields semantically
detect naming inconsistencies across files
group columns by semantic concepts
```

Semantic search opens up powerful new ways to explore and understand your data structure through intelligent, meaning-based analysis!
