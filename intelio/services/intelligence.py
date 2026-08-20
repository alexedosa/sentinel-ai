import json

from .llm import generate_llm_response


INTELLIGENCE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "activity": {
            "type": "STRING"
        },
        "subject": {
            "type": "STRING"
        },
        "project": {
            "type": "STRING"
        },
        "status": {
            "type": "STRING"
        },
        "intent_confidence": {
            "type": "STRING"
        },
        "evidence_confidence": {
            "type": "STRING"
        },
        "project_confidence": {
            "type": "STRING"
        },
        "alignment": {
            "type": "STRING"
        },
        "evidence": {
            "type": "STRING"
        },
        "recommendation": {
            "type": "STRING"
        },
        "summary": {
            "type": "STRING"
        }
    },
    "required": [
        "activity",
        "subject",
        "project",
        "status",
        "intent_confidence",
        "evidence_confidence",
        "project_confidence",
        "alignment",
        "evidence",
        "recommendation",
        "summary"
    ]
}


def analyze_evidence(evidence):

    prompt = f"""
You are Sentinel, an intelligent personal development
intelligence system.

Your job is to reason about the user's current development
intent using ONLY the evidence provided below.

EVIDENCE:

USER REQUEST:
{evidence.get("user_request")}

GITHUB EVIDENCE:
{evidence.get("github_evidence")}

USER HISTORY:
{evidence.get("user_history")}

CURRENT PROJECT STATE:
{evidence.get("project_state")}

EVIDENCE LEVEL:
{evidence.get("evidence_level")}


SOURCE DEFINITIONS:

USER REQUEST:
What the user explicitly says they intend to do now.

GITHUB EVIDENCE:
External development activity retrieved from GitHub.
This is factual evidence of activity that occurred in the repository,
but it is NOT absolute proof of the user's current intention.

USER HISTORY:
Previous statements made by the user.
These are context, not factual proof of development activity.

CURRENT PROJECT STATE:
A derived representation of the project's known state.
It is not a raw source of truth.


RULES:

1. The user's explicit request is the primary signal for current intent.

2. GitHub evidence is supporting evidence of actual repository activity.

3. Never invent GitHub activity, project state, previous statements,
   or development work.

4. Never treat a user's statement as proof that development occurred.

5. Never treat a GitHub commit as absolute proof of what the user
   is currently doing.

6. Do not assume unrelated activities are connected.

7. Use "aligned" ONLY when the user's request is supported by meaningful
   recent evidence from the same project/activity.

8. Use "changed_direction" when meaningful previous evidence exists and
   the user explicitly states they are moving away from that previous focus.

9. Use "potential_conflict" when meaningful recent evidence points toward
   a different activity for the same project and the user has not
   explicitly explained the change.

10. Use "insufficient_evidence" when the user's intent is clear but
    available evidence is insufficient to establish alignment or conflict.

11. A completely new project must NOT automatically be classified
    as "changed_direction".

12. If the user introduces a new activity or project without meaningful
    supporting or conflicting evidence, use "insufficient_evidence".

13. The evidence field must briefly explain WHY the chosen alignment
    was selected.

14. The recommendation must be practical and grounded in the evidence.

15. Do not fabricate technical progress that is not present in GitHub
    evidence or user-provided information.

16. Return ONLY valid JSON.

17. Distinguish user intent from factual development evidence.


18. intent_confidence describes how clearly the user communicated
    what they intend to do.


19. evidence_confidence describes how strongly the available GitHub
    evidence supports that the activity actually occurred.


20. project_confidence describes how strongly the evidence connects
    the activity to a specific project.


21. Never increase evidence_confidence merely because the user said
    they are doing something.


22. Never increase project_confidence merely because the user has
    recently worked on a particular project.


23. Use only:
    - "high"
    - "medium"
    - "low"
    for confidence fields.


24. If the project cannot be established from evidence, use
    "Unspecified" for project and "low" for project_confidence.


25. If the user clearly states an intention but GitHub provides no
    meaningful evidence of the activity, intent_confidence may be
    "high" while evidence_confidence remains "low".


26. The JSON must contain exactly these fields:

{json.dumps(INTELLIGENCE_SCHEMA, indent=2)}
"""

    response = generate_llm_response(prompt)

    try:
        result = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError(
            "LLM returned invalid JSON."
        ) from error

    required_fields = set(INTELLIGENCE_SCHEMA["required"])

    missing_fields = required_fields - result.keys()

    if missing_fields:
        raise ValueError(
            f"LLM response is missing fields: "
            f"{', '.join(sorted(missing_fields))}"
        )

    return result