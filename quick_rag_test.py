#!/usr/bin/env python3
"""Quick test to verify RAG indexing of new files."""

import sys
import os

sys.path.insert(0, "backend")

from services.rag_service import get_rag_service

rag = get_rag_service()

# Check files
kb_path = "backend/data/knowledge_base"
files = [f for f in os.listdir(kb_path) if f.endswith(".txt")]
print(f"Files in knowledge base: {len(files)}")
print(
    f'  littles_law_coaching_template.txt present: {"littles_law_coaching_template.txt" in files}'
)
print(
    f'  littles_law_insight_patterns.txt present: {"littles_law_insight_patterns.txt" in files}'
)

# Force re-index
print("\nRe-indexing...")
chunks = rag.index_knowledge_base()
print(f"Indexed {chunks} chunks")

# Test retrieval
print("\nTesting retrieval:")
docs = rag.retrieve("Little Law coaching template structure", top_k=5)
for i, doc in enumerate(docs, 1):
    source = doc.get("metadata", {}).get("source", "Unknown")
    print(f"{i}. {source}")
    if "littles_law" in source.lower():
        print("   ✅ Found our new file!")
