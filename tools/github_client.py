#!/usr/bin/env python3
"""
GitHub REST API client for the AI-Startup PR review workflow.

Usage:
  python tools/github_client.py get-pr --url https://github.com/owner/repo/pull/123
  python tools/github_client.py post-review --url https://github.com/owner/repo/pull/123 --body "review text"
  python tools/github_client.py get-diff --url https://github.com/owner/repo/pull/123

Requires: GITHUB_TOKEN environment variable
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import Any


GITHUB_API_URL = "https://api.github.com"


def get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "ERROR: GITHUB_TOKEN environment variable is not set.\n"
            "Set it with: export GITHUB_TOKEN=your_token_here\n"
            "Create a token at: https://github.com/settings/tokens",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        print(f"ERROR: Cannot parse GitHub PR URL: {url}", file=sys.stderr)
        print("Expected format: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    owner, repo, pr_number = match.groups()
    return owner, repo, int(pr_number)


def github_request(
    path: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    accept: str = "application/vnd.github+json",
) -> Any:
    token = get_token()
    url = f"{GITHUB_API_URL}{path}"
    payload = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ai-startup-agent/1.0",
        },
        method=method,
    )

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"GitHub API Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def get_pr(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata."""
    pr = github_request(f"/repos/{owner}/{repo}/pulls/{pr_number}")
    print(f"PR #{pr_number}: {pr['title']}")
    print(f"  Author: {pr['user']['login']}")
    print(f"  Branch: {pr['head']['ref']} → {pr['base']['ref']}")
    print(f"  Status: {pr['state']}")
    print(f"  Changed files: {pr['changed_files']}")
    print(f"  +{pr['additions']} -{pr['deletions']}")
    return pr


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the raw unified diff for a PR."""
    token = get_token()
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.diff",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-startup-agent/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"GitHub API Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def get_pr_files(owner: str, repo: str, pr_number: int) -> list[dict]:
    """Fetch list of files changed in a PR."""
    files = github_request(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
    print(f"\nChanged files ({len(files)}):")
    for f in files:
        status_symbol = {"added": "+", "modified": "~", "removed": "-", "renamed": "→"}.get(f["status"], "?")
        print(f"  {status_symbol} {f['filename']} (+{f['additions']} -{f['deletions']})")
    return files


def post_review_comment(
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
    event: str = "COMMENT",
) -> dict:
    """
    Post a review to a PR.

    event: APPROVE | REQUEST_CHANGES | COMMENT
    """
    data = {"body": body, "event": event}
    result = github_request(
        f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        method="POST",
        data=data,
    )
    print(f"Posted review to PR #{pr_number}")
    print(f"  Review ID: {result['id']}")
    print(f"  State: {result['state']}")
    return result


def post_pr_comment(owner: str, repo: str, pr_number: int, body: str) -> dict:
    """Post a general comment (not a review) on a PR."""
    # PR comments go to the issues endpoint in GitHub's API
    data = {"body": body}
    result = github_request(
        f"/repos/{owner}/{repo}/issues/{pr_number}/comments",
        method="POST",
        data=data,
    )
    print(f"Posted comment to PR #{pr_number}")
    print(f"  Comment ID: {result['id']}")
    return result


def main():
    parser = argparse.ArgumentParser(description="GitHub API client for AI-Startup PR review")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get-pr
    get_pr_parser = subparsers.add_parser("get-pr", help="Fetch PR metadata and file list")
    get_pr_parser.add_argument("--url", required=True, help="GitHub PR URL")

    # get-diff
    get_diff_parser = subparsers.add_parser("get-diff", help="Fetch raw PR diff")
    get_diff_parser.add_argument("--url", required=True, help="GitHub PR URL")
    get_diff_parser.add_argument("--output", help="Save diff to this file path")

    # post-review
    post_review_parser = subparsers.add_parser("post-review", help="Post a review to a PR")
    post_review_parser.add_argument("--url", required=True, help="GitHub PR URL")
    post_review_parser.add_argument("--body", help="Review body text (or use --body-file)")
    post_review_parser.add_argument("--body-file", help="Path to file containing review body")
    post_review_parser.add_argument(
        "--event",
        choices=["APPROVE", "REQUEST_CHANGES", "COMMENT"],
        default="COMMENT",
        help="Review event type",
    )

    # post-comment
    post_comment_parser = subparsers.add_parser("post-comment", help="Post a general comment on a PR")
    post_comment_parser.add_argument("--url", required=True, help="GitHub PR URL")
    post_comment_parser.add_argument("--body", help="Comment body")
    post_comment_parser.add_argument("--body-file", help="Path to file containing comment body")

    args = parser.parse_args()

    if args.command == "get-pr":
        owner, repo, pr_number = parse_pr_url(args.url)
        get_pr(owner, repo, pr_number)
        get_pr_files(owner, repo, pr_number)

    elif args.command == "get-diff":
        owner, repo, pr_number = parse_pr_url(args.url)
        diff = get_pr_diff(owner, repo, pr_number)
        if args.output:
            with open(args.output, "w") as f:
                f.write(diff)
            print(f"Diff saved to: {args.output}")
        else:
            print(diff)

    elif args.command == "post-review":
        owner, repo, pr_number = parse_pr_url(args.url)
        body = args.body
        if args.body_file:
            with open(args.body_file) as f:
                body = f.read()
        if not body:
            print("ERROR: Provide --body or --body-file", file=sys.stderr)
            sys.exit(1)
        post_review_comment(owner, repo, pr_number, body, args.event)

    elif args.command == "post-comment":
        owner, repo, pr_number = parse_pr_url(args.url)
        body = args.body
        if args.body_file:
            with open(args.body_file) as f:
                body = f.read()
        if not body:
            print("ERROR: Provide --body or --body-file", file=sys.stderr)
            sys.exit(1)
        post_pr_comment(owner, repo, pr_number, body)


if __name__ == "__main__":
    main()
