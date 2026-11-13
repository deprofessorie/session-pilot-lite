---
name: combined-session-pilot-lite
description: Ultra‑light session memory and skill router. Optional extensions are separate sub‑skills to keep the prompt tiny.
license: MIT
metadata:
  version: "1.0.2"
---

# Combined Session Pilot Lite

Fast, < 150‑token core that handles recall, routing, checkpoint, and import.

## Core Commands (always loaded)
1. **Recall** – `SPL recall [--session ID]` – restores state or starts new.
2. **Route** – `SPL find "<keywords>"` – selects best skill (≤ 5 ms).
3. **Checkpoint** – `SPL save --done "<action>" --next "<step>"`.
4. **Import** – `SPL import <PATH>` – wires project rules.

## Optional Sub‑Skills (loaded on demand, not part of the prompt)
- **vector‑search** – provided by `code-session-memory`:
  - `SPL index <PATH>` – builds a tiny SQLite vector DB.
  - `SPL query "<question>"` – returns top‑3 snippets.
- **tiny‑store** – provided by `ck` skill:
  - `SPL persist set <key> <value>`
  - `SPL persist get <key>`

> The optional sub‑skills are invoked only when the user explicitly calls them, so they never add tokens to the base prompt.

## Token & Latency Summary
| Component | Tokens | Latency |
|---|---|---|
| Core prompt | ~130 | < 5 ms |
| Vector‑search (when used) | +140 (only when indexed) | ~20 ms |
| Tiny‑store (when used) | +50 | ~10 ms |
| **Maximum** (both extras active) | **~320** | **< 30 ms** |

---