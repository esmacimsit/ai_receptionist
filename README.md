# AI Receptionist
Production-oriented, low-latency voice assistant

This project explores how to build a real-time AI receptionist by treating
AI models as components, not the product itself.

The focus is not on model size or hype, but on execution:
latency, cost, failure modes, and deterministic behavior in production.

This is an ongoing project. Design decisions are intentional and documented.

---

## Goals

- Real-time voice interaction (STT → NLU → response)
- Sub-second end-to-end latency
- Deterministic and controllable behavior
- Cost-aware deployment (small models, simple infrastructure)
- Clear separation between understanding and response generation

---

## High-Level Architecture

- Audio In
↓
- VAD (barge-in aware)
↓
- STT (self-hosted, small model)
↓
- NLU (LLM → JSON only)
↓
- Decision / State Logic
↓
- Deterministic Response
↓
- Audio Out

Key idea:
The LLM is only used for intent and slot extraction.
It never generates free-form responses.

---

## Core Design Decisions

### Small, Self-Hosted STT
- Optimized for latency, not raw accuracy
- Approximately 200ms latency (TR / EN)
- Accuracy is sufficient for downstream NLU

A slightly worse transcript is cheaper than a slower system.

---

### JSON-Only LLM Output
- LLM acts purely as an understanding layer
- Output schema is strict JSON:
  - intent
  - slots
  - confidence
  - next_action

This eliminates hallucinated responses and makes the system debuggable.

---

### Deterministic Responses
- No LLM text generation
- Responses are predefined or parameterized
- Predictable UX, easier testing, safer production behavior

---

### Aggressive Barge-In Handling
- User speech can interrupt system output
- State resets are explicit and logged
- Prevents talking over the user

---

### Latency and Cost Awareness
- Model size decisions are driven by:
  - latency budget
  - concurrency
  - GPU cost (T4-friendly)

Scaling the system is not the same as scaling the model.

---

## Tech Stack (Current)

- Python for orchestration and async pipelines
- Async I/O for overlapping wait time
- LLM used only for NLU
- Self-hosted STT
- Rust planned for latency-critical audio and VAD components

---

## Measurements (Work in Progress)

| Component        | Target |
|------------------|--------|
| STT latency      | ~200ms |
| End-to-end       | < 1s   |
| LLM output       | JSON only |
| Barge-in reaction| < 100ms |

---

## Current Status

- STT pipeline (TR / EN)
- Basic VAD
- JSON-based NLU
- Deterministic response logic
- Rust audio ingestion module (planned)
- Fine-tuning small LLM for scheduling logic (planned)
- Full latency breakdown and graphs (planned)
- Deployment notes (planned)

---

## Why This Project Exists

Most AI assistants optimize for:
- larger models
- better demos
- nicer conversations

This project optimizes for:
- execution correctness
- production constraints
- predictable behavior

It is part of a broader effort to build execution-literate AI systems.

---

## Disclaimer

This repository is under active development.
Interfaces and components may change as bottlenecks are discovered.

Design trade-offs are documented intentionally.
