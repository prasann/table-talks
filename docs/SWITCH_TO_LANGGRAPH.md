# Switch to LangGraph: Complete Migration Plan

## Executive Summary

This document outlines the complete migration of TableTalk from custom function calling orchestration to LangGraph-based workflows. The migration will solve sequential function calling issues, enable multi-agent architecture, and support both local (Ollama) and cloud (OpenAI GPT) model integration.

---

## Part I: Design & Architecture

### Current State Analysis

#### Problems to Solve
1. **Sequential Function Calling Bug**: LLM generates correct patterns but execution fails with placeholder resolution
2. **Architecture Limitations**: Manual orchestration makes adding new features difficult  
3. **Scalability Issues**: Hard to add new agents or workflow types
4. **Limited Model Flexibility**: Currently locked to single Ollama model

#### Existing Assets to Preserve
- ✅ **Clean 4-layer design** (CLI → Agent → Tools → Data)
- ✅ **8 well-designed tools** across 4 organized files
- ✅ **DuckDB metadata storage** system
- ✅ **Rich CLI interface** with export capabilities
- ✅ **YAML configuration** system
- ✅ **Strategy pattern implementation** (searchers, analyzers, formatters)
- ✅ **Comprehensive setup** scripts

### Target Architecture Design

#### Multi-Agent System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Schema Agent  │    │ Code Gen Agent  │    │ Orchestrator    │
│   (Ollama)      │    │ (GPT/Ollama)    │    │ (Meta-Agent)    │
│                 │    │                 │    │                 │
│ • Schema explore│    │ • Python scripts│    │ • Request route │
│ • Data discovery│    │ • Jupyter notebooks│  │ • Agent coord   │
│ • Metadata search│   │ • Visualization │    │ • Result agg    │
│ • File analysis │    │ • Data pipelines│    │ • Cross-agent   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   LangGraph     │
                    │   Workflows     │
                    │                 │
                    │ • State mgmt    │
                    │ • Node execution│
                    │ • Error handling│
                    │ • Conditional   │
                    │   routing       │
                    └─────────────────┘
```

#### Agent Types & Responsibilities

**1. Schema Analysis Agent (Primary)**
- **Purpose**: Core TableTalk functionality - schema exploration and data discovery
- **Model**: `phi4-mini-fc` (local Ollama)
- **Tools**: All existing 8 TableTalk tools
- **Workflows**: 
  - Schema exploration
  - Data discovery
  - Metadata search
  - File analysis

**2. Code Generation Agent (Secondary)**
- **Purpose**: Generate Python scripts, notebooks, and analysis code
- **Model Options**: 
  - OpenAI GPT-4 (cloud) - for complex code generation
  - Ollama CodeLlama (local) - for privacy/offline scenarios
- **Tools**: 
  - File system access
  - Code validation
  - Template systems
- **Workflows**:
  - Python script generation
  - Jupyter notebook creation
  - Data pipeline code
  - Visualization scripts

**3. Orchestrator Agent (Meta-Agent)**
- **Purpose**: Route requests to appropriate agents and coordinate multi-agent workflows
- **Model**: Lightweight - rule-based or simple LLM
- **Responsibilities**:
  - Request classification
  - Agent selection
  - Result aggregation
  - Cross-agent communication

### Technical Design Specifications

#### State Management Schema
```python
class TableTalkState(TypedDict):
    """Unified state schema for all workflows."""
    # Core request data
    original_request: str                   # User's original question
    request_type: str                      # "schema", "code_gen", "multi_step"
    
    # Schema agent results
    search_results: Optional[Dict]          # Results from search_metadata
    file_list: Optional[List[str]]         # File names found
    schema_data: Optional[Dict]            # Schema information
    
    # Code generation results
    generated_code: str                    # Generated Python code
    code_validation: Optional[Dict]        # Validation results
    
    # Cross-agent coordination
    agent_history: List[str]               # Which agents were used
    execution_results: str                 # Final execution outcomes
    error_context: str                     # Error handling context
    
    # LangGraph internals
    messages: List[AnyMessage]             # Chat history
    final_response: str                    # Human-readable response
```

#### Model Integration Strategy

**Local Models (Ollama)**
```python
class OllamaMultiModel:
    def __init__(self):
        self.models = {
            "function_calling": "phi4-mini-fc",    # Current model - keep
            "code_generation": "codellama:34b",     # Better for code
            "general": "llama3.1:8b",              # Fast general tasks
            "advanced_code": "qwen2.5-coder"       # Advanced coding
        }
```

**Cloud Models (OpenAI)**
```python
class OpenAICodeAgent:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_code(self, requirements: str, schema_context: dict) -> str:
        # Superior code generation capabilities
        # Better at: complex algorithms, optimization, best practices
        # Trade-offs: API costs, internet dependency, data privacy
```

#### Configuration Strategy
```yaml
# Enhanced config/config.yaml
models:
  primary:
    type: "ollama"
    model: "phi4-mini-fc"
    base_url: "http://localhost:11434"
  
  code_generation:
    type: "openai"  # or "ollama"
    model: "gpt-4"
    api_key: "${OPENAI_API_KEY}"
    fallback:
      type: "ollama"
      model: "codellama:34b"
  
  general:
    type: "ollama"
    model: "llama3.1:8b"

agents:
  schema_agent:
    model: "primary"
    tools: ["all_tabletalk_tools"]
    workflows: ["search_then_schema", "direct_schema", "smart_routing"]
  
  code_generation_agent:
    model: "code_generation"
    tools: ["file_system", "code_validation", "templates"]
    workflows: ["script_generation", "notebook_creation"]
  
  orchestrator:
    model: "primary"
    max_steps: 10
    coordination_strategy: "sequential_with_fallback"

workflows:
  default_timeout: 30
  max_retries: 3
  parallel_execution: true
  enable_caching: true
```

---

## Part II: Changes Required

### New Component Structure

```
src/
├── main.py                     # Entry point (UNCHANGED)
├── cli/                        # CLI layer (MINIMAL CHANGES)
│   ├── chat_interface.py       # Update to use WorkflowAgent
│   └── rich_formatter.py       # UNCHANGED
├── agent/                      # MAJOR REWRITE - LangGraph integration
│   ├── __init__.py             # NEW
│   ├── workflow_agent.py       # NEW - Main LangGraph agent
│   ├── model_clients/          # NEW - Model abstraction layer
│   │   ├── __init__.py
│   │   ├── base_client.py      # Abstract base for all models
│   │   ├── ollama_client.py    # Multi-model Ollama support
│   │   └── openai_client.py    # OpenAI GPT integration
│   ├── workflows/              # NEW - Workflow definitions
│   │   ├── __init__.py
│   │   ├── state_schemas.py    # LangGraph state definitions
│   │   ├── node_wrappers.py    # Tool → Node adapters
│   │   ├── common_patterns.py  # Standard query workflows
│   │   ├── schema_workflows.py # Schema-focused workflows
│   │   └── code_gen_workflows.py # Code generation workflows
│   ├── agents/                 # NEW - Individual agent definitions
│   │   ├── __init__.py
│   │   ├── schema_agent.py     # Schema analysis specialist
│   │   ├── code_gen_agent.py   # Code generation specialist
│   │   └── orchestrator.py     # Multi-agent coordinator
│   └── legacy/                 # OLD CODE - For comparison/fallback
│       └── schema_agent.py     # Current implementation
├── tools/                      # UNCHANGED - Keep existing tools
│   ├── basic_tools.py          # No changes needed
│   ├── search_tools.py         # No changes needed
│   ├── comparison_tools.py     # No changes needed
│   ├── utility_tools.py        # No changes needed
│   ├── tool_registry.py        # MINOR UPDATE - LangGraph integration
│   └── core/                   # UNCHANGED
├── metadata/                   # UNCHANGED
├── utils/                      # UNCHANGED
└── config/                     # ENHANCED - Add workflow configurations
    ├── config.yaml             # Enhanced with workflow settings
    └── workflows.yaml          # NEW - Workflow-specific configurations
```

### Dependencies Changes

**Add to requirements.txt:**
```text
# LangGraph ecosystem (adds ~5MB total)
langgraph>=0.2.0               # Core LangGraph functionality
langchain-core>=0.3.0          # Required by LangGraph

# Optional: OpenAI integration
openai>=1.0.0                  # For GPT models (if using cloud)

# Code generation enhancements
ast>=3.8                       # For code validation
black>=22.0.0                  # For code formatting
```

### Configuration File Updates

**Enhanced config/config.yaml:**
- Add `models` section for multi-model support
- Add `agents` section for agent-specific configurations
- Add `workflows` section for workflow settings
- Maintain backward compatibility with existing settings

**New config/workflows.yaml:**
- Define available workflow types
- Set default routing rules
- Configure agent coordination patterns
- Set performance and timeout parameters

---

## Part III: Implementation Plan

### Phase 1: LangGraph Foundation (Week 1)
**Duration**: 5 days  
**Goal**: Fix sequential function calling bug with basic LangGraph integration

#### Day 1-2: Core Infrastructure
**Tasks:**
1. Install LangGraph dependencies
2. Create state schema (`workflows/state_schemas.py`)
3. Build tool-to-node wrappers (`workflows/node_wrappers.py`)
4. Implement basic sequential workflows

**Deliverables:**
- Working state management system
- Tool wrappers for existing TableTalk tools
- Basic search → schema workflow

**Key Files Created:**
```python
# src/agent/workflows/state_schemas.py
class TableTalkState(TypedDict):
    original_query: str
    search_results: Optional[Dict]
    file_list: Optional[List[str]]
    schema_data: Optional[Dict]
    final_response: str
    error_message: Optional[str]

# src/agent/workflows/node_wrappers.py
class ToolNodeWrapper:
    def create_search_node(self):
        def search_node(state: TableTalkState) -> TableTalkState:
            # Execute search_metadata tool
            # Parse results for next step
            # Return updated state
            pass
        return search_node
```

#### Day 3-4: Workflow Implementation
**Tasks:**
1. Build common workflow patterns (`workflows/common_patterns.py`)
2. Create main workflow agent (`workflow_agent.py`)
3. Implement conditional routing logic
4. Add error handling and recovery

**Deliverables:**
- 3-4 pre-built workflow patterns
- Main WorkflowAgent class
- Smart routing based on query analysis
- Graceful error handling

#### Day 5: Integration & Testing
**Tasks:**
1. Update CLI interface to use new agent
2. Comprehensive testing with existing queries
3. Performance comparison with old agent
4. Bug fixes and optimization

**Deliverables:**
- Updated chat_interface.py
- Test suite covering key workflows
- Performance benchmarks
- Working system with basic LangGraph integration

**Success Criteria for Phase 1:**
- [ ] Sequential function calling works 100% reliably
- [ ] All existing functionality preserved
- [ ] Performance equal or better than current implementation
- [ ] Zero regression in user experience

### Phase 2: Multi-Model Architecture (Week 2)
**Duration**: 5 days  
**Goal**: Add configurable model backends and multi-model support

#### Day 1-2: Model Abstraction Layer
**Tasks:**
1. Create base model client interface (`model_clients/base_client.py`)
2. Implement enhanced Ollama client with multi-model support
3. Add OpenAI GPT client integration
4. Create model selection and routing logic

**Deliverables:**
- Abstract base class for all model clients
- Multi-model Ollama client
- OpenAI GPT client
- Automatic model selection system

#### Day 3-4: Agent Specialization
**Tasks:**
1. Split functionality into specialized agents
2. Implement schema analysis agent
3. Create code generation agent (basic version)
4. Build agent coordination system

**Deliverables:**
- Specialized schema analysis agent
- Basic code generation capabilities
- Agent-to-agent communication system
- Coordinated multi-agent workflows

#### Day 5: Configuration & Testing
**Tasks:**
1. Enhance configuration system for multi-model support
2. Add model performance monitoring
3. Implement cost tracking for API usage
4. Comprehensive testing across model types

**Deliverables:**
- Enhanced configuration files
- Model performance metrics
- Cost tracking dashboard
- Multi-model test suite

**Success Criteria for Phase 2:**
- [ ] Can switch between Ollama and OpenAI seamlessly
- [ ] Configuration-driven model selection works
- [ ] Cost tracking for API usage implemented
- [ ] Performance monitoring for all models

### Phase 3: Code Generation Agent (Week 3)
**Duration**: 5 days  
**Goal**: Add comprehensive Python script and notebook generation

#### Day 1-2: Code Generation Workflows
**Tasks:**
1. Design code generation workflow patterns
2. Implement Python script generation
3. Add code validation and testing
4. Create template system for common patterns

**Deliverables:**
- Code generation workflow definitions
- Python script generation capabilities
- Automated code validation
- Template system for common code patterns

#### Day 3-4: Advanced Features
**Tasks:**
1. Implement Jupyter notebook generation
2. Add data visualization code generation
3. Create data pipeline script generation
4. Implement code optimization suggestions

**Deliverables:**
- Complete Jupyter notebook generation
- Visualization code generation (matplotlib, seaborn, plotly)
- Data pipeline templates
- Code quality and optimization suggestions

#### Day 5: Integration & Export
**Tasks:**
1. Integrate with existing export system
2. Add code execution and testing capabilities
3. Implement code sharing and versioning
4. Create comprehensive documentation

**Deliverables:**
- Integrated export functionality
- Code execution environment
- Version control for generated code
- User documentation and examples

**Success Criteria for Phase 3:**
- [ ] Generate working Python scripts from natural language
- [ ] Create complete Jupyter notebooks with multiple cells
- [ ] Code validation and testing integrated
- [ ] Export functionality for generated code

### Phase 4: Full Multi-Agent System (Week 4)
**Duration**: 5 days  
**Goal**: Enable complex multi-agent workflows and advanced orchestration

#### Day 1-2: Orchestrator Implementation
**Tasks:**
1. Build sophisticated orchestrator agent
2. Implement cross-agent communication protocols
3. Add workflow composition capabilities
4. Create agent coordination strategies

**Deliverables:**
- Advanced orchestrator agent
- Inter-agent communication system
- Workflow composition tools
- Coordination strategy implementations

#### Day 3-4: Advanced Workflows
**Tasks:**
1. Create complex multi-step workflow examples
2. Implement parallel agent execution
3. Add conditional workflow branching
4. Build workflow optimization system

**Deliverables:**
- Complex workflow examples (schema → analysis → code → visualization)
- Parallel execution capabilities
- Advanced conditional logic
- Workflow performance optimization

#### Day 5: Monitoring & Production Readiness
**Tasks:**
1. Implement comprehensive monitoring and debugging
2. Add performance profiling and optimization
3. Create production deployment configurations
4. Final testing and documentation

**Deliverables:**
- Monitoring and debugging dashboard
- Performance profiling tools
- Production-ready configurations
- Complete system documentation

**Success Criteria for Phase 4:**
- [ ] Complex multi-step workflows execute correctly
- [ ] Agent coordination works seamlessly
- [ ] Performance monitoring and debugging available
- [ ] System is production-ready

---

## Part IV: Benefits & Risk Assessment

### Technical Benefits Summary
1. **Bug Resolution**: Sequential function calling works reliably with automatic dependency resolution
2. **Scalability**: Easy to add new agents, workflows, and model types
3. **Model Flexibility**: Switch between local/cloud models based on specific needs
4. **Maintainability**: Clean separation of concerns with modular architecture
5. **Testing**: Unit test individual agents, workflows, and model integrations
6. **Performance**: Built-in optimization, caching, and parallel execution
7. **Monitoring**: Advanced debugging, profiling, and error tracking

### Feature Enablement
1. **Advanced Code Generation**: OpenAI GPT for complex Python scripts and notebooks
2. **Privacy Options**: Keep sensitive schema data local with Ollama models
3. **Cost Optimization**: Use appropriate model for each specific task
4. **Offline Capability**: Full functionality without internet connection
5. **Future Extensibility**: Easy to add new agents (SQL generation, data visualization, etc.)

### Risk Assessment & Mitigation

**Technical Risks:**
- **Complexity Increase**: More components and dependencies
- **Migration Risk**: Potential breaking changes during transition
- **Performance Impact**: Additional overhead from LangGraph
- **Learning Curve**: New concepts for team members

**Mitigation Strategies:**
- **Gradual Migration**: Phase-based approach with backward compatibility
- **Comprehensive Testing**: Unit and integration tests for each phase
- **Documentation**: Clear guides for configuration, usage, and troubleshooting
- **Fallback Options**: Keep legacy system available during transition
- **Performance Monitoring**: Track and optimize performance throughout migration

**Business Risks:**
- **Development Time**: 4-week migration timeline
- **Resource Requirements**: Additional dependencies and storage
- **API Costs**: Potential costs for OpenAI GPT usage

**Mitigation Strategies:**
- **ROI Analysis**: Calculate time saved vs development cost
- **Cost Controls**: Configurable limits and monitoring for API usage
- **Local Alternatives**: Ollama models as cost-effective alternatives

---

## Part V: Success Metrics & Validation

### Technical Success Metrics
1. **Function Call Success Rate**: 100% success for sequential calling patterns
2. **Response Time**: <500ms for simple queries, <2s for complex workflows
3. **Backward Compatibility**: 100% of existing queries work unchanged
4. **Error Handling**: <1% unhandled errors with graceful degradation
5. **Model Flexibility**: Switch between models in <100ms
6. **Resource Usage**: <20% increase in memory usage, <10% CPU overhead

### Feature Success Metrics
1. **Code Generation Quality**: 90% of generated code runs without errors
2. **Notebook Creation**: Generate complete notebooks with 5-10 cells
3. **Multi-Agent Coordination**: Complex workflows complete in <30 seconds
4. **User Satisfaction**: Maintain current user experience quality

### Migration Success Criteria
1. **Zero Downtime**: Seamless transition without service interruption
2. **Feature Parity**: All current features work in new system
3. **Performance**: Equal or better performance than current system
4. **Maintainability**: Reduced code complexity and improved debuggability

---

## Conclusion

This migration to LangGraph represents a strategic upgrade that will:

1. **Immediately solve** the sequential function calling bug that's limiting TableTalk's effectiveness
2. **Enable advanced features** like multi-agent workflows and sophisticated code generation
3. **Provide model flexibility** for both privacy-focused (local) and capability-focused (cloud) use cases
4. **Create a foundation** for future enhancements like automated notebook generation and data pipeline creation
5. **Reduce long-term maintenance** burden through use of production-tested frameworks

The 4-week timeline is conservative and includes thorough testing and documentation. The investment will pay dividends in reduced debugging time, enhanced capabilities, and easier feature development going forward.

**Recommended Next Steps:**
1. **Approval**: Review and approve this migration plan
2. **Environment Setup**: Install LangGraph dependencies and set up development environment
3. **Phase 1 Kickoff**: Begin with core LangGraph integration
4. **API Access**: Set up OpenAI API access for testing cloud model integration
5. **Progress Tracking**: Weekly reviews to ensure timeline adherence and quality standards