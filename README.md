# Session Pilot Lite ⚡

**Ultra-fast, minimal-token memory and skill router for lightweight AI coding tasks.**

Session Pilot Lite is the stripped-down, high-velocity edition of [Session Pilot](https://github.com/deprofessorie/session-pilot). Engineered for speed (<10ms), laser-focused accuracy, and near-zero token consumption, it keeps your context window pure while maintaining seamless conversation memory.

```
you: "add jwt auth"
        │
        ├─ recall  → "SESSION my-chat | next: write tests"   (~15 tokens)
        ├─ find    → "match: strong | fastapi-patterns"      (~20 tokens)
        └─ save    → "ok"                                    (1 token!)
```

## Why Lite?

| Metric | Session Pilot (Full) | Session Pilot Lite ⚡ |
| --- | --- | --- |
| **`SKILL.md` Prompt Size** | ~1,200 tokens | **~280 tokens** (-75%) |
| **Search Response Time** | ~40–50 ms | **< 10 ms** (5x faster) |
| **Helper Token Output** | 60–200 tokens | **10–35 tokens** |
| **`save` Command Ack** | `saved <id>` | **`ok`** (1 token) |
| **Dependencies** | Python 3.8+ (stdlib) | Python 3.8+ (stdlib, single file) |
| **Accuracy Boosts** | BM25 + Scope Rank | **BM25 + Synonym Expansion + Exact Word Multipliers** |
| **Best For** | Heavy workspaces & complex teams | **Daily coding, fast iterations & light models** |

---

## Features

- ⚡ **Instant Recall (<5ms):** Resumes right from your last `next:` item in a single 15-token line.
- 🎯 **Synonym-Boosted Routing:** Automatically maps domain intent (e.g. `api` → `fastapi/rest/graphql`, `db` → `sql/postgres/prisma`, `test` → `unittest/pytest/jest`).
- 🧹 **Automatic Lifecycle & GC:** If you delete a project folder or a chat conversation, memory is instantly purged on recall.
- 📦 **Zero Dependencies:** Pure Python standard library, cross-platform (Windows, macOS, Linux).
- 🔌 **Universal Client Support:** Antigravity, Claude Code, Gemini CLI, Codex CLI, Cursor, and GitHub Copilot.

---

## 1-Command Install

```bash
git clone https://github.com/deprofessorie/session-pilot-lite.git
cd session-pilot-lite

# Install for Antigravity with always-on rule
python install.py --client antigravity --with-rule

# Or Claude Code / Codex / Gemini / Cursor
python install.py --client claude --with-rule
python install.py --client codex --with-rule
python install.py --client gemini --with-rule
python install.py --client cursor --with-rule
python install.py --client all --with-rule
```

---

## CLI Reference

```bash
SPL="python skills/session-pilot-lite/scripts/splite.py"

$SPL recall --session my-chat               # 1-line memory state
$SPL save --session my-chat --done "auth"   # outputs: "ok"
$SPL find "api testing"                     # instant top match
$SPL import /path/to/project                # wire rules & scan instructions
$SPL gc                                     # purge deleted projects/chats
$SPL index --rebuild                        # refresh cached tool index
```

---

## License

MIT © 2026 deProfessori
