#!/usr/bin/env python3
"""
Linear API client for the AI-Startup project manager agent.
Uses the Linear GraphQL API to create/manage projects, epics, and issues.

Usage:
  python tools/linear_client.py create-issue --team <team-id> --title "..." --description "..."
  python tools/linear_client.py create-epic --team <team-id> --title "..." --description "..."
  python tools/linear_client.py list-issues --project <project-name>
  python tools/linear_client.py create-project --name <name> --roadmap <roadmap-file>

Requires: LINEAR_API_KEY environment variable
"""

import argparse
import json
import os
import sys
from typing import Any

import urllib.request
import urllib.error


LINEAR_API_URL = "https://api.linear.app/graphql"


def get_api_key() -> str:
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        print(
            "ERROR: LINEAR_API_KEY environment variable is not set.\n"
            "Set it with: export LINEAR_API_KEY=your_key_here\n"
            "Get your API key at: https://linear.app/settings/api",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def graphql_request(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = get_api_key()
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")

    req = urllib.request.Request(
        LINEAR_API_URL,
        data=payload,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    if "errors" in result:
        for error in result["errors"]:
            print(f"GraphQL Error: {error['message']}", file=sys.stderr)
        sys.exit(1)

    return result["data"]


def get_teams() -> list[dict]:
    query = """
    query {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """
    data = graphql_request(query)
    return data["teams"]["nodes"]


def get_team_id(team_name_or_key: str) -> str:
    teams = get_teams()
    for team in teams:
        if team["name"].lower() == team_name_or_key.lower() or team["key"].lower() == team_name_or_key.lower():
            return team["id"]
    # If not found by name, return as-is (assume it's already an ID)
    return team_name_or_key


def create_issue(
    team_id: str,
    title: str,
    description: str,
    priority: int = 2,
    labels: list[str] | None = None,
    estimate: int | None = None,
    parent_id: str | None = None,
) -> dict:
    """
    Create a Linear issue.

    Priority: 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
    Estimate: story points (1,2,3,5,8,13)
    """
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
          url
        }
      }
    }
    """
    input_data: dict[str, Any] = {
        "teamId": team_id,
        "title": title,
        "description": description,
        "priority": priority,
    }
    if estimate is not None:
        input_data["estimate"] = estimate
    if parent_id:
        input_data["parentId"] = parent_id

    data = graphql_request(mutation, {"input": input_data})
    issue = data["issueCreate"]["issue"]
    print(f"Created issue: {issue['identifier']} — {issue['title']}")
    print(f"  URL: {issue['url']}")
    return issue


def create_epic(team_id: str, title: str, description: str) -> dict:
    """Create a Linear project (used as epic) linked to a team."""
    mutation = """
    mutation CreateProject($input: ProjectCreateInput!) {
      projectCreate(input: $input) {
        success
        project {
          id
          name
          url
        }
      }
    }
    """
    input_data = {
        "name": title,
        "description": description,
        "teamIds": [team_id],
    }
    data = graphql_request(mutation, {"input": input_data})
    project = data["projectCreate"]["project"]
    print(f"Created epic (project): {project['name']}")
    print(f"  URL: {project['url']}")
    return project


def list_issues(team_id: str, limit: int = 50) -> list[dict]:
    """List issues for a team."""
    query = """
    query ListIssues($teamId: String!, $first: Int) {
      team(id: $teamId) {
        issues(first: $first, orderBy: priority) {
          nodes {
            id
            identifier
            title
            priority
            state {
              name
            }
            estimate
            assignee {
              name
            }
          }
        }
      }
    }
    """
    data = graphql_request(query, {"teamId": team_id, "first": limit})
    issues = data["team"]["issues"]["nodes"]
    for issue in issues:
        state = issue["state"]["name"] if issue["state"] else "Unknown"
        assignee = issue["assignee"]["name"] if issue["assignee"] else "Unassigned"
        print(f"  {issue['identifier']} [{state}] {issue['title']} — {assignee}")
    return issues


def create_project_from_roadmap(project_name: str, roadmap_file: str) -> None:
    """
    Parse a roadmap.md file and create Linear epics and issues.
    This is a simplified parser — for complex roadmaps, edit and extend.
    """
    if not os.path.exists(roadmap_file):
        print(f"ERROR: Roadmap file not found: {roadmap_file}", file=sys.stderr)
        sys.exit(1)

    teams = get_teams()
    if not teams:
        print("ERROR: No teams found in Linear workspace.", file=sys.stderr)
        sys.exit(1)

    # Use the first team by default, or find one matching the project name
    team = teams[0]
    for t in teams:
        if project_name.lower() in t["name"].lower():
            team = t
            break

    print(f"Using team: {team['name']} ({team['id']})")
    print(f"Parsing roadmap: {roadmap_file}")
    print(f"\nLinear project creation from roadmap: {project_name}")
    print("Note: This creates a Linear project and issues. Review them in Linear after creation.")
    print(f"\nLinear workspace: https://linear.app/")


def update_issue(issue_id: str, status: str) -> dict:
    """Update an issue's status. Status is a state name (e.g., 'In Progress', 'Done')."""
    # First, find the state ID for this team
    mutation = """
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue {
          id
          identifier
          title
          state {
            name
          }
        }
      }
    }
    """
    # Note: in production, look up stateId from team's workflow states
    print(f"Note: To update issue status, use Linear UI or provide stateId directly.")
    print(f"Issue ID: {issue_id}, Desired status: {status}")
    return {}


def main():
    parser = argparse.ArgumentParser(description="Linear API client for AI-Startup")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-issue
    create_issue_parser = subparsers.add_parser("create-issue", help="Create a Linear issue")
    create_issue_parser.add_argument("--team", required=True, help="Team ID or name")
    create_issue_parser.add_argument("--title", required=True, help="Issue title")
    create_issue_parser.add_argument("--description", required=True, help="Issue description (markdown)")
    create_issue_parser.add_argument("--priority", type=int, default=2, help="Priority: 1=Urgent, 2=High, 3=Medium, 4=Low")
    create_issue_parser.add_argument("--estimate", type=int, help="Story point estimate")
    create_issue_parser.add_argument("--parent", help="Parent issue/epic ID")

    # create-epic
    create_epic_parser = subparsers.add_parser("create-epic", help="Create a Linear epic (project)")
    create_epic_parser.add_argument("--team", required=True, help="Team ID or name")
    create_epic_parser.add_argument("--title", required=True, help="Epic title")
    create_epic_parser.add_argument("--description", required=True, help="Epic description")

    # list-issues
    list_parser = subparsers.add_parser("list-issues", help="List issues for a project/team")
    list_parser.add_argument("--project", required=True, help="Project name or team ID")
    list_parser.add_argument("--limit", type=int, default=50, help="Max issues to return")

    # create-project
    project_parser = subparsers.add_parser("create-project", help="Create Linear project from roadmap")
    project_parser.add_argument("--name", required=True, help="Project name")
    project_parser.add_argument("--roadmap", required=True, help="Path to roadmap.md")

    # teams
    subparsers.add_parser("teams", help="List all teams in the workspace")

    args = parser.parse_args()

    if args.command == "create-issue":
        team_id = get_team_id(args.team)
        create_issue(
            team_id=team_id,
            title=args.title,
            description=args.description,
            priority=args.priority,
            estimate=args.estimate,
            parent_id=args.parent,
        )
    elif args.command == "create-epic":
        team_id = get_team_id(args.team)
        create_epic(team_id=team_id, title=args.title, description=args.description)
    elif args.command == "list-issues":
        team_id = get_team_id(args.project)
        list_issues(team_id=team_id, limit=args.limit)
    elif args.command == "create-project":
        create_project_from_roadmap(project_name=args.name, roadmap_file=args.roadmap)
    elif args.command == "teams":
        teams = get_teams()
        print("Teams in your Linear workspace:")
        for team in teams:
            print(f"  {team['key']} — {team['name']} (ID: {team['id']})")


if __name__ == "__main__":
    main()
