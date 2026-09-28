"""RAG pipeline for ReplyPilot company knowledge retrieval.

Handles:
- Markdown document loading from data/knowledge/
- Section-aware chunking preserving header metadata
- Local embedding generation using HuggingFace all-MiniLM-L6-v2
- Persistent ChromaDB collection management
- Semantic similarity retrieval for policy grounding
"""

import os
# Prevent HuggingFace from making slow remote network requests when model is cached
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from pathlib import Path
from typing import Any, Optional
import chromadb
from chromadb.utils import embedding_functions

from core.config import settings

# Global in-memory cache for vector store collection and embedding function
_chroma_client: Optional[chromadb.PersistentClient] = None
_knowledge_collection = None
_embedding_fn = None


def get_embedding_function():
    """Initialize and cache the HuggingFace sentence-transformers embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
    return _embedding_fn


def get_chroma_client() -> chromadb.PersistentClient:
    """Initialize and cache local persistent ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        settings.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_PATH))
    return _chroma_client


def load_knowledge_documents() -> list[dict[str, Any]]:
    """Load and parse markdown policy documents into structured chunks with section metadata.
    
    Splits each markdown file by top-level (#) and sub-level (##) headers
    so each chunk contains accurate source and section context.
    """
    knowledge_dir = settings.KNOWLEDGE_PATH
    if not knowledge_dir.exists():
        return []

    chunks: list[dict[str, Any]] = []

    for file_path in sorted(knowledge_dir.glob("*.md")):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        doc_title = file_path.stem.replace("_", " ").title() + " Policy"
        lines = content.split("\n")
        current_section = "General"
        section_lines: list[str] = []

        for line in lines:
            if line.startswith("# "):
                doc_title = line.replace("# ", "").strip()
            elif line.startswith("## "):
                # Flush previous section
                if section_lines:
                    section_text = "\n".join(section_lines).strip()
                    if section_text:
                        chunks.append({
                            "doc_name": file_path.name,
                            "doc_title": doc_title,
                            "section": current_section,
                            "content": section_text,
                        })
                    section_lines = []
                current_section = line.replace("## ", "").strip()
            else:
                section_lines.append(line)

        # Flush final section
        if section_lines:
            section_text = "\n".join(section_lines).strip()
            if section_text:
                chunks.append({
                    "doc_name": file_path.name,
                    "doc_title": doc_title,
                    "section": current_section,
                    "content": section_text,
                })

    return chunks


def initialize_vector_store(force_reindex: bool = False):
    """Ensure ChromaDB collection exists, is populated with policies, and cached.
    
    Avoids rebuilding embeddings on every Streamlit rerun.
    """
    global _knowledge_collection
    client = get_chroma_client()
    emb_fn = get_embedding_function()

    if force_reindex:
        try:
            client.delete_collection(name=settings.CHROMA_COLLECTION)
        except Exception:
            pass
        _knowledge_collection = None

    collection = client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Check if already populated
    if collection.count() == 0 or force_reindex:
        raw_chunks = load_knowledge_documents()
        if raw_chunks:
            ids = [f"chunk_{i}_{chunk['doc_name']}_{i}" for i, chunk in enumerate(raw_chunks)]
            documents = [
                f"[{chunk['doc_title']} - {chunk['section']}]\n{chunk['content']}"
                for chunk in raw_chunks
            ]
            metadatas = [
                {
                    "doc_name": chunk["doc_name"],
                    "doc_title": chunk["doc_title"],
                    "section": chunk["section"],
                }
                for chunk in raw_chunks
            ]
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

    _knowledge_collection = collection
    return _knowledge_collection


def query_knowledge_base(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Retrieve top-k most relevant policy sections from Chroma with formatted similarity scores."""
    collection = initialize_vector_store(force_reindex=False)
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    formatted_results: list[dict[str, Any]] = []
    if not results or not results["documents"] or not results["documents"][0]:
        return formatted_results

    documents = results["documents"][0]
    metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
    distances = results["distances"][0] if results.get("distances") else [0.5] * len(documents)

    for doc_text, meta, dist in zip(documents, metadatas, distances):
        # Convert cosine distance to similarity score in [0.0, 1.0]
        similarity = max(0.0, min(1.0, 1.0 - float(dist)))
        formatted_results.append({
            "content": doc_text,
            "source": meta.get("doc_title", "Company Policy"),
            "section": meta.get("section", "General"),
            "doc_name": meta.get("doc_name", ""),
            "similarity": round(similarity, 2),
        })

    return formatted_results


def get_knowledge_documents_overview() -> list[dict[str, Any]]:
    """Provide summary of loaded knowledge documents for the Knowledge UI view."""
    knowledge_dir = settings.KNOWLEDGE_PATH
    if not knowledge_dir.exists():
        return []

    collection = initialize_vector_store(force_reindex=False)
    total_chunks = collection.count()

    overview = []
    doc_descriptions = {
        "billing.md": "Guidelines on duplicate charges, recurring billing cycles, payment failures, and tax invoices.",
        "refunds.md": "14-day refund policy, non-refundable categories, exceptions, and credit turnaround times.",
        "cancellation.md": "Self-service cancellation procedures, billing period cutoff dates, and data retention rules.",
        "escalation.md": "Tier 1 vs Tier 2 triggers, delayed shipment investigations, dispute handling, and human review mandates.",
        "product_faq.md": "Starter, Pro, and Enterprise plan limits, hardware delivery expectations, and warranty specifications.",
        "tone_guidelines.md": "Internal tone of voice standards: empathetic, direct, transparent, and grounded copilot principles.",
    }

    for file_path in sorted(knowledge_dir.glob("*.md")):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Count sections
        sections = [l.strip("# ").strip() for l in lines if l.startswith("## ")]
        title = lines[0].replace("# ", "").strip() if lines else file_path.stem.title()

        overview.append({
            "filename": file_path.name,
            "title": title,
            "description": doc_descriptions.get(file_path.name, "Company internal documentation."),
            "sections_count": len(sections),
            "sections": sections,
        })

    return overview
