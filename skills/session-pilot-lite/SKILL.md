---
name: session-pilot-lite
description: Ultra-fast, minimal-token memory and skill router for light tasks. Recalls chat state, picks the best skill in <10ms, and checkpoints progress with near-zero token overhead.
license: MIT
metadata:
  version: "1.0.0"
---

# Session Pilot Lite

Minimal-token memory & skill scout for fast turns.
`SPL` = `python <this_folder>/scripts/splite.py` (Python 3.8+ stdlib).

## Every Turn

1. **Recall (first turn or resumed chat):**
   Run `SPL recall [--session ID]`. If `NEW SESSION`, start fresh. Otherwise continue from `next:`.

2. **Route (tasks only — skip for greetings & Q&A):**
   Run `SPL find "<3-6 keywords>"`.
   - `match: strong` → read only the returned SKILL.md path and follow it.
   - `match: none` → proceed with general AI capability or ask user.

3. **Checkpoint (after meaningful progress):**
   Run `SPL save [--session ID] --done "<action>" --next "<step>" [--goal "<one line>"]`.

## Project Import
When opening an imported repo, run `SPL import [PATH]` to wire rules and check instructions.
Deleted chats/projects are auto-pruned on recall.
