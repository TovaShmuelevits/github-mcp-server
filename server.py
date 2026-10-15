
import os
from typing import Literal

import requests
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("GitHub Assistant")


def github_get(endpoint: Literal["pulls", "issues"]) -> list[dict]:
    """Return open pull requests or issues from the configured repository."""
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")

    missing = [
        name
        for name, value in (
            ("GITHUB_TOKEN", token),
            ("GITHUB_OWNER", owner),
            ("GITHUB_REPO", repo),
        )
        if not value
    ]

    if missing:
        raise ValueError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )

    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/{endpoint}",
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            params={"state": "open", "per_page": 30},
            timeout=20,
        )

        response.raise_for_status()

    except requests.HTTPError as exc:
        raise RuntimeError(
            f"GitHub API error: HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        ) from exc

    except requests.RequestException as exc:
        raise RuntimeError(
            f"GitHub connection error: {exc}"
        ) from exc

    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError(
            "Unexpected response from GitHub API: expected a list."
        )

    return data


@mcp.tool()
def list_pull_requests() -> list[dict]:
    """List open pull requests in the configured GitHub repository."""
    items = github_get("pulls")

    return [
        {
            "number": item["number"],
            "title": item["title"],
            "author": item["user"]["login"],
            "url": item["html_url"],
            "updated_at": item["updated_at"],
        }
        for item in items
    ]


@mcp.tool()
def list_issues() -> list[dict]:
    """List open issues, excluding pull requests."""
    items = github_get("issues")

    return [
        {
            "number": item["number"],
            "title": item["title"],
            "author": item["user"]["login"],
            "url": item["html_url"],
            "updated_at": item["updated_at"],
        }
        for item in items
        if "pull_request" not in item
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")
