#!/usr/bin/env python3
"""Regenerate per-tool skill wrappers from the canonical skills/ directory.

Canonical source: skills/<name>/SKILL.md (Claude format).
Outputs:
  - .github/prompts/<name>.prompt.md           (Copilot slash-command prompts)
  - .agents/skills                              (symlink → ../skills, or copy on Windows)

Run this after editing any SKILL.md or adding a new skill.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
PROMPTS_DIR = REPO_ROOT / ".github" / "prompts"
AGENTS_SKILLS = REPO_ROOT / ".agents" / "skills"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*(.+(?:\n[ \t]+.+)*)$", re.MULTILINE)


def parse_skill(skill_md: Path) -> tuple[str, str, str]:
    """Return (name, description, body) from a SKILL.md file."""
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{skill_md} is missing YAML frontmatter")
    fm = match.group(1)
    body = text[match.end():]

    name_match = NAME_RE.search(fm)
    desc_match = DESC_RE.search(fm)
    if not name_match or not desc_match:
        raise ValueError(f"{skill_md} frontmatter must define both 'name' and 'description'")
    return (
        name_match.group(1).strip(),
        " ".join(desc_match.group(1).split()),
        body,
    )


def rewrite_reference_links(body: str, skill_name: str) -> str:
    """Rewrite relative reference/ paths so they resolve from .github/prompts/.

    Copilot prompt files live at .github/prompts/<name>.prompt.md.
    Reference files live at skills/<name>/reference/...
    Convert "reference/foo.md" → "../../skills/<name>/reference/foo.md".
    """
    return re.sub(
        r"(`?)reference/([\w./-]+)(`?)",
        rf"\1../../skills/{skill_name}/reference/\2\3",
        body,
    )


def write_copilot_prompt(name: str, description: str, body: str) -> Path:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    rewritten = rewrite_reference_links(body, name)
    # Single-quote the description, escaping any embedded single quotes per YAML spec.
    desc_yaml = "'" + description.replace("'", "''") + "'"
    content = (
        "---\n"
        f"description: {desc_yaml}\n"
        f"name: '{name}'\n"
        "agent: 'agent'\n"
        "---\n"
        f"<!-- GENERATED from skills/{name}/SKILL.md by scripts/sync-skills.py. Do not edit by hand. -->\n"
        f"{rewritten}"
    )
    out = PROMPTS_DIR / f"{name}.prompt.md"
    out.write_text(content, encoding="utf-8")
    return out


def ensure_agents_skills() -> str:
    """Symlink .agents/skills → ../skills, or copy on platforms without symlinks."""
    AGENTS_SKILLS.parent.mkdir(parents=True, exist_ok=True)

    if AGENTS_SKILLS.is_symlink() or AGENTS_SKILLS.exists():
        if AGENTS_SKILLS.is_symlink():
            return f"symlink already in place: {AGENTS_SKILLS} → {os.readlink(AGENTS_SKILLS)}"
        # Refuse to clobber a non-symlink — could be a Windows materialized copy with edits.
        return f"exists as non-symlink (Windows mode?): {AGENTS_SKILLS}"

    if platform.system() == "Windows":
        shutil.copytree(SKILLS_DIR, AGENTS_SKILLS)
        return f"copied skills/ → {AGENTS_SKILLS} (Windows fallback; re-run after edits)"

    AGENTS_SKILLS.symlink_to(Path("..") / "skills", target_is_directory=True)
    return f"created symlink {AGENTS_SKILLS} → ../skills"


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"error: {SKILLS_DIR} does not exist", file=sys.stderr)
        return 1

    skills = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    if not skills:
        print(f"error: no skills found under {SKILLS_DIR}", file=sys.stderr)
        return 1

    print(ensure_agents_skills())

    for skill_dir in skills:
        name, description, body = parse_skill(skill_dir / "SKILL.md")
        out = write_copilot_prompt(name, description, body)
        print(f"wrote {out.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
