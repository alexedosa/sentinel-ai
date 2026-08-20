from difflib import SequenceMatcher
import re


STOP_WORDS = {
    "i",
    "im",
    "i'm",
    "the",
    "a",
    "an",
    "am",
    "is",
    "are",
    "was",
    "were",
    "to",
    "on",
    "in",
    "for",
    "and",
    "or",
    "of",
    "my",
    "work",
    "working",
    "continue",
    "continuing",
}


def _tokenize(text):
    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.lower()
    )


    return {
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 2
    }


def _similarity(a, b):
    return SequenceMatcher(
        None,
        a.lower(),
        b.lower(),
    ).ratio()


def _is_relevant(user_request, text):
    if not user_request or not text:
        return False

    request_tokens = _tokenize(user_request)
    text_tokens = _tokenize(text)

    if not request_tokens or not text_tokens:
        return False

    overlap = request_tokens.intersection(
        text_tokens
    )

    if overlap:
        return True

    similarity = _similarity(
        user_request,
        text,
    )

    return similarity >= 0.70


def _derive_evidence_level(
    github_evidence,
    project_state,
):
    total = (
        len(github_evidence)
        + len(project_state)
    )

    if total == 0:
        return "none"

    if total >= 3:
        return "strong"

    return "some"


def build_evidence(
    user_request,
    context,
):
    github_activity = context.get(
        "github_activity",
        [],
    )

    user_signals = context.get(
        "user_signals",
        [],
    )

    current_projects = context.get(
        "current_projects",
        [],
    )

    relevant_github = []

    for activity in github_activity:
        searchable_text = " ".join([
            activity.get("project", ""),
            activity.get("activity", ""),
            activity.get("subject", ""),
            activity.get("summary", ""),
        ])

        if _is_relevant(
            user_request,
            searchable_text,
        ):
            relevant_github.append(activity)

    relevant_signals = []

    for signal in user_signals:
        if _is_relevant(
            user_request,
            signal.get("request", ""),
        ):
            relevant_signals.append(signal)

    relevant_projects = []

    for project in current_projects:
        searchable_text = " ".join([
            project.get("project", ""),
            project.get("current_focus", ""),
            project.get("status", ""),
            project.get("summary", ""),
        ])

        if _is_relevant(
            user_request,
            searchable_text,
        ):
            relevant_projects.append(project)

    return {
        "user_request": user_request,
        "github_evidence": relevant_github,
        "user_history": relevant_signals,
        "project_state": relevant_projects,
        "evidence_level": _derive_evidence_level(
            relevant_github,
            relevant_projects,
        ),
    }