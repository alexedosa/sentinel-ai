from intelio.services.github import get_recent_commits
from intelio.services.ingestion import ingest_github_commits


def sync_github():
    commits = get_recent_commits(
        "alexedosa",
        "sentinel-ai"
    )

    return ingest_github_commits(commits)