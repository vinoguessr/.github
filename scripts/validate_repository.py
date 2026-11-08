#!/usr/bin/env python3
"""Validate actual foundation files; intentionally no network or credentials required."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

import yaml


class WorkflowLoader(yaml.SafeLoader):
    """Keep the YAML 1.2 workflow key 'on' as a string with PyYAML's 1.1 loader."""


WorkflowLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in values if tag != "tag:yaml.org,2002:bool"]
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

REVIEW_AGENT_TOOLS = {"Read", "Grep", "Glob", "Bash"}
# CodeQL needs to upload results; no other job may be granted write access.
JOB_WRITE_ALLOWLIST = {"security-events"}


def trigger_events(on: object) -> set[str]:
    """Workflow `on:` may be a string, a list, or a mapping."""
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return {str(event) for event in on}
    if isinstance(on, dict):
        return {str(event) for event in on}
    return set()


def runs_codeql(job: dict) -> bool:
    return any(str(step.get("uses", "")).startswith("github/codeql-action/") for step in job.get("steps") or [])


def job_permissions_are_safe(permissions: object, codeql: bool) -> bool:
    if isinstance(permissions, str):
        return permissions == "read-all"
    if isinstance(permissions, dict):
        return all(value in ("read", "none") or (value == "write" and codeql and scope in JOB_WRITE_ALLOWLIST)
                   for scope, value in permissions.items())
    return False


def agent_tools(value: object) -> set[str]:
    """Claude Code agent `tools:` may be a comma-separated string or a YAML list."""
    if isinstance(value, str):
        return {tool.strip() for tool in value.split(",") if tool.strip()}
    if isinstance(value, list):
        return {str(tool).strip() for tool in value if str(tool).strip()}
    return set()


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    def require(condition: object, message: str) -> None:
        if not condition:
            errors.append(message)

    required = [
        "README.md", "profile/README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md",
        ".github/CODEOWNERS", ".github/pull_request_template.md", ".github/dependabot.yml",
        ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/feature.yml",
        ".github/ISSUE_TEMPLATE/bug.yml", ".codex/config.toml", "CLAUDE.md",
        ".claude/agents/reviewer.md", ".claude/agents/security-reviewer.md",
    ]
    for filename in required:
        p = root / filename
        require(p.is_file() and bool(p.read_text().strip()), f"Missing or empty {filename}")

    claude = root / "CLAUDE.md"
    if claude.is_file():
        # Claude Code reads CLAUDE.md, not AGENTS.md; the import keeps AGENTS.md the single source of rules.
        require(claude.read_text().startswith("@AGENTS.md"), "CLAUDE.md must import AGENTS.md on its first line")

    for p in sorted((root / ".claude/agents").glob("*.md")):
        text = p.read_text()
        match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        require(match is not None, f"Missing agent frontmatter: {p.name}")
        if match is None:
            continue
        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            errors.append(f"Invalid agent frontmatter {p.name}: {exc}")
            continue
        require(isinstance(meta, dict) and meta.get("name") and meta.get("description"), f"Missing agent name/description: {p.name}")
        tools = agent_tools(meta.get("tools") if isinstance(meta, dict) else None)
        # An allowlist, not a denylist: new write-capable or MCP tools must not slip into a reviewer.
        require(bool(tools) and tools <= REVIEW_AGENT_TOOLS, f"Review agent tools must be a subset of {sorted(REVIEW_AGENT_TOOLS)}: {p.name}")

    workflow_files = sorted([*(root / ".github").rglob("*.yml"), *(root / ".github").rglob("*.yaml")])
    for p in workflow_files:
        try:
            data = yaml.load(p.read_text(), Loader=WorkflowLoader)
        except yaml.YAMLError as exc:
            errors.append(f"Invalid YAML {p.relative_to(root)}: {exc}")
            continue
        require(isinstance(data, dict), f"Expected YAML mapping: {p.relative_to(root)}")
        if not isinstance(data, dict):
            continue
        if p.parent.name == "workflows":
            require("on" in data and "jobs" in data, f"Missing workflow trigger/jobs: {p.name}")
            require(data.get("permissions") == {"contents": "read"}, f"Workflow must default to contents:read: {p.name}")
            require("pull_request_target" not in trigger_events(data.get("on")), f"Unsafe trigger: {p.name}")
            for job_id, job in (data.get("jobs") or {}).items():
                if "uses" not in job:
                    require("timeout-minutes" in job, f"Missing job timeout: {p.name}")
                if "permissions" in job:
                    require(job_permissions_are_safe(job["permissions"], runs_codeql(job)), f"Job permissions too broad: {p.name}: {job_id}")
                uses = [job["uses"]] if "uses" in job else []
                for step in job.get("steps", []):
                    if "uses" in step:
                        uses.append(step["uses"])
                    if str(step.get("uses", "")).startswith("actions/checkout@"):
                        require((step.get("with") or {}).get("persist-credentials") == "false", f"Checkout credentials persist: {p.name}")
                for ref in uses:
                    require(ref.startswith("./") or bool(re.search(r"@[0-9a-f]{40}$", ref)), f"Action/workflow is not SHA pinned: {p.name}: {ref}")
        if p.parent.name == "ISSUE_TEMPLATE" and p.name != "config.yml":
            require(bool(data.get("name")) and bool(data.get("description")), f"Missing form metadata: {p.name}")
            fields = data.get("body", [])
            ids = [field.get("id") for field in fields]
            require(all(ids) and len(ids) == len(set(ids)), f"Missing/duplicate form IDs: {p.name}")
            require("acceptance" in ids and "dependencies" in ids, f"Missing acceptance/dependencies: {p.name}")

    for p in sorted((root / ".codex").rglob("*.toml")):
        try:
            data = tomllib.loads(p.read_text())
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"Invalid TOML {p.relative_to(root)}: {exc}")
            continue
        if p.parent.name == "agents":
            require(all(data.get(key) for key in ["name", "description", "developer_instructions"]), f"Missing agent schema keys: {p.name}")
            require(not any(key in data for key in ["sandbox_mode", "approval_policy", "mcp_servers"]), f"Agent cannot override parent permissions: {p.name}")

    # Check local Markdown paths without requiring pending remote repositories or network access.
    for p in root.rglob("*.md"):
        if ".git" in p.parts or ".venv" in p.parts or "node_modules" in p.parts:
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", p.read_text()):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path = target.split("#", 1)[0]
            if path:
                destination = p.parent / path
                wiki_page = "wiki" in p.parts and destination.with_suffix(".md").is_file()
                require(destination.exists() or wiki_page, f"Broken local link in {p.relative_to(root)}: {target}")
    return errors


if __name__ == "__main__":
    failures = validate(Path(__file__).resolve().parents[1])
    if failures:
        print("\n".join(f"ERROR: {failure}" for failure in failures), file=sys.stderr)
        raise SystemExit(1)
    print("Foundation files, YAML, TOML, Claude agents, workflow security policy, Issue Forms, and local links verified.")
