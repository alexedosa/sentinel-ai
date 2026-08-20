from intelio.models import Activity, ProjectState


def sync_project_state():
    """
    Derive and persist a ProjectState snapshot for each project
    based on confirmed Activity records.

    Rules:
    - Activity is the source of truth.
    - ProjectState is derived state only.
    - The latest Activity (by occurred_at) wins for each project.
    - No LLM involvement.
    - No Activity records are modified.
    """

    activities = (
        Activity.objects
        .order_by("project", "-occurred_at")
    )

    # Collect the latest activity per project.
    latest_per_project = {}

    for activity in activities:
        if activity.project not in latest_per_project:
            latest_per_project[activity.project] = activity

    if not latest_per_project:
        return {
            "created": [],
            "updated": [],
        }

    created = []
    updated = []

    for project_name, activity in latest_per_project.items():
        state, was_created = ProjectState.objects.update_or_create(
            project=project_name,
            defaults={
                "current_focus": activity.subject,
                "status": "active",
                "summary": activity.summary,
            },
        )

        if was_created:
            created.append(project_name)
        else:
            updated.append(project_name)

    return {
        "created": created,
        "updated": updated,
    }
