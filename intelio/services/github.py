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
        }
        for commit in commits[:limit]
    ]