from intelio.services.evidence import _tokenize


def resolve_project(user_request, context):
    """
    Attempt to identify which known project a user request belongs to.

    Rules:
    - Explicit project name in the request is the strongest signal.
    - ProjectState records may provide supporting evidence.
    - Recent GitHub Activity may provide supporting evidence.
    - Never force a project assignment when evidence is insufficient.
    - Never map a technical concept to a project without direct evidence.
    - Deterministic. No LLM.
    """

    project_states = context.get("current_projects", [])
    github_activity = context.get("github_activity", [])

    known_projects = {
        state["project"]
        for state in project_states
        if state.get("project")
    }

    # Also collect project names from GitHub activity.
    for activity in github_activity:
        project = activity.get("project")
        if project:
            known_projects.add(project)

    known_projects.discard(None)
    known_projects.discard("")
    known_projects.discard("Unspecified")

    if not known_projects:
        return {
            "project": None,
            "confidence": "low",
            "reason": "No known projects in evidence.",
        }

    # Step 1: Check for an explicit project name mention in the request.
    request_lower = user_request.lower()

    explicitly_named = []

    for project in known_projects:
        if project.lower() in request_lower:
            explicitly_named.append(project)

    if len(explicitly_named) == 1:
        return {
            "project": explicitly_named[0],
            "confidence": "high",
            "reason": (
                f"Project '{explicitly_named[0]}' is explicitly "
                f"named in the user request."
            ),
        }

    if len(explicitly_named) > 1:
        return {
            "project": None,
            "confidence": "low",
            "reason": "Multiple projects explicitly named in request.",
        }

    # Step 2: No explicit mention. Check if GitHub evidence
    # connects the request tokens to a specific project's activity.
    request_tokens = _tokenize(user_request)

    if not request_tokens:
        return {
            "project": None,
            "confidence": "low",
            "reason": "No reliable project evidence.",
        }

    project_scores = {}

    for activity in github_activity:
        project = activity.get("project")

        if not project or project == "Unspecified":
            continue

        activity_text = " ".join([
            activity.get("subject", ""),
            activity.get("summary", ""),
            activity.get("activity", ""),
        ])

        activity_tokens = _tokenize(activity_text)

        overlap = request_tokens.intersection(activity_tokens)

        if overlap:
            project_scores[project] = (
                project_scores.get(project, 0) + len(overlap)
            )

    if not project_scores:
        return {
            "project": None,
            "confidence": "low",
            "reason": "No reliable project evidence.",
        }

    max_score = max(project_scores.values())
    top_projects = [
        p for p, score in project_scores.items()
        if score == max_score
    ]

    if len(top_projects) == 1:
        return {
            "project": top_projects[0],
            "confidence": "medium",
            "reason": (
                f"GitHub evidence for '{top_projects[0]}' "
                f"overlaps with the user request."
            ),
        }

    return {
        "project": None,
        "confidence": "low",
        "reason": "Multiple possible projects.",
    }
