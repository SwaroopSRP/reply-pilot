# ReplyPilot — RAG Pipeline Specification

This document details the retrieval-augmented generation (RAG) architecture used in ReplyPilot to ground LLM responses in company policies.

---

## 1. Knowledge Base Corpus

The internal policy documents are stored as structured Markdown files in `data/knowledge/`:

| File | Title | Primary Coverage |
| :--- | :--- | :--- |
| `billing.md` | Billing & Invoicing Policy | Duplicate transactions, billing cycle dates, payment failure retries, invoice exports. |
| `refunds.md` | Refund & Return Policy | 14-day statutory refund window, non-refundable digital items, fee dispute guidelines. |
| `cancellation.md` | Subscription Cancellation | Self-service cancellation workflow, grace periods, data retention windows. |
| `escalation.md` | Support Escalation Tiers | Tier 1 vs Tier 2 criteria, lost/delayed packages, executive review triggers. |
| `product_faq.md` | Product Specifications & FAQ | Plan tiers (Starter, Pro, Enterprise), hardware warranty, shipment timelines. |
| `tone_guidelines.md` | Customer Communication Tone | Empathy standards, active voice, non-defensive language, structured sign-offs. |

---

## 2. Chunking Strategy

Standard character-count or token-window chunking often cuts sentences or separates policy clauses from their conditions. ReplyPilot implements **Section-Aware Markdown Chunking**:

1. **Header Parsing**: The parser scans for second-level Markdown headings (`## `).
2. **Context Preservation**: Each chunk includes the document title and the specific section title.
3. **Chunk Size Bounding**: Sections under 800 characters are kept intact. Larger sections are broken along paragraph boundaries with a 100-character sliding overlap.
4. **Metadata Attachment**: Every indexed chunk carries structured metadata:
   ```python
   {
       "doc_name": "billing.md",
       "doc_title": "Billing & Invoicing Policy",
       "section": "Duplicate Charges & Overbilling",
       "chunk_id": "billing.md_chunk_2"
   }
   ```

---

## 3. Embedding Model & Vector Index

- **Model**: `all-MiniLM-L6-v2` (`sentence-transformers`)
- **Dimensionality**: 384 dimensions
- **Compute Target**: CPU execution via PyTorch
- **Vector Database**: Embedded ChromaDB (`chromadb.PersistentClient`)
- **Storage Location**: `data/chroma/`
- **Distance Metric**: Cosine Distance

### Cosine Distance to Similarity Formula
Chroma returns the cosine distance $d \in [0, 2]$. ReplyPilot normalizes this distance into a human-readable similarity confidence score $s \in [0.0, 1.0]$:

$$s = \max(0.0, \min(1.0, 1.0 - d))$$

---

## 4. Latency & Offline Isolation

### Problem
Default initialization of HuggingFace `SentenceTransformer` attempts a remote network handshake to `huggingface.co` to check for newer model revisions. In air-gapped or latency-sensitive environments, this adds 5–10 seconds of cold network latency.

### Implementation
1. **Offline Mode**:
   ```python
   import os
   os.environ.setdefault("HF_HUB_OFFLINE", "1")
   ```
   Forces `transformers` to load the local weights immediately from cache.
2. **Pre-Warming on App Initialization**:
   During application bootstrap (`app.py`), a single warm-up query is dispatched:
   ```python
   query_knowledge_base("warmup query", top_k=1)
   ```
   This loads PyTorch model weights and initializes the Chroma index into memory once. Subsequent vector queries execute in **<10 milliseconds**.

---

## 5. Grounded Prompt Synthesis

Retrieved chunks are formatted as explicit contextual evidence before being fed to the LLM:

```text
=== RELEVANT COMPANY POLICIES (RAG EVIDENCE) ===
[Billing & Invoicing Policy > Duplicate Charges & Overbilling] (Relevance: 0.89)
If a customer is charged twice due to network timeout or retry:
1. Verify both transaction IDs in the payment ledger.
2. If confirmed duplicate, immediately initiate a full refund of the duplicate charge.
3. Processing turnaround: 3-5 business days.

[Customer Communication Tone > Empathy and Structure] (Relevance: 0.74)
Acknowledge the billing discrepancy clearly. Apologize for the inconvenience. State the exact refunded amount and expected arrival window.
```

The system prompt strictly commands the model:
> *"Do not extrapolate policies that are not present in the retrieved context. If the policy does not state an answer, acknowledge policy limitations and route to human review."*
