# 🗣️ TableTalk Conversation Migration Plan

**Created**: August 6, 2025  
**Target**: Multi-turn conversational capabilities  
**Current State**: Transactional query processing  
**LLM Model**: Phi-4 Mini (function calling)  

## 📋 Executive Summary

This document outlines the migration plan to transform TableTalk from a transactional query system into a conversational data exploration assistant. The plan focuses on Phi-4 Mini compatibility and maintains the existing clean architecture while adding conversation memory and context resolution.

## 🎯 Goals & Expected Outcomes

### **Primary Goals**
- ✅ Enable multi-turn conversations with context awareness
- ✅ Support natural follow-up questions and references  
- ✅ Maintain conversation state across related queries
- ✅ Preserve existing tool functionality and export system

### **Success Metrics**
- **Context Resolution**: 85%+ success rate for simple references ("that file", "those results")
- **Follow-up Success**: 90%+ success for immediate follow-ups  
- **User Experience**: Seamless conversation flow without breaking changes
- **Performance**: <200ms overhead for conversation processing

### **Example Target Conversations**
```bash
# Scenario 1: File exploration with context
User: "What files do we have?"
Assistant: "Found 4 files: customers.csv, orders.csv, reviews.csv, legacy_users.csv"
User: "Show me the schema for customers"
Assistant: [customers.csv schema details]
User: "What about orders?"  # ← Context resolution
Assistant: [orders.csv schema details - system resolves "orders" reference]

# Scenario 2: Analysis continuation  
User: "Find schema differences between customers and legacy_users"
Assistant: [Detailed differences analysis - may trigger export]
User: "Are there any type mismatches in that analysis?"  # ← Analysis continuation
Assistant: [Filtered view focusing on type mismatches from previous analysis]

# Scenario 3: Multi-file exploration
User: "Compare all user-related files"  
Assistant: [Analysis of customers.csv, legacy_users.csv relationships]
User: "Show me the most similar pair"  # ← Reference to previous analysis
Assistant: [Details for highest similarity pair from previous comparison]
```

## 🏗️ Technical Architecture Changes

### **Current Architecture (Transactional)**
```
User Query → Agent → Tools → Response (No State)
```

### **Target Architecture (Conversational)**
```
User Query → Context Resolver → Agent + Context → Tools → Response + State Update
              ↑                                                           ↓
              ←← Conversation Manager ←← State Tracker ←←←←←←←←←←←←←←←←←←
```

### **New Components**

#### **1. ConversationManager**
```python
class ConversationManager:
    """Central conversation orchestrator"""
    def __init__(self):
        self.context = ConversationContext()
        self.resolver = ContextResolver()
        self.memory = ConversationMemory()
        
    def process_query(self, query: str) -> Tuple[str, dict]:
        """Process query with full conversation context"""
        # 1. Resolve references and context
        # 2. Build contextual prompt  
        # 3. Execute query with agent
        # 4. Update conversation state
        # 5. Return response + metadata
```

#### **2. ConversationContext**
```python
class ConversationContext:
    """Tracks conversation state and context"""
    def __init__(self):
        self.current_files: List[str] = []
        self.last_analysis_type: Optional[str] = None
        self.last_result_summary: Optional[str] = None
        self.active_comparison: Optional[dict] = None
        self.cached_results: Dict[str, Any] = {}
```

#### **3. ContextResolver**
```python
class ContextResolver:
    """Resolves pronouns and references in queries"""
    def resolve_query(self, query: str, context: ConversationContext) -> str:
        """Transform query with context resolution"""
        # Handle file references: "that file" → "customers.csv"
        # Handle analysis references: "that analysis" → "schema_differences"
        # Handle pronoun resolution: "the first one" → specific item
```

#### **4. ConversationMemory**
```python
class ConversationMemory:
    """Manages conversation history with smart compression"""
    def __init__(self, max_detailed_history: int = 5):
        self.detailed_history: Deque[ConversationExchange] = deque(maxlen=max_detailed_history)
        self.compressed_history: List[ConversationSummary] = []
```

## 📋 Implementation Plan

### **Phase 1: Foundation (2 days)**

#### **Day 1: Core Infrastructure**
- [ ] Create conversation management components
- [ ] Implement basic context tracking
- [ ] Add conversation memory storage
- [ ] Update ChatInterface to use ConversationManager

**Files to Create:**
- `src/conversation/conversation_manager.py`
- `src/conversation/context_resolver.py` 
- `src/conversation/conversation_memory.py`
- `src/conversation/__init__.py`

**Files to Modify:**
- `src/cli/chat_interface.py` - Integrate ConversationManager
- `config/config.yaml` - Add conversation settings

#### **Day 2: Basic Context Resolution**
- [ ] Implement simple reference resolution patterns
- [ ] Add file context tracking 
- [ ] Create context-aware prompt building
- [ ] Test basic multi-turn scenarios

**Key Features:**
- File reference resolution ("that file" → actual filename)
- Analysis continuation ("that analysis" → previous analysis type)
- Simple follow-up support

### **Phase 2: Smart Context (2 days)**

#### **Day 3: Advanced Resolution**
- [ ] Enhanced pronoun resolution
- [ ] Analysis result caching and filtering
- [ ] Context compression for long conversations
- [ ] Error handling and fallbacks

#### **Day 4: Integration & Polish**
- [ ] Export system integration with conversation context
- [ ] Conversation state persistence (optional)
- [ ] Help system updates for conversation features
- [ ] Performance optimization

### **Phase 3: Validation & Documentation (1 day)**

#### **Day 5: Testing & Documentation**
- [ ] Comprehensive conversation testing
- [ ] Performance benchmarking
- [ ] Documentation updates
- [ ] User guide for conversation features

## 🔧 Implementation Details

### **Configuration Changes**

#### **config/config.yaml**
```yaml
# New conversation section
conversation:
  enabled: true
  max_history: 10           # Detailed conversation exchanges to keep
  context_window: 5         # Exchanges to include in context
  compression_threshold: 15  # When to start compressing history
  reference_resolution: true # Enable pronoun/reference resolution
  fallback_clarification: true # Ask for clarification when ambiguous

# Enhanced export integration
export:
  enabled: true
  auto_export_threshold: 20
  base_path: "./exports"
  conversation_aware: true    # Include conversation context in exports
```

### **Context Resolution Patterns**

#### **File References**
```python
FILE_PATTERNS = {
    r'\bthat file\b': lambda ctx: ctx.current_files[-1] if ctx.current_files else None,
    r'\bthose files\b': lambda ctx: ', '.join(ctx.current_files),
    r'\bthe (\w+) file\b': lambda ctx, name: f"{name}.csv" if f"{name}.csv" in ctx.current_files else None,
    r'\b(customers?|orders?|reviews?|users?)\b': lambda ctx, name: f"{name}.csv"
}
```

#### **Analysis References**
```python
ANALYSIS_PATTERNS = {
    r'\bthat analysis\b': lambda ctx: ctx.last_analysis_type,
    r'\bthose (differences|results|mismatches)\b': lambda ctx, type: f"{ctx.last_analysis_type}_{type}",
    r'\bthe previous (comparison|analysis)\b': lambda ctx, type: ctx.last_analysis_type,
}
```

#### **Result Filtering** 
```python
FILTER_PATTERNS = {
    r'\bhigh similarity\b': lambda results: [r for r in results if getattr(r, 'similarity', 0) > 0.7],
    r'\btype mismatches?\b': lambda results: [r for r in results if 'type_mismatch' in str(r)],
    r'\bthe first (one|item|result)\b': lambda results: results[0] if results else None,
}
```

### **Phi-4 Mini Optimizations**

#### **Context-Aware Prompting**
```python
def build_phi4_optimized_prompt(self, query: str, context: ConversationContext) -> str:
    """Build conversation prompt optimized for Phi-4 Mini capabilities"""
    prompt_parts = []
    
    # System context (explicit, not implicit)
    if context.current_files:
        prompt_parts.append(f"Available files: {', '.join(context.current_files)}")
    
    if context.last_analysis_type:
        prompt_parts.append(f"Last analysis: {context.last_analysis_type}")
        
    # Recent conversation (compressed)
    if context.recent_exchanges:
        prompt_parts.append("Recent conversation:")
        for exchange in context.recent_exchanges[-2:]:  # Last 2 only
            prompt_parts.append(f"  Q: {exchange.query[:50]}...")
            prompt_parts.append(f"  A: {exchange.summary}")
    
    # Current query with explicit instructions
    prompt_parts.extend([
        f"Current query: {query}",
        "",
        "Instructions:",
        "- If query references 'that file/analysis', use the context above",
        "- If unclear, ask for clarification",
        "- Use function calling for data operations"
    ])
    
    return "\n".join(prompt_parts)
```

#### **Smart Context Compression**
```python
class Phi4ContextCompressor:
    """Compress conversation history for Phi-4 Mini efficiency"""
    
    def compress_exchange(self, exchange: ConversationExchange) -> ConversationSummary:
        """Compress to essential information only"""
        return ConversationSummary(
            query_intent=self.extract_intent(exchange.query),
            tools_used=exchange.tools_used,
            result_type=exchange.result_type,
            key_findings=self.extract_key_findings(exchange.response),
            files_involved=exchange.files_involved
        )
```

## 🧪 Testing Strategy

### **Unit Tests**
- [ ] Context resolution accuracy
- [ ] Reference pattern matching  
- [ ] Memory management
- [ ] Conversation state transitions

### **Integration Tests**
- [ ] Multi-turn conversation flows
- [ ] Export system with conversation context
- [ ] Error handling and recovery
- [ ] Performance under load

### **User Acceptance Tests**
```python
CONVERSATION_TEST_SCENARIOS = [
    {
        "name": "Basic File Exploration",
        "steps": [
            "What files do we have?",
            "Show me the schema for customers", 
            "What about orders?",
            "Find differences between these two"
        ],
        "expected_success_rate": 0.95
    },
    {
        "name": "Analysis Deep Dive", 
        "steps": [
            "Find schema differences between customers and legacy_users",
            "Are there any type mismatches?",
            "Show me the most significant differences",
            "Can you explain the first mismatch?"
        ],
        "expected_success_rate": 0.85
    }
]
```

## 📊 Risk Assessment & Mitigation

### **High Risk: Context Resolution Accuracy**
**Risk**: Phi-4 Mini may struggle with complex pronoun resolution  
**Mitigation**: 
- Explicit context injection instead of relying on model memory
- Fallback to clarification requests
- Simple reference patterns first, complex ones later

### **Medium Risk: Performance Impact**
**Risk**: Conversation processing adds latency  
**Mitigation**:
- Async context processing
- Smart context compression  
- Caching of resolved contexts

### **Low Risk: Memory Usage**
**Risk**: Conversation history grows over time  
**Mitigation**:
- Automatic history compression
- Configurable memory limits
- Optional persistence with cleanup

## 🚀 Rollout Plan

### **Feature Flags**
```yaml
conversation:
  enabled: true              # Master toggle
  reference_resolution: true # Can disable if issues
  context_injection: true    # Can fallback to basic mode
  memory_persistence: false  # Start with in-memory only
```

### **Gradual Rollout**
1. **Phase 1**: Internal testing with basic patterns
2. **Phase 2**: Beta testing with advanced features  
3. **Phase 3**: Full release with monitoring
4. **Phase 4**: Performance optimization based on usage

### **Monitoring & Metrics**
- Conversation success rates
- Context resolution accuracy
- User satisfaction scores
- Performance impact metrics
- Error rates and patterns

## 📚 Documentation Updates

### **User Documentation**
- [ ] Update USAGE.md with conversation examples
- [ ] Add conversation best practices
- [ ] Document reference patterns and limitations

### **Developer Documentation**  
- [ ] Update ARCHITECTURE.md with conversation components
- [ ] API documentation for conversation classes
- [ ] Troubleshooting guide for conversation issues

## 🎯 Success Criteria

### **Functional Requirements** 
- ✅ 90%+ success rate for basic file references
- ✅ 85%+ success rate for analysis continuation
- ✅ 80%+ success rate for complex multi-turn scenarios
- ✅ Graceful degradation when context is unclear

### **Non-Functional Requirements**
- ✅ <200ms conversation processing overhead
- ✅ Memory usage under 50MB for conversation state
- ✅ No breaking changes to existing functionality
- ✅ Backward compatibility with transactional usage

### **User Experience Requirements**
- ✅ Natural conversation flow
- ✅ Clear feedback when clarification needed
- ✅ Consistent behavior across conversation types
- ✅ Easy fallback to explicit queries when needed

## 🔄 Future Enhancements

### **Phase 4: Advanced Features (Future)**
- Conversation branching and context switching
- Multi-topic conversation management  
- Advanced coreference resolution
- Conversation summarization and insights
- Integration with larger language models
- Voice conversation support

### **Phase 5: Intelligence Upgrades (Future)**
- Intent classification and routing
- Proactive suggestions based on conversation
- Automated follow-up question generation
- Conversation pattern learning
- Personalized conversation styles

---

**Next Steps**: Begin Phase 1 implementation with ConversationManager foundation and basic context tracking.

**Questions/Concerns**: Contact development team for clarification on any implementation details or timeline adjustments.
