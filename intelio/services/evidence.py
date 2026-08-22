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
    "want",
    "need",
    "trying",
    "going",
}


MAX_EVIDENCE_PER_SOURCE = 5

RELEVANCE_THRESHOLD = 0.20


def tokenize(text):
    """
    Normalize text into meaningful lowercase tokens.

    This is intentionally deterministic. A more advanced semantic
    retrieval implementation can replace this later without changing
    the evidence contract.
    """

    if not text:
        return set()

    words = re.findall(
        r"[a-zA-Z0-9]+",
        str(text).lower(),
    )

    return {
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 2
    }


def _similarity(left, right):
    if not left or not right:
        return 0.0

    return SequenceMatcher(
        None,
        str(left).lower(),
        str(right).lower(),
    ).ratio()


def _token_overlap(request_tokens, evidence_tokens):
    if not request_tokens or not evidence_tokens:
        return 0.0

    overlap = request_tokens.intersection(
        evidence_tokens
    )

    if not overlap:
        return 0.0

    return len(overlap) / len(request_tokens)


def _relevance_score(user_request, searchable_text):
    """
    Produce a deterministic relevance score between 0 and 1.

    Token overlap is the primary signal. Text similarity provides
    supporting evidence when wording differs slightly.
    """

    if not user_request or not searchable_text:
        return 0.0

    request_tokens = tokenize(user_request)
    evidence_tokens = tokenize(searchable_text)

    if not request_tokens or not evidence_tokens:
        return 0.0

    overlap_score = _token_overlap(
        request_tokens,
        evidence_tokens,
    )

    similarity_score = _similarity(
        user_request,
        searchable_text,
    )

    return min(
        1.0,
        (overlap_score * 0.75)
        + (similarity_score * 0.25),
    )


def _rank_candidates(
    user_request,
    candidates,
    text_builder,
    source,
):
    """
    Score and rank candidate evidence records.

    Records below the relevance threshold are discarded.
    """

    ranked = []

    for candidate in candidates:
        searchable_text = text_builder(candidate)

        relevance = _relevance_score(
            user_request,
            searchable_text,
        )

        if relevance < RELEVANCE_THRESHOLD:
            continue

        ranked.append({
            "source": source,
            "relevance": round(
                relevance,
                3,
            ),
            "data": candidate,
        })

    ranked.sort(
        key=lambda item: item["relevance"],
        reverse=True,
    )

    return ranked[:MAX_EVIDENCE_PER_SOURCE]


def _github_text(activity):
    return " ".join(
        [
            activity.get("project", ""),
            activity.get("repository", ""),
            activity.get("activity", ""),
            activity.get("subject", ""),
            activity.get("summary", ""),
        ]
    )


def _signal_text(signal):
    return signal.get(
        "request",
        "",
    )


def _project_text(project):
    return " ".join(
        [
            project.get("project", ""),
            project.get("current_focus", ""),
            project.get("status", ""),
            project.get("summary", ""),
        ]
    )


def _derive_evidence_level(evidence):
    """
    Derive an overall evidence level from the strongest available
    relevance score rather than simply counting records.
    """

    if not evidence:
        return "none"

    strongest = max(
        item["relevance"]
        for item in evidence
    )

    if strongest >= 0.70:
        return "strong"

    if strongest >= 0.40:
        return "moderate"

    return "weak"


def build_evidence(
    user_request,
    context,
):
    """
    Retrieve and rank evidence relevant to the user's request.

    This service is responsible for retrieval and evidence packaging.
    It does not decide intent, alignment, project direction, or
    recommendations.
    """

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

    github_evidence = _rank_candidates(
        user_request,
        github_activity,
        _github_text,
        "github",
    )

    user_history = _rank_candidates(
        user_request,
        user_signals,
        _signal_text,
        "user_history",
    )

    project_state = _rank_candidates(
        user_request,
        current_projects,
        _project_text,
        "project_state",
    )

    all_evidence = (
        github_evidence
        + user_history
        + project_state
    )

    all_evidence.sort(
        key=lambda item: item["relevance"],
        reverse=True,
    )

    return {
        "user_request": user_request,
        "github_evidence": github_evidence,
        "user_history": user_history,
        "project_state": project_state,
        "evidence_level": _derive_evidence_level(
            all_evidence
        ),
    }