# 📚 TraceIQ Beginner Learning & Architecture Guide

Welcome! This documentation series is specifically created so you can **understand every concept, architecture decision, and code structure** behind TraceIQ from first principles.

Whether you are new to Retrieval-Augmented Generation (RAG), vector databases, or microservice architecture, this guide explains each component step-by-step.

---

## 🗺️ Learning Roadmap

| Guide | Description | What You Will Learn |
| :--- | :--- | :--- |
| **[01. What is RAG & TraceIQ?](./01_what_is_rag_and_traceiq.md)** | The fundamentals of RAG and why we are building TraceIQ | LLM limitations, what RAG is, why simple RAG fails in engineering, and the 5 multi-source evidence types. |
| **[02. Architecture & Technical Deep Dive](./02_architecture_and_deep_dive.md)** | Technical design & algorithms | MongoDB Vector Search, Full-Text Search, Hybrid RRF Search, Embeddings, and LangChain orchestration. |
| **[03. Codebase Tour & File Guide](./03_codebase_tour_and_file_guide.md)** | Tour of this repository | What every folder and file in `backend/` and `frontend/` does and how they interact. |
| **[04. The 4 Judge Evaluation Scenarios](./04_the_four_judge_evaluation_tests.md)** | Hackathon benchmark scenarios | The 4 specific challenges judges will test: Cross-source synthesis, Exact keyword lookup, Contradictory evidence, and Abstention. |

---

## 💡 How to Use These Documents
1. **Read in order**: Start with Guide 01 and progress sequentially.
2. **Experiment alongside**: Refer back to the codebase files linked throughout the text.
3. **Ask questions**: Every time we complete a phase or feature, we will discuss the concepts behind it before moving to the next.
