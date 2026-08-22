from intelio.services.code import build_code_evidence
from intelio.services.context import build_context
from intelio.services.evidence import build_evidence
from intelio.services.intelligence import analyze_evidence
from intelio.services.signals import save_user_signal
from intelio.services.sync import sync_github


def process_intelligence_request(*, user, user_request):
    """
    Execute the complete Sentinel intelligence pipeline.

    The pipeline is responsible for orchestration only.
    Individual services remain responsible for their own domain logic.
    """

    # 1. Persist the user's explicit intention.
    user_signal = save_user_signal(
        user=user,
        request=user_request,
    )

    # 2. Synchronize factual development activity.
    sync_result = sync_github()

    # 3. Retrieve recent commits for code-level evidence.
    # Temporary repository configuration until GitHub connections
    # become user-configurable.
    from intelio.services.github import get_recent_commits

    commits = get_recent_commits(
        "alexedosa",
        "sentinel-ai",
    )

    code_evidence = build_code_evidence(
        "alexedosa",
        "sentinel-ai",
        commits,
    )

    # 4. Build the authenticated user's current context.
    context = build_context(
        user=user,
        code_evidence=code_evidence,
    )

    # 5. Build normalized evidence.
    evidence = build_evidence(
        user_request,
        context,
    )

    # 6. Let the intelligence layer interpret the evidence.
    decision = analyze_evidence(
        evidence
    )

    return {
        "signal_id": user_signal.id,
        "sync": {
            "created": len(sync_result["created"]),
            "skipped": len(sync_result["skipped"]),
        },
        "decision": decision,
        "created_at": user_signal.created_at,
    }
