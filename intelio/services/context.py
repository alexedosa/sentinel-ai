from intelio.models import Activity, ProjectState, UserSignal


def build_context():
    activities = Activity.objects.order_by("-occurred_at")[:20]
    signals = UserSignal.objects.order_by("-created_at")[:20]
    project_states = ProjectState.objects.all()

    github_activity = []

    for activity in activities:
        github_activity.append({
            "external_id": activity.external_id,
            "repository": activity.repository,
            "project": activity.project,
            "activity": activity.activity_type,
            "subject": activity.subject,
            "summary": activity.summary,
            "occurred_at": activity.occurred_at.isoformat(),
        })

    user_signals = []

    for signal in signals:
        user_signals.append({
            "request": signal.request,
            "created_at": signal.created_at.isoformat(),
        })

    current_projects = []

    for state in project_states:
        current_projects.append({
            "project": state.project,
            "current_focus": state.current_focus,
            "status": state.status,
            "summary": state.summary,
            "updated_at": state.updated_at.isoformat(),
        })

    return {
        "github_activity": github_activity,
        "user_signals": user_signals,
        "current_projects": current_projects,
    }