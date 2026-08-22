import json

from .decision import finalize_decision
from .llm import generate_llm_response
from .project import resolve_project


INTELLIGENCE_FIELDS = {
    "activity",
    "subject",
    "status",
    "alignment",
    "evidence",
    "recommendation",
    "summary",
}


VALID_ALIGNMENTS = {
    "aligned",
    "changed_direction",
    "potential_conflict",
    "insufficient_evidence",
}


def _build_prompt(evidence, project_result):
    return f"""
You are Sentinel, a personal development intelligence system.

Interpret the user's current intent using ONLY the evidence provided.

Do not invent development activity.
Do not treat a user statement as proof that work occurred.
Do not invent projects, commits, history, or technical progress.

USER REQUEST:
{evidence.get("user_request")}

RELEVANT GITHUB EVIDENCE:
{evidence.get("github_evidence", [])}

RELEVANT USER HISTORY:
{evidence.get("user_history", [])}

RELEVANT PROJECT STATE:
{evidence.get("project_state", [])}

EVIDENCE LEVEL:
{evidence.get("evidence_level")}

DETERMINISTIC PROJECT RESOLUTION:
{project_result}

Your task is to interpret the evidence.

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "activity": "string",
    "subject": "string",
    "status": "string",
    "alignment": "aligned | changed_direction | potential_conflict | insufficient_evidence",
    "evidence": "brief explanation of why this alignment was selected",
    "recommendation": "practical recommendation grounded in the evidence",
    "summary": "concise summary of the situation"
}}

Rules:

1. The user's request describes current intent.

2. GitHub evidence describes observable repository activity.

3. User history provides context but is not proof of development activity.

4. Project state provides contextual information but is not raw proof.

5. Use "aligned" only when meaningful evidence supports the same activity.

6. Use "changed_direction" only when previous meaningful evidence
   indicates a different focus and the user clearly indicates a change.

7. Use "potential_conflict" only when meaningful evidence points toward
   a different activity and there is no clear explanation for the difference.

8. Use "insufficient_evidence" when intent is clear but evidence is
   insufficient to establish alignment or conflict.

9. A new project or activity is not automatically a changed direction.

10. Never claim that code was written, completed, deployed, tested,
    fixed, or shipped unless the evidence actually supports that claim.

11. Keep the recommendation practical.

12. Keep the summary concise.

13. The alignment value MUST be one of:
    "aligned",
    "changed_direction",
    "potential_conflict",
    "insufficient_evidence".

27. Deterministic project resolution is stronger project evidence than
    inferred project associations. Use it when available, but do not
    override an explicit user statement with a weaker inference.
"""


def _parse_response(response):
    try:
        result = json.loads(response)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(
            "LLM returned invalid JSON."
        ) from error

    missing_fields = (
        INTELLIGENCE_FIELDS - result.keys()
    )

    if missing_fields:
        raise ValueError(
            "LLM response is missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    alignment = result.get("alignment")

    if alignment not in VALID_ALIGNMENTS:
        raise ValueError(
            f"LLM returned invalid alignment: {alignment}"
        )

    return result


def analyze_evidence(evidence):
    """
    Interpret evidence through the LLM and then apply deterministic
    project and confidence rules.

    The LLM provides interpretation.
    Deterministic services remain authoritative for project resolution,
    confidence, and final alignment safety.
    """

    project_result = resolve_project(
        evidence.get("user_request", ""),
        evidence,
    )

    prompt = _build_prompt(
        evidence,
        project_result,
    )

    response = generate_llm_response(
        prompt
    )

    decision = _parse_response(
        response
    )

    decision["project"] = (
        project_result["project"]
        if project_result["project"] is not None
        else "Unspecified"
    )

    decision["intent_confidence"] = (
        "high"
        if evidence.get("user_request")
        else "low"
    )

    return finalize_decision(
        decision,
        evidence,
    )
