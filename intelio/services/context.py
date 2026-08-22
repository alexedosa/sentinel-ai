from intelio.models import Activity, ProjectState, UserSignal


def build_context(user=None, code_evidence=None):
    """
    Build context for the intelligence and mentor pipelines.

    GitHub activity (Activity) and project state (ProjectState) are global
    infrastructure data — they represent the developer's shared GitHub history
    and are intentionally not user-scoped at this stage of the product.

    UserSignal records ARE user-specific. When a user is provided, only that
    user's signals are included. This prevents one user's stated intentions
    from appearing in another user's Sentinel context.

    The user parameter MUST be passed from the view layer (always request.user)
    so that the filtering happens before any data reaches the LLM.
    """
    activities = Activity.objects.order_by("-occurred_at")[:20]
    project_states = ProjectState.objects.all()

    # Scope signals to the authenticated user when a user is provided.
    if user is not None and user.is_authenticated:
        signals = UserSignal.objects.filter(
            user=user
        ).order_by("-created_at")[:20]
    else:
        # No user provided (e.g. called from a non-user context in tests).
        # Return empty signals rather than leaking all users' signals.
        signals = UserSignal.objects.none()

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
        "code_evidence": code_evidence or [],
    }