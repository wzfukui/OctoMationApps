# -*- coding: utf-8 -*-
"""Package changed Shakespeare app directories into release/*.zip.

The script is designed for GitHub Actions but can also be run locally.
It detects app directories changed between two git revisions, creates zip
archives that keep the app directory as the archive root, and writes them to a
release directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path


APP_DIR_RE = re.compile(r"^(shakespeare-(?:action|app)-[A-Za-z0-9_.-]+|Archived/shakespeare-(?:action|app)-[A-Za-z0-9_.-]+)$")
ZERO_SHA = "0" * 40
DEFAULT_EXCLUDE_NAMES = {
    ".DS_Store",
    ".coverage",
    ".env",
    ".env.local",
    ".env.production",
    ".venv",
    "__MACOSX",
    "__pycache__",
    "ENV",
    "env",
    "htmlcov",
    "venv",
    "coverage.xml",
    "nosetests.xml",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".git",
    ".github",
}
DEFAULT_EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".pem",
    ".key",
    ".crt",
    ".csr",
    ".p12",
    ".pfx",
    ".jks",
    ".keystore",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".coverage",
    ".zip",
}
DEFAULT_EXCLUDE_FILE_PATTERNS = (
    re.compile(r"(^|/)\.env(\..*)?$"),
    re.compile(r"(^|/).+_access_token\.json$", re.IGNORECASE),
    re.compile(r"(^|/).*(credentials?|secrets?)\.(json|ya?ml|toml|ini|env)$", re.IGNORECASE),
    re.compile(r"(^|/)test_[^/]*\.py$"),
    re.compile(r"(^|/)[^/]*_test\.py$"),
    re.compile(r"(^|/)demo\.py$"),
)
DEFAULT_EXCLUDE_DIR_PATTERNS = (
    re.compile(r"(^|/)tests?($|/)"),
    re.compile(r"(^|/)testdata($|/)"),
)


def run_git(args: list[str], cwd: Path, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def git_object_exists(ref: str, cwd: Path) -> bool:
    if not ref or ref == ZERO_SHA:
        return False
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}^{{commit}}"],
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def changed_paths(base: str | None, head: str, cwd: Path) -> list[str]:
    if git_object_exists(base or "", cwd):
        output = run_git(["diff", "--name-only", "--diff-filter=ACMRT", f"{base}..{head}"], cwd)
    else:
        parent = run_git(["rev-parse", f"{head}^"], cwd, check=False)
        if parent and git_object_exists(parent, cwd):
            output = run_git(["diff", "--name-only", "--diff-filter=ACMRT", f"{parent}..{head}"], cwd)
        else:
            output = run_git(["ls-tree", "-r", "--name-only", head], cwd)
    return [line.strip() for line in output.splitlines() if line.strip()]


def is_app_dir(rel_path: Path, cwd: Path) -> bool:
    rel = rel_path.as_posix()
    full = cwd / rel_path
    return bool(APP_DIR_RE.match(rel)) and full.is_dir() and (full / "config.json").is_file()


def discover_apps_from_paths(paths: list[str], cwd: Path) -> list[Path]:
    apps: set[Path] = set()
    for changed in paths:
        parts = Path(changed).parts
        if not parts:
            continue
        candidates = [Path(parts[0])]
        if parts[0] == "Archived" and len(parts) >= 2:
            candidates.insert(0, Path(parts[0]) / parts[1])
        for candidate in candidates:
            if is_app_dir(candidate, cwd):
                apps.add(candidate)
                break
    return sorted(apps, key=lambda item: item.as_posix())


def parse_apps(apps: str | None, cwd: Path) -> list[Path]:
    if not apps:
        return []
    result: list[Path] = []
    for raw in re.split(r"[,\s]+", apps.strip()):
        if not raw:
            continue
        rel = Path(raw.rstrip("/"))
        if not is_app_dir(rel, cwd):
            raise SystemExit(f"not a valid Shakespeare app directory: {rel}")
        result.append(rel)
    return sorted(set(result), key=lambda item: item.as_posix())


def should_exclude(rel_file: Path) -> bool:
    rel = rel_file.as_posix()
    parts = rel_file.parts
    if any(part in DEFAULT_EXCLUDE_NAMES for part in parts):
        return True
    if rel_file.suffix in DEFAULT_EXCLUDE_SUFFIXES:
        return True
    if any(pattern.search(rel) for pattern in DEFAULT_EXCLUDE_FILE_PATTERNS):
        return True
    if any(pattern.search(rel) for pattern in DEFAULT_EXCLUDE_DIR_PATTERNS):
        return True
    return False


def package_app(app_dir: Path, output_dir: Path, cwd: Path) -> dict[str, object]:
    source = cwd / app_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{app_dir.name}.zip"
    files = sorted(path for path in source.rglob("*") if path.is_file())
    included_files = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            rel_inside_app = file_path.relative_to(source)
            if should_exclude(rel_inside_app):
                continue
            archive_name = app_dir / rel_inside_app
            archive.write(file_path, archive_name.as_posix())
            included_files.append(archive_name.as_posix())
    return {
        "app": app_dir.as_posix(),
        "zip": zip_path.relative_to(cwd).as_posix(),
        "files": len(included_files),
    }


def write_manifest(packages: list[dict[str, object]], manifest: Path | None) -> None:
    if not manifest:
        return
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"packages": packages}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Package changed Shakespeare app directories.")
    parser.add_argument("--base", default=os.environ.get("BASE_SHA"), help="base git revision")
    parser.add_argument("--head", default=os.environ.get("GITHUB_SHA", "HEAD"), help="head git revision")
    parser.add_argument("--apps", default=os.environ.get("APP_DIRS"), help="explicit app dirs, comma or whitespace separated")
    parser.add_argument("--output-dir", default="release", help="directory for generated zip files")
    parser.add_argument("--manifest", default="release/packaged-apps.json", help="JSON manifest path; use empty value to skip")
    args = parser.parse_args()

    cwd = Path.cwd()
    explicit_apps = parse_apps(args.apps, cwd)
    apps = explicit_apps or discover_apps_from_paths(changed_paths(args.base, args.head, cwd), cwd)
    if not apps:
        print("No changed Shakespeare app directories found.")
        return 0

    output_dir = cwd / args.output_dir
    packages = [package_app(app_dir, output_dir, cwd) for app_dir in apps]
    write_manifest(packages, cwd / args.manifest if args.manifest else None)

    print("Packaged Shakespeare apps:")
    for package in packages:
        print(f"- {package['app']} -> {package['zip']} ({package['files']} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
