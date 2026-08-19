from ..models import Activity, ProjectState


def build_context(project="Sentinel", limit=10):

    recent_activities = (
        Activity.objects
        .order_by("-created_at")[:limit]
    )

    project_state = ProjectState.objects.filter(
        project=project
    ).first()

    return {
        "project_state": (
            {
                "project": project_state.project,
                "current_focus": project_state.current_focus,
                "status": project_state.status,
                "summary": project_state.summary,
                "updated_at": project_state.updated_at.isoformat(),
            }
            if project_state
            else None
        ),
        "recent_activities": [
            {
                "project": activity.project,
                "activity": activity.activity_type,
                "subject": activity.subject,
                "status": activity.status,
                "summary": activity.summary,
                "created_at": activity.created_at.isoformat(),
            }
            for activity in recent_activities
        ],
    }