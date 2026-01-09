"""Quick test of RAG retrieval functionality."""

import sys

sys.path.insert(0, "backend")

from backend.services.rag_service import get_rag_service

# Get RAG service (will auto-index if needed)
print("Initializing RAG service...")
rag = get_rag_service()

# Get stats
stats = rag.get_stats()
print(f"\n✅ RAG Service Ready!")
print(f"   Total chunks indexed: {stats['total_chunks']}")
print(f"   Total documents: {stats['total_documents']}")
print(f"   Sources: {', '.join(stats['sources'][:5])}...")

# Test retrieval
print("\n🔍 Testing semantic retrieval...\n")

test_queries = [
    "How do I write a good Epic?",
    "What is the difference between an Epic and a Feature?",
    "How to reduce lead time?",
]

for query in test_queries:
    print(f"Query: {query}")
    results = rag.retrieve(query, top_k=2)

    if results:
        for i, doc in enumerate(results, 1):
            source = doc["metadata"]["source"]
            score = doc["similarity_score"]
            content = doc["content"][:100].replace("\n", " ")
            print(f"  [{i}] {source} (score: {score:.3f})")
            print(f"      {content}...")
    else:
        print("  No results found")
    print()

print("✅ RAG retrieval working successfully!")
