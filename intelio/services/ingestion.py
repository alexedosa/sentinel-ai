from intelio.models import Activity


def ingest_github_commits(commits):
    created = []
    skipped = []

    for commit in commits:
        external_id = commit["sha"]

        if Activity.objects.filter(
            external_id=external_id
        ).exists():
            skipped.append(external_id)
            continue

        activity = Activity.objects.create(
            external_id=external_id,
            source=Activity.SOURCE_GITHUB,
            repository=commit["repository"],
            project="Sentinel",
            activity_type="commit",
            subject=commit["message"],
            summary=commit["message"],
            occurred_at=commit["date"],
        )

        created.append(activity)

    return {
        "created": created,
        "skipped": skipped,
    }