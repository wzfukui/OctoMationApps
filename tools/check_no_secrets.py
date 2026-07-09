# -*- coding: utf-8 -*-
"""Fail fast when local env files, key material, or obvious secrets appear.

This is intentionally dependency-free so it can run in GitHub Actions and local
developer shells before packaging app directories.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__MACOSX",
    "__pycache__",
    "htmlcov",
}
SKIP_SUFFIXES = {
    ".gif",
    ".ico",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".png",
    ".pyc",
    ".zip",
}
ALLOWED_ENV_SAMPLES = {
    ".env.example",
    ".env.sample",
}
FORBIDDEN_NAME_PATTERNS = (
    re.compile(r"(^|/)\.env(\..+)?$"),
    re.compile(r"(^|/).+_access_token\.json$", re.IGNORECASE),
    re.compile(r"(^|/).*(credentials?|secrets?)\.(json|ya?ml|toml|ini|env)$", re.IGNORECASE),
)
FORBIDDEN_SUFFIXES = {
    ".crt",
    ".csr",
    ".db",
    ".jks",
    ".key",
    ".keystore",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
}
SECRET_CONTENT_PATTERNS = (
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----\s+"
        r"[A-Za-z0-9+/=\s]{80,}"
        r"-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(
        r"""(?ix)
        \b(access[_-]?token|refresh[_-]?token|api[_-]?key|secret|client[_-]?secret|
        corpsecret|private[_-]?key|password|passwd)\b
        \s*["']?\s*[:=]\s*["']([A-Za-z0-9_./+=:-]{20,})["']
        """
    ),
)


def git_files(cwd: Path) -> set[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "--others", "--cached", "--exclude-standard"],
        cwd=str(cwd),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return {Path(line) for line in proc.stdout.splitlines() if line.strip()}


def iter_files(paths: list[Path], cwd: Path) -> list[Path]:
    if paths:
        result: list[Path] = []
        for raw in paths:
            path = raw if raw.is_absolute() else cwd / raw
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        result.append(child.relative_to(cwd))
            elif path.is_file():
                result.append(path.relative_to(cwd))
        return sorted(set(result), key=lambda item: item.as_posix())
    return sorted(git_files(cwd), key=lambda item: item.as_posix())


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return path.suffix.lower() in SKIP_SUFFIXES


def name_findings(path: Path) -> list[str]:
    rel = path.as_posix()
    if path.name in ALLOWED_ENV_SAMPLES:
        return []
    findings = []
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        findings.append("forbidden secret/runtime file suffix")
    for pattern in FORBIDDEN_NAME_PATTERNS:
        if pattern.search(rel):
            findings.append("forbidden secret/runtime file name")
            break
    return findings


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def content_findings(path: Path) -> list[str]:
    text = read_text(path)
    if text is None:
        return []
    findings = []
    for pattern in SECRET_CONTENT_PATTERNS:
        if pattern.search(text):
            findings.append("possible secret value in file content")
            break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for env files and obvious secrets.")
    parser.add_argument("paths", nargs="*", type=Path, help="optional paths to scan; defaults to git tracked and untracked files")
    args = parser.parse_args()

    cwd = Path.cwd()
    failures = []
    for rel_path in iter_files(args.paths, cwd):
        full_path = cwd / rel_path
        if not full_path.exists():
            continue
        if should_skip(rel_path):
            continue
        reasons = name_findings(rel_path) + content_findings(full_path)
        for reason in reasons:
            failures.append(f"{rel_path}: {reason}")

    if failures:
        print("Secret/env guard failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Secret/env guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
