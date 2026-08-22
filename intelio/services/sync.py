from intelio.services.github import get_recent_commits
from intelio.services.ingestion import ingest_github_commits


DEFAULT_GITHUB_USERNAME = "alexedosa"
DEFAULT_GITHUB_REPOSITORY = "sentinel-ai"


def sync_github(
    username=DEFAULT_GITHUB_USERNAME,
    repository_name=DEFAULT_GITHUB_REPOSITORY,
):
    """
    Synchronize recent GitHub commits into Sentinel's activity store.

    GitHub retrieval and database ingestion remain delegated to their
    respective services. This function only coordinates the sync operation.
    """

    commits = get_recent_commits(
        username,
        repository_name,
    )

    return ingest_github_commits(commits)
