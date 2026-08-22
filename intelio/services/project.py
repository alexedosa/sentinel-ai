from intelio.services.evidence import tokenize


UNKNOWN_PROJECT = None

LOW_CONFIDENCE = "low"
MEDIUM_CONFIDENCE = "medium"
HIGH_CONFIDENCE = "high"

IGNORED_PROJECT_NAMES = {
    "",
    "unspecified",
}


def _clean_project_name(project):
    if project is None:
        return None

    project = str(project).strip()

    if project.lower() in IGNORED_PROJECT_NAMES:
        return None

    return project


def _collect_known_projects(context):
    projects = set()

    for state in context.get("current_projects", []):
        project = _clean_project_name(
            state.get("project")
        )

        if project:
            projects.add(project)

    for activity in context.get("github_activity", []):
        project = _clean_project_name(
            activity.get("project")
        )

        if project:
            projects.add(project)

    return projects


def _project_is_explicitly_named(
    user_request,
    project,
):
    request_tokens = tokenize(user_request)
    project_tokens = tokenize(project)

    if not request_tokens or not project_tokens:
        return False

    return project_tokens.issubset(
        request_tokens
    )


def _find_explicit_project(
    user_request,
    projects,
):
    matches = [
        project
        for project in projects
        if _project_is_explicitly_named(
            user_request,
            project,
        )
    ]

    if len(matches) == 1:
        project = matches[0]

        return {
            "project": project,
            "confidence": HIGH_CONFIDENCE,
            "reason": (
                f"Project '{project}' was explicitly named "
                "in the user request."
            ),
        }

    if len(matches) > 1:
        return {
            "project": UNKNOWN_PROJECT,
            "confidence": LOW_CONFIDENCE,
            "reason": (
                "Multiple known projects were explicitly named "
                "in the user request."
            ),
        }

    return None


def _score_github_projects(
    user_request,
    github_activity,
):
    request_tokens = tokenize(user_request)

    if not request_tokens:
        return {}

    scores = {}

    for activity in github_activity:
        project = _clean_project_name(
            activity.get("project")
        )

        if not project:
            continue

        activity_text = " ".join(
            [
                activity.get("repository", ""),
                activity.get("subject", ""),
                activity.get("summary", ""),
                activity.get("activity", ""),
            ]
        )

        activity_tokens = tokenize(
            activity_text
        )

        overlap = request_tokens.intersection(
            activity_tokens
        )

        if not overlap:
            continue

        score = len(overlap) / len(
            request_tokens
        )

        scores[project] = (
            scores.get(project, 0.0) + score
        )

    return scores


def _resolve_from_scores(scores):
    if not scores:
        return {
            "project": UNKNOWN_PROJECT,
            "confidence": LOW_CONFIDENCE,
            "reason": (
                "No GitHub activity provides reliable evidence "
                "for a specific project."
            ),
        }

    highest_score = max(
        scores.values()
    )

    top_projects = [
        project
        for project, score in scores.items()
        if score == highest_score
    ]

    if len(top_projects) != 1:
        return {
            "project": UNKNOWN_PROJECT,
            "confidence": LOW_CONFIDENCE,
            "reason": (
                "Multiple projects have equally strong supporting "
                "evidence."
            ),
        }

    project = top_projects[0]

    return {
        "project": project,
        "confidence": MEDIUM_CONFIDENCE,
        "reason": (
            f"GitHub activity for '{project}' overlaps with "
            "the user request."
        ),
    }


def resolve_project(
    user_request,
    context,
):
    """
    Resolve the project most strongly supported by available context.

    Resolution order:

    1. Explicit project mention.
    2. Deterministic GitHub activity overlap.

    Ambiguous or unsupported matches are never forced.

    This service contains no LLM logic.
    """

    if not user_request:
        return {
            "project": UNKNOWN_PROJECT,
            "confidence": LOW_CONFIDENCE,
            "reason": "No user request was provided.",
        }

    projects = _collect_known_projects(
        context
    )

    if not projects:
        return {
            "project": UNKNOWN_PROJECT,
            "confidence": LOW_CONFIDENCE,
            "reason": (
                "No known projects exist in the available context."
            ),
        }

    explicit_match = _find_explicit_project(
        user_request,
        projects,
    )

    if explicit_match:
        return explicit_match

    scores = _score_github_projects(
        user_request,
        context.get(
            "github_activity",
            [],
        ),
    )

    return _resolve_from_scores(scores)
