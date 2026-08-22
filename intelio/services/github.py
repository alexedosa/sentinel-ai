import os

from dotenv import load_dotenv
from github import Github


load_dotenv()


github = Github(
    os.getenv("GITHUB_TOKEN")
)


def get_recent_commits(username, repository_name, limit=10):

    user = github.get_user(username)

    repository = user.get_repo(repository_name)

    commits = repository.get_commits()

    return [
        {
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": commit.author.login if commit.author else None,
            "date": commit.commit.author.date.isoformat()
            if commit.commit.author
            else None,
            "repository": repository.full_name,
        }
        for commit in commits[:limit]
    ]


def get_commit_details(username, repository_name, sha):

    user = github.get_user(username)

    repository = user.get_repo(repository_name)

    commit = repository.get_commit(sha)

    files = []

    for file in commit.files:
        files.append({
            "filename": file.filename,
            "status": file.status,
            "additions": file.additions,
            "deletions": file.deletions,
            "patch": file.patch,
        })

    return {
        "sha": commit.sha,
        "message": commit.commit.message,
        "repository": repository.full_name,
        "files": files,
    }