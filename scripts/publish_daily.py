"""Run the full Horizon daily publish workflow.

This script is the local/manual equivalent of the GitHub Actions workflow:
collect news, build static HTML, commit public artifacts, and optionally push to
the GitHub repository that Cloudflare Pages watches.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ARTIFACTS = [
    "docs/index.html",
    "docs/firsthand.html",
    "docs/insights.html",
    "docs/daily",
    "docs/read",
    "docs/data",
    "docs/_posts",
]


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(command)}")
    return subprocess.run(
        command,
        cwd=ROOT,
        check=check,
        text=True,
        stdout=None,
        stderr=None,
    )


def has_staged_changes() -> bool:
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 1


def require_clean_index() -> None:
    if has_staged_changes():
        raise SystemExit(
            "Git index already has staged changes. Commit, unstage, or review them before publishing."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Horizon daily publish workflow.")
    parser.add_argument("--hours", type=int, default=24, help="Collection window in hours.")
    parser.add_argument("--remote", default=os.getenv("HORIZON_PUBLISH_REMOTE", "pages"))
    parser.add_argument("--branch", default=os.getenv("HORIZON_PUBLISH_BRANCH", "main"))
    parser.add_argument("--no-push", action="store_true", help="Commit locally but do not push.")
    parser.add_argument("--skip-collect", action="store_true", help="Skip uv run horizon.")
    parser.add_argument("--skip-build", action="store_true", help="Skip static HTML build.")
    args = parser.parse_args()

    require_clean_index()

    if not args.skip_collect:
        run([sys.executable, "-m", "src.main", "--hours", str(args.hours)])

    if not args.skip_build:
        run([sys.executable, "scripts/build_static_pages.py"])

    run(["git", "add", *PUBLIC_ARTIFACTS])

    if not has_staged_changes():
        print("No public artifact changes to commit.")
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    run(["git", "commit", "-m", f"Daily HTML summary: {today}"])

    if args.no_push:
        print("--no-push set; commit created locally only.")
        return 0

    run(["git", "push", args.remote, f"HEAD:{args.branch}"])
    print("Publish workflow complete. Cloudflare Pages will deploy from the pushed docs/ update.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
