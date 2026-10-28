#!/usr/bin/env python3
"""session-pilot-lite multi-client installer (Antigravity, Claude, Codex, Gemini, Cursor, Copilot)."""
import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_SRC = ROOT / "skills" / "session-pilot-lite"

CLIENTS = {
    "antigravity": {
        "skill": Path.home() / ".gemini" / "config" / "skills" / "session-pilot-lite",
        "rule_file": Path.home() / ".gemini" / "config" / "AGENTS.md",
        "gemini_md": Path.home() / ".gemini" / "config" / "GEMINI.md",
    },
    "claude": {
        "skill": Path.home() / ".claude" / "skills" / "session-pilot-lite",
        "rule_file": Path.home() / ".claude" / "CLAUDE.md",
    },
    "codex": {
        "skill": Path.home() / ".codex" / "skills" / "session-pilot-lite",
        "rule_file": Path.home() / ".codex" / "AGENTS.md",
    },
    "gemini": {
        "skill": Path.home() / ".gemini" / "skills" / "session-pilot-lite",
        "rule_file": Path.home() / ".gemini" / "GEMINI.md",
    },
    "cursor": {
        "skill": Path.home() / ".cursor" / "skills" / "session-pilot-lite",
        "rule_file": Path.home() / ".cursor" / "rules" / "session-pilot-lite.mdc",
    },
    "copilot": {
        "skill": Path.home() / ".copilot" / "skills" / "session-pilot-lite",
        "rule_file": Path.home() / ".github" / "copilot-instructions.md",
    },
}

START_MARKER = "<!-- session-pilot-lite:start -->"
END_MARKER = "<!-- session-pilot-lite:end -->"


def build_rule(script_path):
    return (
        f"{START_MARKER}\n"
        "## Session Pilot Lite (always on)\n\n"
        f"At start of turn: `python {script_path} recall`.\n"
        f"On task: `python {script_path} find \"<3-6 keywords>\"`.\n"
        f"After progress: `python {script_path} save --done \"<done>\" --next \"<next>\"`.\n"
        f"{END_MARKER}\n"
    )


def inject_rule(file_path, rule_text):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_text(rule_text, encoding="utf-8")
        return True
    content = file_path.read_text(encoding="utf-8", errors="replace")
    if START_MARKER in content and END_MARKER in content:
        start = content.index(START_MARKER)
        end = content.index(END_MARKER) + len(END_MARKER)
        content = content[:start].rstrip() + "\n\n" + rule_text + content[end:].lstrip()
    else:
        content = content.rstrip() + "\n\n" + rule_text
    file_path.write_text(content, encoding="utf-8")
    return True


def install_client(name, with_rule=False, dry_run=False):
    cfg = CLIENTS.get(name)
    if not cfg:
        print(f"Unknown client: {name}")
        return False
    dest = cfg["skill"]
    rule_file = cfg.get("rule_file")
    script = dest / "scripts" / "splite.py"
    rule_text = build_rule(str(script))

    if dry_run:
        print(f"[dry-run] Install skill -> {dest}")
        if with_rule and rule_file:
            print(f"[dry-run] Add always-on rule -> {rule_file}")
        return True

    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_SRC, dest)
    print(f"Installed {name} skill -> {dest}")

    if with_rule and rule_file:
        inject_rule(rule_file, rule_text)
        print(f"Wired always-on rule -> {rule_file}")
        if cfg.get("gemini_md"):
            inject_rule(cfg["gemini_md"], rule_text)
            print(f"Wired always-on rule -> {cfg['gemini_md']}")
    return True


def main():
    p = argparse.ArgumentParser(description="Install session-pilot-lite")
    p.add_argument("--client", choices=list(CLIENTS.keys()) + ["all"], default="antigravity")
    p.add_argument("--with-rule", action="store_true", help="Inject always-on rule into client rule files")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = list(CLIENTS.keys()) if args.client == "all" else [args.client]
    for t in targets:
        install_client(t, with_rule=args.with_rule, dry_run=args.dry_run)
    print("Done!")


if __name__ == "__main__":
    main()
