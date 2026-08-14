#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only
"""Regenerate the ``## [Unreleased]`` section of ``CHANGELOG.md``.

This script is intended to be run in CI. It only rewrites the
``## [Unreleased]`` block from the commits merged since the most recent
stable release tag. The released version history below the next ``---`` is
left untouched.

It groups commit subjects (conventional-commits prefixes) into Keep a
Changelog categories (Added / Changed / Fixed / Removed / ...).
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"

CHANGELOG_MARKER = "## [Unreleased]"

TYPE_MAP = [
    (re.compile(r"^feat[!:]", re.I), "Added"),
    (re.compile(r"^fix[!:]", re.I), "Fixed"),
    (re.compile(r"^rem[!:]", re.I), "Removed"),
    (re.compile(r"^chg[!:]", re.I), "Changed"),
    (re.compile(r"^perf[!:]", re.I), "Changed"),
    (re.compile(r"^refactor[!:]", re.I), "Changed"),
    (re.compile(r"^docs[!:]", re.I), "Documentation"),
    (re.compile(r"^test[!:]", re.I), "Testing"),
]

GROUP_ORDER = ["Added", "Changed", "Fixed", "Removed", "Documentation", "Testing", "Other"]


def _git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True)


def latest_stable_tag():
    """Return the newest tag like ``X.Y.Z`` (stable, not rc/dev), or None."""
    for tag in _git("tag", "--sort=-v:refname").splitlines():
        if re.fullmatch(r"\d+\.\d+\.\d+", tag.strip()):
            return tag.strip()
    return None


def commit_records(base):
    if base:
        log = _git("log", "{}..HEAD".format(base), "--format=%h %s")
    else:
        log = _git("log", "HEAD", "--format=%h %s")
    for line in log.splitlines():
        line = line.strip()
        if not line:
            continue
        hash_, _, subject = line.partition(" ")
        yield hash_, subject


def build_unreleased(base):
    grouped = {}
    for hash_, subject in commit_records(base):
        group = "Other"
        for rx, category in TYPE_MAP:
            if rx.match(subject):
                group = category
                break
        grouped.setdefault(group, []).append((subject, hash_))

    lines = [CHANGELOG_MARKER, ""]
    if not grouped:
        lines.append("- No notable changes yet.")
        return "\n".join(lines)

    for group in GROUP_ORDER:
        entries = grouped.get(group)
        if not entries:
            continue
        lines.append("### {}".format(group))
        for subject, hash_ in entries:
            lines.append("- {} ({})".format(subject, hash_))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    base = latest_stable_tag()
    block = build_unreleased(base)

    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.find(CHANGELOG_MARKER)
    if start < 0:
        print("No '{}' marker found in CHANGELOG.md".format(CHANGELOG_MARKER))
        return 1

    end = text.find("\n---", start)
    if end < 0:
        end = len(text)

    new_text = text[:start] + block + text[end:]
    CHANGELOG.write_text(new_text, encoding="utf-8")
    print("CHANGELOG.md updated (base tag: {})".format(base))
    return 0


if __name__ == "__main__":
    sys.exit(main())
