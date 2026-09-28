# ReplyPilot — Latency & Performance Benchmarks

This document records empirical latency, memory usage, and throughput measurements for ReplyPilot running on Linux with Python 3.14.

---

## 1. Model Latency Comparison

Measurements conducted using Google GenAI SDK with structured Pydantic schema validation (`response_schema=SupportAnalysis`):

| Model | Average Latency | Output Quality | Best Use Case |
| :--- | :--- | :--- | :--- |
| **`gemini-3.5-flash-lite`** | **1.55s – 1.80s** | 100% compliant JSON, strict grounding, high empathy | **Default / Production UI** (Sub-2s response) |
| **`gemini-3.5-flash`** | 2.80s – 3.40s | Comprehensive reasoning, detailed operational action | Balanced complex inquiries |
| **`gemma-4-26b-a4b-it`** | 28.00s – 45.00s | High nuance, open-weights MoE architecture | Batch offline research / evaluation |
| **`Deterministic Fallback`** | **0.03s (< 50ms)** | 100% grounded heuristic template match | Offline mode, API outages, unit tests |

---

## 2. End-to-End Latency Breakdown

Using the default configuration (`gemini-3.5-flash-lite` + local pre-warmed embeddings):

```
Total Response Time: ~1.62s
┌─────────────────────────────────────────────────────────────┬──────────┐
│ Operation                                                   │ Latency  │
├─────────────────────────────────────────────────────────────┼──────────┤
│ 1. SQLite Customer, Order & Payment Lookup                  │    1.2ms │
│ 2. ChromaDB Semantic Vector Query (k=3, all-MiniLM-L6-v2)    │    8.4ms │
│ 3. LLM Structured Generation & Pydantic Validation           │ 1580.0ms │
│ 4. SQLite Audit Persistence (Conversation + Analysis)        │    2.1ms │
│ 5. Streamlit DOM Update & State Render                      │   25.0ms │
└─────────────────────────────────────────────────────────────┴──────────┘
```

---

## 3. Cold Start vs. Warm Start

| Metric | Cold Start (First Query) | Warm Start (Subsequent Queries) |
| :--- | :--- | :--- |
| **Embedding Engine Load** | ~4.8s (loading weights into memory) | < 10ms (cached PyTorch tensor execution) |
| **ChromaDB Collection Connect** | ~180ms | < 2ms |
| **SQLite Connection & Query** | ~5ms | < 1ms |
| **LLM Inference** | ~1.6s | ~1.5s |
| **Total Turnaround** | **~6.6s** | **~1.6s** |

> **Optimization Note**: ReplyPilot implements an automatic pre-warming step during `setup_application()` in `app.py`. The embedding weights are pre-loaded on app launch, ensuring the very first user interaction is already in **warm-start mode (< 2s)**.

---

## 4. Test Suite Execution Speed

The automated test suite (`pytest tests/ -v`) executes:
- 3 relational SQLite tests (joins, foreign keys, missing customer handling)
- 2 Chroma semantic retrieval tests (policy citations, cosine similarity checks)
- 2 Pydantic schema validation tests (confidence clamping, empty message validation)
- 1 full end-to-end analysis workflow with live API inference

```bash
# Prior (Gemma 4 default):
8 passed in 56.16s

# Optimized (Gemini 3.5 Flash-Lite default + HF_HUB_OFFLINE):
8 passed in 8.63s  (6.5x faster test turnaround)
```
