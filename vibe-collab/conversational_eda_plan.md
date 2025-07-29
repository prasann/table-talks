
# 🧠 Conversational EDA Assistant (CLI + Local SLM)

## 🔍 Problem Statement

Our datasets are spread across multiple files (CSV, Parquet, etc.), each representing different tables. Manually inspecting their schemas, understanding commonalities, detecting inconsistencies, and exploring anomalies is time-consuming.

We want to build a **Python-based CLI assistant**, backed by a **local Small Language Model (SLM)**, that enables **natural language exploration of data schemas**.

---

## 🎯 Goals

- Extract and store schema metadata across files
- Identify:
  - Schema mismatches (e.g., `user_id` as int in one file, str in another)
  - Schema commonalities (shared columns across files)
  - Outliers in data types or null distributions
- Enable **natural language questions** via CLI chat
- All processing is **local-first**, with optional future cloud integration

---

## 🧱 Architecture Overview

```
                ┌────────────────────┐
                │   CLI Chat Loop    │
                └────────┬───────────┘
                         ↓
                ┌────────────────────┐
                │   SLM Agent Layer  │  ← Uses LangChain + Ollama
                └────────┬───────────┘
                         ↓
                ┌────────────────────┐
                │  Context Manager   │  ← Selects only relevant info
                └────────┬───────────┘
                         ↓
              ┌────────────────────────┐
              │ Tool Layer (Python fns)│  ← get_schema(), detect_mismatch()
              └────────┬───────────────┘
                       ↓
         ┌──────────────────────────────┐
         │ Metadata Store (DuckDB/SQLite)│  ← schema_info table
         └──────────────────────────────┘
```

---

## 🧰 Components

### 1. Metadata Store

Scans `.csv` or `.parquet` files. Extracts:
- `file_name`, `column_name`, `data_type`, `null_count`, `unique_count`
- Stores in `schema_info` table in DuckDB

```sql
CREATE TABLE schema_info (
  file_name TEXT,
  column_name TEXT,
  dtype TEXT,
  nulls INT,
  uniques INT
);
```

### 2. Tool Layer

Python functions:
- `get_schema(file_name)`
- `detect_type_mismatches()`
- `find_common_columns()`
- `summarize_file(file_name)`

### 3. Context Manager

Parses user intent → selects relevant tool → summarizes data within model's context window.

Example:
```python
if "schema" in query:
    return get_schema(file_name)
elif "outlier" in query:
    return detect_type_mismatches()
```

### 4. SLM Agent (LangChain + Ollama)

- Loads a local model (`phi3`, `mistral`, etc.)
- Uses `initialize_agent()` with tool functions

### 5. CLI Interface

```python
def chat():
    while True:
        q = input("You> ")
        if q in ["exit", "quit"]: break
        print("Assistant>", agent.run(q))
```

---

## 🔄 Example Queries

- "Show me the schema of `orders.csv`"
- "Which files have a `user_id` column?"
- "Find inconsistent data types across files"

---

## 🚀 Future Extensions

| Feature | Approach |
|--------|----------|
| Embedding-based context | Use FAISS or Chroma with column metadata |
| Visualization | Plotly / textual plots |
| Web interface | Streamlit layer |
| Smart memory | Keep multi-turn session context |
| Autocomplete | LLM-generated rephrasing |

---

## ✅ Summary

This is a **schema-aware, conversational EDA system** running fully locally. Key pieces include:
- DuckDB metadata registry
- Tool-based Python functions
- Context Manager to filter prompt size
- Local SLM agent to handle logic + chat

---

## 🛠 Next Steps

- [ ] Build schema scanner into DuckDB
- [ ] Implement first 3 tools
- [ ] Wrap tools into LangChain agent
- [ ] Build CLI loop and test with Phi-3 via Ollama
- [ ] Discuss with team for iterations
