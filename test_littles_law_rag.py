#!/usr/bin/env python3
"""
Test script to verify Little's Law coaching template is accessible via RAG.

This script tests:
1. RAG service initialization
2. Re-indexing knowledge base (including new templates)
3. Retrieving the Little's Law coaching template
4. Retrieving the Little's Law insight patterns
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

from services.rag_service import get_rag_service


def main():
    print("=" * 80)
    print("Testing Little's Law RAG Integration")
    print("=" * 80)

    # Get RAG service
    print("\n1. Initializing RAG service...")
    rag = get_rag_service()
    print("✅ RAG service initialized")

    # Re-index knowledge base
    print("\n2. Re-indexing knowledge base...")
    num_chunks = rag.index_knowledge_base()
    print(f"✅ Indexed {num_chunks} chunks")

    # Get stats
    print("\n3. Knowledge base statistics:")
    stats = rag.get_stats()
    print(f"   Total chunks: {stats.get('total_chunks', 0)}")
    print(f"   Total documents: {stats.get('total_documents', 0)}")

    # Test retrieval of coaching template
    print("\n4. Testing coaching template retrieval...")
    template_docs = rag.retrieve(
        query="Little's Law coaching template analysis structure", top_k=2
    )

    if template_docs:
        print(f"✅ Found {len(template_docs)} relevant documents")
        for idx, doc in enumerate(template_docs, 1):
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            print(f"\n   Document {idx}:")
            print(f"   Source: {metadata.get('source', 'Unknown')}")
            print(f"   Content length: {len(content)} chars")
            print(f"   Preview: {content[:200]}...")
    else:
        print("❌ No coaching template documents found")

    # Test retrieval of insight patterns
    print("\n5. Testing insight patterns retrieval...")
    pattern_docs = rag.retrieve(
        query="Little's Law insight patterns interpretation flow efficiency", top_k=2
    )

    if pattern_docs:
        print(f"✅ Found {len(pattern_docs)} relevant documents")
        for idx, doc in enumerate(pattern_docs, 1):
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            print(f"\n   Document {idx}:")
            print(f"   Source: {metadata.get('source', 'Unknown')}")
            print(f"   Content length: {len(content)} chars")
            print(f"   Preview: {content[:200]}...")
    else:
        print("❌ No insight pattern documents found")

    print("\n" + "=" * 80)
    print("✅ RAG Integration Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
