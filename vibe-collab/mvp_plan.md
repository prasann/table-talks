# 📋 TableTalk MVP Implementation Plan

## 🎯 Project Overview
**TableTalk** - A conversational EDA assistant that enables natural language exploration of data schemas using a local SLM.

---

## 🏗️ MVP Scope & Components

### Core Features (MVP)
- [x] Schema extraction from CSV/Parquet files
- [x] Metadata storage in DuckDB
- [x] Basic tool functions for schema queries
- [x] LangChain agent with local SLM (Phi-3 via Ollama)
- [x] CLI chat interface

### Out of Scope (Future Phases)
- Web interface
- Advanced visualizations
- Embedding-based context
- Cross-file relationship detection
- Data quality scoring

---

## 📁 Project Structure

```
table-talk/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── schema_extractor.py     # Extract schemas from files
│   │   └── metadata_store.py       # DuckDB operations
│   ├── tools/
│   │   ├── __init__.py
│   │   └── schema_tools.py         # Tool functions for LangChain
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── context_manager.py      # Intent detection & context filtering
│   │   └── llm_agent.py           # LangChain + Ollama integration
│   ├── cli/
│   │   ├── __init__.py
│   │   └── chat_interface.py       # CLI chat loop
│   └── main.py                     # Entry point
├── tests/
│   ├── __init__.py
│   ├── test_schema_extractor.py
│   ├── test_metadata_store.py
│   └── test_tools.py
└── data/
    └── sample/                     # Sample CSV/Parquet files for testing
```

---

## � Docker Strategy

### Approach: Single Container (MVP)
For the MVP, we'll use a **single Docker image** containing:
- Python runtime with all dependencies
- Ollama with Phi-3 model pre-installed
- DuckDB (file-based, no separate container needed)
- TableTalk application

### Docker Structure
```
table-talk/
├── Dockerfile
├── docker-compose.yml          # For easy local development
├── .dockerignore
├── docker/
│   ├── entrypoint.sh          # Startup script
│   └── ollama-setup.sh        # Ollama initialization
└── ...
```

### Container Configuration
```dockerfile
# Dockerfile highlights:
FROM python:3.11-slim

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Pre-pull Phi-3 model during build
RUN ollama serve & sleep 10 && ollama pull phi3:mini

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY src/ /app/src/
WORKDIR /app

# Start both Ollama and TableTalk
CMD ["./docker/entrypoint.sh"]
```

### Usage
```bash
# Build and run
docker-compose up --build

# Or direct Docker
docker build -t tabletalk .
docker run -it -v $(pwd)/data:/app/data tabletalk
```

### Alternative: Multi-Container Setup (Future)
```yaml
# docker-compose.yml for production
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
  
  tabletalk:
    build: .
    depends_on: [ollama]
    volumes:
      - ./data:/app/data
      - ./database:/app/database
```

---

## �🗄️ Database Schema

```sql
-- DuckDB schema for metadata storage
CREATE TABLE schema_info (
    id INTEGER PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    null_count INTEGER,
    unique_count INTEGER,
    total_rows INTEGER,
    file_size_mb REAL,
    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_file_name ON schema_info(file_name);
CREATE INDEX idx_column_name ON schema_info(column_name);
```

---

## 🛠️ Implementation Tasks

### Phase 1: Core Infrastructure (Days 1-2)
1. **Project Setup**
   - [ ] Initialize Python project with proper structure
   - [ ] Create `requirements.txt` with dependencies
   - [ ] Set up basic configuration management
   - [ ] Create sample data files for testing
   - [ ] Create Dockerfile and docker-compose.yml
   - [ ] Set up Docker build and entry scripts

2. **Metadata Storage**
   - [ ] Implement `MetadataStore` class with DuckDB
   - [ ] Create database schema and connection management
   - [ ] Add basic CRUD operations for schema_info

3. **Schema Extraction**
   - [ ] Implement `SchemaExtractor` for CSV files
   - [ ] Implement `SchemaExtractor` for Parquet files
   - [ ] Add file scanning and batch processing
   - [ ] Handle common data type detection

### Phase 2: Tool Functions (Days 3-4)
4. **Core Tools**
   - [ ] `get_schema(file_name)` - Return schema for specific file
   - [ ] `list_files()` - Show all scanned files
   - [ ] `detect_type_mismatches()` - Find columns with different types
   - [ ] `find_common_columns()` - Find shared columns across files
   - [ ] `summarize_file(file_name)` - Basic file statistics

5. **Tool Integration**
   - [ ] Create LangChain tool wrappers
   - [ ] Add proper error handling and validation
   - [ ] Implement tool result formatting

### Phase 3: LLM Agent (Days 5-6)
6. **Context Management**
   - [ ] Implement intent detection (keyword-based)
   - [ ] Create context filtering for token limits
   - [ ] Add query preprocessing

7. **LLM Integration**
   - [ ] Set up Ollama client connection
   - [ ] Configure Phi-3 model
   - [ ] Implement LangChain agent with tools
   - [ ] Add conversation memory management

### Phase 4: CLI Interface (Day 7)
8. **Chat Interface**
   - [ ] Create interactive CLI loop
   - [ ] Add command parsing (`/scan`, `/help`, `/exit`)
   - [ ] Implement file scanning commands
   - [ ] Add basic error handling and user feedback

9. **Integration & Testing**
   - [ ] End-to-end testing with sample data
   - [ ] Performance testing with larger files
   - [ ] User experience refinements
   - [ ] Docker image testing and optimization
   - [ ] Create Docker deployment documentation

---

## 📦 Dependencies

### Python Requirements
```txt
# Core dependencies
duckdb>=0.9.0
pandas>=2.0.0
pyarrow>=10.0.0  # For Parquet support
langchain>=0.1.0
langchain-community>=0.0.20
ollama>=0.1.7
pyyaml>=6.0
click>=8.0.0     # For CLI interface

# Development dependencies
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

### Docker Files
- `Dockerfile` - Multi-stage build with Python + Ollama
- `docker-compose.yml` - Local development setup
- `.dockerignore` - Exclude unnecessary files from build context
- `docker/entrypoint.sh` - Container startup script
- `docker/ollama-setup.sh` - Ollama model initialization

---

## 🧪 Example Usage Scenarios

### Initial Setup
```bash
# Start TableTalk
python src/main.py

# Scan data directory
TableTalk> /scan data/
Scanning 15 files... ✓
Found 3 CSV files, 2 Parquet files
Schemas extracted and stored.

# Start conversation
TableTalk> What files do we have?
```

### Sample Conversations
```
You> Show me the schema of orders.csv
Assistant> The orders.csv file has 8 columns:
- order_id (int64): 1,250 unique values, 0 nulls
- customer_id (int64): 892 unique values, 0 nulls
- product_name (string): 45 unique values, 0 nulls
- quantity (int64): 12 unique values, 0 nulls
...

You> Which files have a user_id column?
Assistant> I found user_id columns in 3 files:
1. customers.csv (data_type: int64)
2. orders.csv (data_type: string) ⚠️ Type mismatch!
3. reviews.parquet (data_type: int64)

You> Find data type inconsistencies
Assistant> Found 2 type mismatches:
1. user_id: int64 in customers.csv, string in orders.csv
2. created_date: datetime in orders.csv, string in reviews.parquet
```

---

## 🎯 Success Criteria

### Functional Requirements
- [ ] Successfully extract schemas from CSV and Parquet files
- [ ] Store and query metadata efficiently
- [ ] Answer basic schema questions via natural language
- [ ] Handle files up to 100MB without performance issues
- [ ] Maintain conversation context within a session

### Performance Requirements
- [ ] Schema extraction: < 5 seconds for files up to 10MB
- [ ] Query response: < 3 seconds for simple questions
- [ ] Memory usage: < 500MB for typical datasets

### User Experience
- [ ] Intuitive CLI commands and responses
- [ ] Clear error messages and guidance
- [ ] Helpful suggestions for common queries

---

## 🚀 Getting Started

### Option 1: Docker (Recommended)
```bash
# Clone and navigate to project
cd table-talk

# Build and run with Docker Compose
docker-compose up --build

# Or build and run Docker directly
docker build -t tabletalk .
docker run -it -v $(pwd)/data:/app/data tabletalk

# Access the CLI inside container
docker exec -it tabletalk_app_1 python src/main.py
```

### Option 2: Local Development
1. **Environment Setup**
   ```bash
   cd table-talk
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

2. **Install Ollama & Phi-3**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve &
   
   # Pull Phi-3 model
   ollama pull phi3:mini
   ```

3. **Run TableTalk**
   ```bash
   python src/main.py
   ```

### Data Volume Mounting
```bash
# Mount your data directory to container
docker run -it \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/database:/app/database \
  tabletalk
```

---

## 📝 Notes

### Development
- Start with small sample files (< 1MB) for initial testing
- Use Phi-3:mini for faster responses during development
- Implement basic logging for debugging
- Keep tool functions simple and focused for MVP
- Plan for easy extension in future phases

### Docker Considerations
- Single container approach keeps MVP simple
- Pre-pull Phi-3 model during image build to reduce startup time
- Use multi-stage builds to minimize final image size
- Mount data and database directories as volumes for persistence
- Consider using .dockerignore to exclude test data from build context
- Future: Split into microservices (Ollama + TableTalk) for production scaling

---

**Ready for implementation! 🎉**
