VALID_ALIGNMENTS = {
    "aligned",
    "changed_direction",
    "potential_conflict",
    "insufficient_evidence",
}


def derive_evidence_confidence(evidence):
    github = evidence.get(
        "github_evidence",
        []
    )

    project_state = evidence.get(
        "project_state",
        []
    )

    if not github and not project_state:
        return "low"

    if len(github) >= 3:
        return "high"

    if github and project_state:
        return "high"

    return "medium"


def derive_project_confidence(evidence):
    project_state = evidence.get(
        "project_state",
        []
    )

    github = evidence.get(
        "github_evidence",
        []
    )

    if project_state:
        return "high"

    projects = {
        item.get("project")
        for item in github
        if item.get("project")
    }

    projects.discard(None)
    projects.discard("")
    projects.discard("Unspecified")

    if len(projects) == 1:
        return "medium"

    return "low"


def finalize_decision(
    decision,
    evidence
):
    alignment = decision.get(
        "alignment",
        "insufficient_evidence"
    )

    if alignment not in VALID_ALIGNMENTS:
        alignment = "insufficient_evidence"

    evidence_confidence = (
        derive_evidence_confidence(
            evidence
        )
    )

    project_confidence = (
        derive_project_confidence(
            evidence
        )
    )

    if project_confidence == "low":
        decision["project"] = "Unspecified"

    if evidence_confidence == "low":
        alignment = "insufficient_evidence"

    decision["evidence_confidence"] = (
        evidence_confidence
    )

    decision["project_confidence"] = (
        project_confidence
    )

    decision["alignment"] = alignment

    return decision