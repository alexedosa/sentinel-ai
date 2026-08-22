import os

from dotenv import load_dotenv
from github import Github


load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_github_client():
    """
    Create a GitHub API client using the configured token.

    Keeping client creation behind a function prevents external-service
    initialization from happening when this module is merely imported.
    """

    return Github(GITHUB_TOKEN)


def get_repository(username, repository_name):
    """
    Resolve a GitHub repository for the requested user.
    """

    client = get_github_client()
    user = client.get_user(username)

    return user.get_repo(repository_name)


def get_recent_commits(
    username,
    repository_name,
    limit=10,
):
    """
    Retrieve and normalize recent commits from a GitHub repository.
    """

    repository = get_repository(
        username,
        repository_name,
    )

    commits = repository.get_commits()

    return [
        {
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": (
                commit.author.login
                if commit.author
                else None
            ),
            "date": (
                commit.commit.author.date.isoformat()
                if commit.commit.author
                else None
            ),
            "repository": repository.full_name,
        }
        for commit in commits[:limit]
    ]


def get_commit_details(
    username,
    repository_name,
    sha,
):
    """
    Retrieve and normalize detailed information about a GitHub commit,
    including changed files.
    """

    repository = get_repository(
        username,
        repository_name,
    )

    commit = repository.get_commit(sha)

    files = [
        {
            "filename": file.filename,
            "status": file.status,
            "additions": file.additions,
            "deletions": file.deletions,
            "patch": file.patch,
        }
        for file in commit.files
    ]

    return {
        "sha": commit.sha,
        "message": commit.commit.message,
        "repository": repository.full_name,
        "files": files,
    }
