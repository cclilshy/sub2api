#!/usr/bin/env python3
"""Generate override deployment files for cclilshy/sub2api.

The generated files live under override/deploy. They are copied from the
repository's deploy/ directory and rewritten for the override/main branch and the
cclilshy/sub2api:latest Docker image.

Runtime/sensitive files such as deploy/.env and deploy/data are intentionally not
copied: only files tracked by git under deploy/ are used as the source set.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "deploy"
DEST_DIR = ROOT / "override" / "deploy"

OWNER = "cclilshy"
REPO = "sub2api"
PROJECT = f"{OWNER}/{REPO}"
BRANCH = "override/main"
RAW_REF = f"refs/heads/{BRANCH}"
IMAGE = f"{PROJECT}:latest"
REPO_URL = f"https://github.com/{PROJECT}"
RAW_REPO_URL = f"https://raw.githubusercontent.com/{PROJECT}/{RAW_REF}"
RAW_DEPLOY_URL = f"{RAW_REPO_URL}/override/deploy"

# Keep replacements specific to this project. Do not rewrite unrelated upstreams
# such as Wei-Shaw/model-price-repo.
REPLACEMENTS: tuple[tuple[str, str], ...] = (
    # Raw deployment links must point at this branch's generated override/deploy.
    (
        "https://raw.githubusercontent.com/Wei-Shaw/sub2api/main/deploy",
        RAW_DEPLOY_URL,
    ),
    (
        "https://raw.githubusercontent.com/weishaw/sub2api/main/deploy",
        RAW_DEPLOY_URL,
    ),
    # Other raw links in this repository should point at override/main.
    (
        "https://raw.githubusercontent.com/Wei-Shaw/sub2api/main",
        RAW_REPO_URL,
    ),
    (
        "https://raw.githubusercontent.com/weishaw/sub2api/main",
        RAW_REPO_URL,
    ),
    # Repository and documentation links.
    ("https://github.com/Wei-Shaw/sub2api", REPO_URL),
    ("https://github.com/weishaw/sub2api", REPO_URL),
    ("github.com/Wei-Shaw/sub2api", f"github.com/{PROJECT}"),
    ("github.com/weishaw/sub2api", f"github.com/{PROJECT}"),
    ("Wei-Shaw/sub2api", PROJECT),
    ("weishaw/sub2api", PROJECT),
    # Maintainer label in deployment Dockerfile.
    ('LABEL maintainer="Wei-Shaw <github.com/Wei-Shaw>"', f'LABEL maintainer="{OWNER} <github.com/{OWNER}>"'),
    # Manual clone instructions should enter the generated deployment directory.
    ("cd sub2api/deploy", "cd sub2api/override/deploy"),
)


def git_tracked_deploy_files() -> list[Path]:
    """Return tracked files under deploy/ as paths relative to ROOT."""
    output = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "deploy"],
        text=True,
    )
    return [Path(line) for line in output.splitlines() if line.strip()]


def copy_deploy() -> int:
    """Copy tracked deploy files into override/deploy."""
    if not SOURCE_DIR.is_dir():
        raise SystemExit(f"source directory not found: {SOURCE_DIR}")

    if DEST_DIR.exists():
        shutil.rmtree(DEST_DIR)
    DEST_DIR.mkdir(parents=True)

    files = git_tracked_deploy_files()
    if not files:
        raise SystemExit("no tracked deploy files found")

    for rel_path in files:
        src = ROOT / rel_path
        dst = DEST_DIR / rel_path.relative_to("deploy")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    return len(files)


def rewrite_file(path: Path) -> bool:
    """Apply text replacements to one file. Return True if it changed."""
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    updated = original
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)

    if updated == original:
        return False

    path.write_text(updated, encoding="utf-8")
    return True


def rewrite_generated_files() -> int:
    changed = 0
    for path in DEST_DIR.rglob("*"):
        if path.is_file() and rewrite_file(path):
            changed += 1
    return changed


def main() -> None:
    copied = copy_deploy()
    changed = rewrite_generated_files()

    print(f"Generated: {DEST_DIR.relative_to(ROOT)}")
    print(f"Copied tracked deploy files: {copied}")
    print(f"Rewritten text files: {changed}")
    print(f"Project: {PROJECT}")
    print(f"Branch: {BRANCH}")
    print(f"Image: {IMAGE}")
    print(f"Raw deploy URL: {RAW_DEPLOY_URL}")


if __name__ == "__main__":
    main()
