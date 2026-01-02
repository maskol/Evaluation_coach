# RAG Knowledge Base Structure

**Purpose**: Provide structured, metadata-driven knowledge retrieval for coaching insights.

**Philosophy**: Knowledge is not just "documents in a folder" — it's a tagged, queryable, contextual resource.

---

## 1. Knowledge Domain Taxonomy

```
knowledge/
├── agile_principles/          # Foundational theory
│   ├── flow_theory.md
│   ├── little_law.md
│   ├── system_thinking.md
│   ├── kanban_principles.md
│   └── lean_thinking.md
│
├── safe/                      # SAFe-specific guidance
│   ├── portfolio_flow.md
│   ├── art_execution.md
│   ├── pi_planning.md
│   ├── team_topologies.md
│   ├── built_in_quality.md
│   └── lean_portfolio_mgmt.md
│
├── coaching_patterns/         # Symptom → Guidance mapping
│   ├── low_predictability.md
│   ├── high_wip.md
│   ├── dependency_anti_patterns.md
│   ├── quality_degradation.md
│   ├── blocked_work.md
│   └── scope_instability.md
│
├── metrics_interpretation/    # How to read the data
│   ├── lead_time.md
│   ├── throughput.md
│   ├── predictability.md
│   ├── flow_efficiency.md
│   └── quality_metrics.md
│
├── improvement_playbooks/     # Actionable guidance
│   ├── reduce_wip.md
│   ├── dependency_management.md
│   ├── quality_shift_left.md
│   ├── improve_pi_planning.md
│   ├── team_wip_limits.md
│   └── cross_team_collaboration.md
│
└── case_studies/             # Real-world examples
    ├── art_turnaround_dependency_mgmt.md
    ├── team_wip_reduction.md
    └── portfolio_epic_limits.md
```

---

## 2. Document Metadata Schema

Every knowledge document MUST include YAML frontmatter for retrieval.

### Example: `coaching_patterns/high_wip.md`

```yaml
---
id: high_wip_pattern
title: High Work-in-Progress Anti-Pattern
category: coaching_pattern
tags:
  - wip
  - flow
  - bottleneck
  - team
applicability:
  scope: [Team, ART]
  metrics:
    - name: wip_per_person
      trigger: "> 2.5"
    - name: cycle_time
      trigger: "increasing"
symptom: High parallel work, long cycle times, low throughput
root_causes:
  - Over-commitment
  - Lack of WIP limits
  - Unclear priorities
  - External interruptions
related_metrics:
  - wip
  - cycle_time
  - throughput
  - flow_efficiency
related_patterns:
  - low_throughput
  - low_flow_efficiency
confidence: high
---

# High WIP Anti-Pattern

## Overview
When teams or ARTs take on too much work simultaneously, context switching increases, cycle times extend, and throughput paradoxically decreases.

## Indicators
- **WIP per person > 2.5**
- **Cycle time trending upward**
- **Throughput declining despite high WIP**
- **Flow efficiency < 30%**

## Root Causes

### 1. Over-Commitment
Teams say "yes" to all requests without considering capacity.

### 2. Lack of WIP Limits
No explicit constraints on parallel work.

### 3. Unclear Prioritization
Everything is high priority, so nothing gets focused attention.

## Impact
- **Cycle time** increases by 2-3x
- **Throughput** decreases by 20-40%
- **Quality** suffers (more defects)
- **Team morale** declines (feeling overwhelmed)

## Coaching Guidance

### Short-Term Actions (Next Sprint)
1. **Visualize Current WIP**
   - Create board showing all in-progress items
   - Calculate WIP per person
   
2. **Implement Soft WIP Limit**
   - Start with limit of 2 per person
   - Make violations visible

3. **Daily Stand-Up Focus**
   - "What can we finish today?" vs "What's starting?"

### Medium-Term Actions (Next PI)
1. **Formalize WIP Limits**
   - Team agrees on limits
   - Add to working agreement
   
2. **Introduce Pull System**
   - Only start new work when capacity opens
   
3. **Prioritization Discipline**
   - Clear priority ordering
   - Product Owner empowerment

### Long-Term Actions (Systemic)
1. **Organizational Respect for WIP**
   - Leadership understands trade-offs
   - No bypassing WIP limits
   
2. **Capacity-Based Planning**
   - Plan based on throughput, not optimistic estimates

## Success Metrics
- WIP per person drops to ≤ 1.5
- Cycle time decreases by 30-50%
- Throughput increases by 15-25%
- Team satisfaction improves

## Related Playbooks
- [Reduce WIP Playbook](../improvement_playbooks/reduce_wip.md)
- [Team WIP Limits](../improvement_playbooks/team_wip_limits.md)

## References
- Vacanti, D. (2015). *Actionable Agile Metrics*
- Reinertsen, D. (2009). *Product Development Flow*
- Little's Law
```

---

## 3. Metadata-Driven Retrieval Strategy

### 3.1 Query Construction

When the agent detects a pattern, it constructs a structured query:

```python
query = {
    "metric": "wip_per_person",
    "value": 3.2,
    "scope": "Team",
    "symptom": "high_wip",
    "context": {
        "cycle_time": "increasing",
        "throughput": "declining"
    }
}
```

### 3.2 Retrieval Logic

```python
def retrieve_coaching_knowledge(query: dict) -> List[Document]:
    """
    Retrieve relevant knowledge using metadata + semantic search.
    """
    # Step 1: Metadata filter
    filtered_docs = filter_by_metadata(
        scope=query["scope"],
        metrics=query["metric"],
        tags=query.get("symptom")
    )
    
    # Step 2: Semantic search within filtered docs
    embeddings = embed_query(query["symptom"])
    ranked_docs = semantic_search(
        embeddings=embeddings,
        documents=filtered_docs,
        top_k=5
    )
    
    # Step 3: Re-rank by confidence + relevance
    final_docs = rerank(ranked_docs, query)
    
    return final_docs
```

### 3.3 Embedding Strategy

```python
# Use OpenAI embeddings for semantic search
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Index all knowledge documents
vectorstore = Chroma(
    collection_name="evaluation_coach_knowledge",
    embedding_function=embeddings,
    persist_directory="./data/vectorstore"
)
```

---

## 4. Knowledge Document Templates

### 4.1 Coaching Pattern Template

```yaml
---
id: [unique_id]
title: [Pattern Name]
category: coaching_pattern
tags: [list of tags]
applicability:
  scope: [Team, ART, Portfolio]
  metrics:
    - name: [metric_name]
      trigger: [threshold]
symptom: [One-line description]
root_causes: [List]
related_metrics: [List]
related_patterns: [List]
confidence: [high, medium, low]
---

# [Pattern Name]

## Overview
[What this pattern is]

## Indicators
[What signals this pattern]

## Root Causes
[Why this happens]

## Impact
[Consequences]

## Coaching Guidance
### Short-Term Actions
### Medium-Term Actions
### Long-Term Actions

## Success Metrics
[How to know it's working]

## References
[Sources]
```

### 4.2 Improvement Playbook Template

```yaml
---
id: [unique_id]
title: [Playbook Name]
category: improvement_playbook
tags: [list of tags]
applicability:
  scope: [Team, ART, Portfolio]
  patterns: [List of patterns this addresses]
difficulty: [easy, moderate, hard]
time_to_value: [days/weeks/months]
prerequisites: [What's needed]
---

# [Playbook Name]

## Goal
[What this playbook achieves]

## When to Use
[Triggers]

## Steps

### Phase 1: [Name]
**Duration**: [Time]
**Actions**:
1. [Action 1]
2. [Action 2]

### Phase 2: [Name]
...

## Common Pitfalls
[What to avoid]

## Success Criteria
[How to measure success]

## Case Study
[Real example]
```

### 4.3 Metrics Interpretation Template

```yaml
---
id: [unique_id]
title: [Metric Name] Interpretation
category: metrics_interpretation
tags: [list of tags]
metric: [exact metric name]
related_metrics: [List]
---

# [Metric Name]

## Definition
[What this metric measures]

## Calculation
[Formula]

## Interpretation

### Healthy Range
[What values indicate good performance]

### Warning Signs
[What values suggest problems]

### Critical Issues
[What values demand immediate attention]

## Common Misinterpretations
[What people get wrong]

## Context Matters
[When this metric alone is misleading]

## Related Metrics
[What else to look at]
```

---

## 5. Knowledge Ingestion Pipeline

### 5.1 Setup

```bash
# Install dependencies
pip install langchain-community langchain-openai chromadb

# Initialize vectorstore
python backend/rag/ingest_knowledge.py
```

### 5.2 Ingestion Script

```python
# backend/rag/ingest_knowledge.py
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter
import yaml

def parse_metadata(content: str) -> tuple:
    """Extract YAML frontmatter and content."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        metadata = yaml.safe_load(parts[1])
        text = parts[2].strip()
        return metadata, text
    return {}, content

def ingest_knowledge_base():
    """Ingest all knowledge documents into vectorstore."""
    knowledge_dir = Path("knowledge")
    
    # Load all markdown files
    loader = DirectoryLoader(
        str(knowledge_dir),
        glob="**/*.md",
        show_progress=True
    )
    docs = loader.load()
    
    # Parse metadata and split
    processed_docs = []
    for doc in docs:
        metadata, content = parse_metadata(doc.page_content)
        
        # Add file path to metadata
        metadata["source"] = doc.metadata["source"]
        
        # Split by headers
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "title"),
                ("##", "section"),
                ("###", "subsection")
            ]
        )
        chunks = splitter.split_text(content)
        
        # Merge metadata
        for chunk in chunks:
            chunk.metadata.update(metadata)
            processed_docs.append(chunk)
    
    # Create vectorstore
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=processed_docs,
        embedding=embeddings,
        collection_name="evaluation_coach_knowledge",
        persist_directory="./data/vectorstore"
    )
    
    print(f"Ingested {len(processed_docs)} chunks from {len(docs)} documents")
    
    return vectorstore

if __name__ == "__main__":
    ingest_knowledge_base()
```

---

## 6. Retrieval Examples

### Example 1: High WIP at Team Level

**Input**:
```python
query = {
    "scope": "Team",
    "metric": "wip_per_person",
    "value": 3.2,
    "symptom": "high_wip"
}
```

**Retrieved Documents**:
1. `coaching_patterns/high_wip.md` (confidence: 0.95)
2. `improvement_playbooks/reduce_wip.md` (confidence: 0.92)
3. `improvement_playbooks/team_wip_limits.md` (confidence: 0.89)
4. `agile_principles/little_law.md` (confidence: 0.75)

### Example 2: Low PI Predictability

**Input**:
```python
query = {
    "scope": "ART",
    "metric": "pi_predictability",
    "value": 0.62,
    "symptom": "low_predictability",
    "context": {
        "blocked_time": 0.18,
        "cross_team_deps": 0.22
    }
}
```

**Retrieved Documents**:
1. `coaching_patterns/low_predictability.md`
2. `coaching_patterns/dependency_anti_patterns.md`
3. `improvement_playbooks/improve_pi_planning.md`
4. `improvement_playbooks/dependency_management.md`
5. `safe/pi_planning.md`

---

## 7. Knowledge Maintenance

### 7.1 Versioning

```
knowledge/
├── v1.0/                    # Initial knowledge base
├── v1.1/                    # Added case studies
└── current -> v1.1/         # Symlink to active version
```

### 7.2 Contribution Guidelines

**Adding New Patterns**:
1. Use appropriate template
2. Include all required metadata
3. Link related patterns/playbooks
4. Cite sources
5. Test retrieval

**Updating Existing Documents**:
1. Update metadata version
2. Maintain backward compatibility
3. Re-ingest into vectorstore

### 7.3 Quality Checklist

- [ ] YAML frontmatter complete
- [ ] All required fields present
- [ ] Tags aligned with taxonomy
- [ ] Related documents linked
- [ ] References cited
- [ ] Retrieval tested

---

## 8. Advanced Retrieval Techniques

### 8.1 Hybrid Search (Keyword + Semantic)

```python
def hybrid_retrieval(query: dict, alpha: float = 0.5):
    """
    Combine keyword (BM25) and semantic (vector) search.
    
    alpha: weight for semantic search (1-alpha for keyword)
    """
    # Keyword search
    keyword_results = bm25_search(query["symptom"])
    
    # Semantic search
    semantic_results = vector_search(query["symptom"])
    
    # Combine and re-rank
    combined = merge_results(
        keyword_results,
        semantic_results,
        alpha=alpha
    )
    
    return combined
```

### 8.2 Context-Aware Filtering

```python
def context_aware_filter(docs: List[Document], context: dict) -> List[Document]:
    """
    Filter documents based on additional context.
    """
    filtered = []
    for doc in docs:
        # Check scope match
        if context["scope"] not in doc.metadata.get("applicability", {}).get("scope", []):
            continue
        
        # Check confidence threshold
        if doc.metadata.get("confidence") == "low":
            continue
        
        filtered.append(doc)
    
    return filtered
```

---

## 9. Integration with Agent Workflow

### Node 4: Knowledge Retriever

```python
async def knowledge_retriever_node(state: AgentState) -> AgentState:
    """
    Retrieve relevant coaching knowledge based on detected patterns.
    """
    patterns = state["analysis_result"]["patterns"]
    
    retrieved_knowledge = []
    
    for pattern in patterns:
        # Construct query
        query = {
            "scope": state["scope"],
            "metric": pattern["metric"],
            "symptom": pattern["name"],
            "context": state["metrics"]
        }
        
        # Retrieve documents
        docs = retrieve_coaching_knowledge(query)
        
        # Extract relevant sections
        for doc in docs:
            retrieved_knowledge.append({
                "pattern": pattern["name"],
                "document": doc.metadata["source"],
                "content": doc.page_content,
                "confidence": doc.metadata.get("confidence", "medium")
            })
    
    return {
        **state,
        "retrieved_knowledge": retrieved_knowledge
    }
```

---

## 10. Starter Knowledge Base

Create initial documents:

```bash
# Phase 4 (Weeks 9-10)
mkdir -p knowledge/{agile_principles,safe,coaching_patterns,metrics_interpretation,improvement_playbooks,case_studies}

# Priority documents to create first:
knowledge/coaching_patterns/high_wip.md
knowledge/coaching_patterns/low_predictability.md
knowledge/coaching_patterns/dependency_anti_patterns.md
knowledge/improvement_playbooks/reduce_wip.md
knowledge/improvement_playbooks/dependency_management.md
knowledge/safe/pi_planning.md
knowledge/safe/art_execution.md
knowledge/metrics_interpretation/lead_time.md
knowledge/metrics_interpretation/predictability.md
```

---

## References

- LangChain RAG Documentation
- ChromaDB Documentation
- SAFe 6.0 Lean-Agile Principles
- "Thinking in Systems" - Donella Meadows
