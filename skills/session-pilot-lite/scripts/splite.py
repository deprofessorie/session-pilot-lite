#!/usr/bin/env python3
"""session-pilot-lite: ultra-fast, minimal-token memory & skill router.

Stdlib only, Python 3.8+. Designed for speed (<10ms), high accuracy, and tiny token footprint.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import time
from pathlib import Path

VERSION = "1.0.0"
HOME = Path(os.environ.get("SESSION_PILOT_LITE_HOME") or (Path.home() / ".session-pilot-lite"))
INDEX_FILE = HOME / "index.json"
SESS_DIR = HOME / "sessions"

GLOBAL_ROOTS = [
    ("~/.gemini/config/skills", "skill"),
    ("~/.gemini/antigravity/builtin/skills", "skill"),
    ("~/.gemini/skills", "skill"),
    ("~/.gemini/config/plugins", "plugin"),
    ("~/.claude/skills", "skill"),
    ("~/.claude/agents", "agent"),
    ("~/.claude/plugins", "plugin"),
    ("~/.codex/skills", "skill"),
    ("~/.agents/skills", "skill"),
    ("~/.cursor/skills", "skill"),
    ("~/.copilot/skills", "skill"),
]

PROJECT_ROOTS = [
    (".agents/skills", "skill"), (".claude/skills", "skill"),
    (".cursor/skills", "skill"), (".gemini/skills", "skill"),
    ("skills", "skill"),
]

INSTRUCTION_FILES = [
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules",
    ".windsurfrules", ".github/copilot-instructions.md", "README.md"
]

STOP = set("a an the and or but if then so to of in on at by for with from into onto about as is are was were be been do have i me my we you it this that there can will not no ok hey hi help how what when where which who why".split())

SYNONYMS = {
    "test": ["test", "unittest", "pytest", "spec", "jest", "axe"],
    "auth": ["auth", "jwt", "oauth", "login", "token", "security"],
    "db": ["db", "database", "sql", "postgres", "mysql", "sqlite", "prisma", "migration"],
    "api": ["api", "endpoint", "rest", "fastapi", "graphql", "route"],
    "clean": ["clean", "refactor", "format", "lint", "style"],
    "token": ["token", "compress", "compact", "context", "budget", "optimizer"],
    "pdf": ["pdf", "document", "extract"],
    "ui": ["ui", "frontend", "react", "vue", "tailwind", "css"],
}


def out(s=""):
    if sys.stdout:
        sys.stdout.write(s + "\n")


def stem(w):
    for suf in ("ing", "ers", "er", "ed", "es", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in STOP and len(w) > 1]


def load_json(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def atomic_write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, p)


def frontmatter(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            head = fh.read(3000)
    except OSError:
        return {}
    if not head.startswith("---"):
        return {}
    end = head.find("\n---", 3)
    if end == -1:
        return {}
    res = {}
    for line in head[3:end].splitlines():
        m = re.match(r"^(name|description):\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip().strip("'\"")
            if v and v not in (">", "|"):
                res[k] = v
    return res


def scan_root(root, kind):
    entries = []
    if kind == "agent":
        for f in sorted(root.glob("*.md")):
            fm = frontmatter(f)
            if fm:
                entries.append({"n": fm.get("name") or f.stem, "d": fm.get("description", ""), "k": "agent", "p": str(f)})
        return entries
    for c in sorted(root.iterdir()):
        if not c.is_dir():
            continue
        sk = c / "SKILL.md"
        if sk.is_file():
            fm = frontmatter(sk)
            entries.append({"n": fm.get("name") or c.name, "d": fm.get("description", ""), "k": "skill", "p": str(sk)})
        else:
            for g in c.iterdir():
                if g.is_dir() and (g / "SKILL.md").is_file():
                    fm = frontmatter(g / "SKILL.md")
                    entries.append({"n": fm.get("name") or g.name, "d": fm.get("description", ""), "k": "skill", "p": str(g / "SKILL.md")})
    return entries


def all_roots(cwd=None):
    roots = []
    if not os.environ.get("SESSION_PILOT_LITE_NO_DEFAULTS"):
        roots += [(Path(os.path.expanduser(p)), k, "global") for p, k in GLOBAL_ROOTS]
        base = Path(cwd or os.getcwd()).resolve()
        for d in [base] + list(base.parents)[:4]:
            for p, k in PROJECT_ROOTS:
                roots.append((d / p, k, "project"))
            if (d / ".git").exists():
                break
    for extra in filter(None, os.environ.get("SESSION_PILOT_LITE_ROOTS", "").split(os.pathsep)):
        roots.append((Path(os.path.expanduser(extra)), "skill", "extra"))
    seen, uniq = set(), []
    for p, k, s in roots:
        key = (str(p).lower(), k)
        if key not in seen and p.is_dir():
            seen.add(key)
            uniq.append((p, k, s))
    return uniq


def build_index(rebuild=False, cwd=None):
    cache = {} if rebuild else load_json(INDEX_FILE, {})
    old = cache.get("roots", {})
    now = time.time()
    fresh, items, changed = {}, [], False
    for root, kind, scope in all_roots(cwd):
        key = f"{kind}|{root}"
        try:
            mtime = root.stat().st_mtime
        except OSError:
            continue
        prev = old.get(key)
        if prev and prev.get("m") == mtime and now - prev.get("t", 0) < 86400:
            ents = prev["e"]
        else:
            ents, changed = scan_root(root, kind), True
            prev = {"m": mtime, "t": now, "e": ents}
        fresh[key] = prev
        for e in ents:
            items.append(dict(e, s=scope))
    if changed or set(fresh) != set(old):
        atomic_write(INDEX_FILE, {"v": VERSION, "roots": fresh})
    return items


def rank(items, query, k=2):
    raw_q = tokens(query)
    # Expand synonyms
    expanded_q = set(raw_q)
    for w in raw_q:
        if w in SYNONYMS:
            expanded_q.update(tokens(" ".join(SYNONYMS[w])))
    q = list(expanded_q)
    if not q or not items:
        return []

    docs = []
    for it in items:
        name_t = tokens(it["n"].replace("-", " ").replace("_", " "))
        body = name_t * 4 + tokens(it["d"])
        docs.append((it, body, set(name_t)))

    n = len(docs)
    avg = sum(len(b) for _, b, _ in docs) / n or 1.0
    df = {t: sum(1 for _, b, _ in docs if t in b) for t in q}
    qlow = query.lower()
    scored = []

    for it, body, names in docs:
        tf = {}
        for t in body:
            if t in df:
                tf[t] = tf.get(t, 0) + 1
        if not tf:
            continue
        s = 0.0
        for t, f in tf.items():
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * len(body) / avg))
        # Exact name hit gets strong boost
        if it["n"].lower() in qlow or it["n"].lower().replace("-", " ") in qlow:
            s *= 2.5
        # Scope boost (project > global)
        scope_mult = 1.4 if it.get("s") == "project" else 1.0
        cov = len(tf) / len(raw_q or q)
        scored.append((s * (0.5 + cov) * scope_mult, cov, it))

    scored.sort(key=lambda x: -x[0])
    best, seen = [], set()
    for s, cov, it in scored:
        if it["n"] not in seen:
            seen.add(it["n"])
            best.append((s, cov, it))
            if len(best) >= k:
                break
    return best


def detect_active_conversation():
    for ev in ("SESSION_PILOT_ID", "CONVERSATION_ID", "SESSION_ID", "CHAT_ID"):
        v = os.environ.get(ev)
        if v:
            return v, None
    brain_root = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_root.is_dir():
        candidates = []
        now = time.time()
        for d in brain_root.iterdir():
            if d.is_dir() and len(d.name) == 36 and d.name.count("-") == 4:
                tfile = d / ".system_generated" / "logs" / "transcript.jsonl"
                mtime = tfile.stat().st_mtime if tfile.is_file() else d.stat().st_mtime
                if now - mtime < 900:
                    candidates.append((mtime, d.name, str(d)))
        if candidates:
            candidates.sort(key=lambda x: -x[0])
            return candidates[0][1], candidates[0][2]
    return None, None


def session_id(arg):
    if arg:
        return re.sub(r"[^A-Za-z0-9._-]", "_", arg)[:100]
    if not os.environ.get("SESSION_PILOT_NO_AUTO_CONV"):
        cid, _ = detect_active_conversation()
        if cid:
            return re.sub(r"[^A-Za-z0-9._-]", "_", cid)[:100]
    return "auto-" + hashlib.sha1(os.getcwd().lower().encode()).hexdigest()[:10]


def gc_sessions():
    pruned = 0
    brain_root = Path.home() / ".gemini" / "antigravity" / "brain"
    for f in list(SESS_DIR.glob("*.json")):
        s = load_json(f, {})
        cwd = s.get("cwd")
        if cwd and not Path(cwd).exists():
            f.unlink()
            pruned += 1
            continue
        bdir = s.get("brain_dir")
        if bdir and not Path(bdir).exists():
            f.unlink()
            pruned += 1
            continue
        sid = s.get("id", f.stem)
        if brain_root.is_dir() and len(sid) == 36 and sid.count("-") == 4:
            if not (brain_root / sid).exists():
                f.unlink()
                pruned += 1
    return pruned


# ------------------------------------------------------------------ commands
def cmd_recall(a):
    sid = session_id(a.session)
    f = SESS_DIR / f"{sid}.json"
    s = load_json(f, None)
    if s:
        # Auto-verify existence of project
        if s.get("cwd") and not Path(s["cwd"]).exists():
            f.unlink()
            s = None
        elif s.get("brain_dir") and not Path(s["brain_dir"]).exists():
            f.unlink()
            s = None
    if not s:
        out(f"NEW SESSION {sid}")
        return
    cps = s.get("checkpoints", [])
    last = cps[-1] if cps else {}
    parts = [f"SESSION {sid}"]
    if s.get("goal"):
        parts.append(f"goal: {s['goal']}")
    if last.get("next"):
        parts.append(f"next: {last['next']}")
    out(" | ".join(parts))


def cmd_save(a):
    sid = session_id(a.session)
    now = int(time.time())
    cwd_str = str(Path(a.cwd or os.getcwd()).resolve())
    s = load_json(SESS_DIR / f"{sid}.json", None) or {"id": sid, "cwd": cwd_str, "checkpoints": []}
    s["cwd"] = cwd_str
    if a.goal:
        s["goal"] = a.goal[:140]
    if a.done or a.next:
        s["checkpoints"].append({"t": now, "done": (a.done or "")[:120], "next": (a.next or "")[:120]})
    s["checkpoints"] = s["checkpoints"][-5:]
    s["u"] = now
    # Track brain directory if Antigravity
    brain = Path.home() / ".gemini" / "antigravity" / "brain" / sid
    if brain.is_dir():
        s["brain_dir"] = str(brain)
    atomic_write(SESS_DIR / f"{sid}.json", s)
    out("ok")


def cmd_find(a):
    items = build_index(cwd=a.cwd)
    best = rank(items, a.query, k=a.k)
    if not best:
        out("match: none")
        return
    s, cov, it = best[0]
    scale = max(1.0, math.log(max(4, len(items))))
    conf = "strong" if cov >= 0.25 and s >= (1.5 * scale) else ("weak" if s >= (0.8 * scale) else "none")
    out(f"match: {conf} | {it['n']} ({it['p']})")
    for _, _, extra in best[1:]:
        out(f"alt: {extra['n']} ({extra['p']})")


def cmd_import(a):
    pdir = Path(a.path or os.getcwd()).resolve()
    if not pdir.is_dir():
        out("error: path not found")
        return
    found = []
    for rel in INSTRUCTION_FILES:
        f = pdir / rel
        if f.is_file():
            found.append(rel)
    # Wire bootstrap into AGENTS.md if absent
    agents_md = pdir / "AGENTS.md"
    snippet = "<!-- session-pilot-lite -->\nAt start of chat: run `splite.py recall`. On task: `splite.py find \"keywords\"`. Checkpoint: `splite.py save --done \"...\" --next \"...\"`.\n"
    if not agents_md.exists():
        agents_md.write_text("# Guidelines\n" + snippet, encoding="utf-8")
    else:
        txt = agents_md.read_text(encoding="utf-8", errors="replace")
        if "session-pilot-lite" not in txt:
            agents_md.write_text(txt.rstrip() + "\n\n" + snippet, encoding="utf-8")
    out(f"imported {pdir.name} (rules: {', '.join(found) or 'standard'})")


def cmd_gc(a):
    n = gc_sessions()
    out(f"pruned {n}")


def cmd_index(a):
    items = build_index(rebuild=a.rebuild)
    out(f"indexed {len(items)}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="splite.py", description="session-pilot-lite helper")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("recall")
    r.add_argument("--session")
    r.set_defaults(fn=cmd_recall)

    s = sub.add_parser("save")
    s.add_argument("--session")
    s.add_argument("--cwd")
    s.add_argument("--goal")
    s.add_argument("--done")
    s.add_argument("--next")
    s.add_argument("--skill")
    s.set_defaults(fn=cmd_save)

    f = sub.add_parser("find")
    f.add_argument("query")
    f.add_argument("-k", type=int, default=1)
    f.add_argument("--cwd")
    f.set_defaults(fn=cmd_find)

    sub.add_parser("gc").set_defaults(fn=cmd_gc)

    imp = sub.add_parser("import")
    imp.add_argument("path", nargs="?", default=None)
    imp.set_defaults(fn=cmd_import)

    idx = sub.add_parser("index")
    idx.add_argument("--rebuild", action="store_true")
    idx.set_defaults(fn=cmd_index)

    a = p.parse_args(argv)
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    a.fn(a)


if __name__ == "__main__":
    main()
