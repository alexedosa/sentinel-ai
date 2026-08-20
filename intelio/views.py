import json

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import UserSignal
from .services.context import build_context
from .services.decision import finalize_decision
from .services.evidence import build_evidence
from .services.intelligence import analyze_evidence
from .services.sync import sync_github


@api_view(["POST"])
def intelligence(request):

    data = request.data
    user_request = None

    if isinstance(data, str):
        try:
            parsed = json.loads(data)

            if isinstance(parsed, dict):
                user_request = parsed.get("request")
            else:
                user_request = data

        except Exception:
            user_request = data

    elif isinstance(data, dict):
        user_request = data.get("request")

    if not user_request:
        return Response(
            {"error": "A 'request' field is required."},
            status=400
        )

    # Store exactly what the user explicitly said.
    user_signal = UserSignal.objects.create(
        request=user_request
    )

    # Sync factual development activity from GitHub.
    sync_result = sync_github()

    # Build Sentinel's current context from stored data.
    context = build_context()

    # Compare the user's statement against available evidence.
    evidence = build_evidence(
        user_request,
        context
    )

    # Let the intelligence layer interpret the evidence.
    decision = analyze_evidence(evidence)

    decision = finalize_decision(
        decision,
        evidence
    )

    return Response({
        "signal_id": user_signal.id,

        "sync": {
            "created": len(sync_result["created"]),
            "skipped": len(sync_result["skipped"]),
        },

        "activity": decision["activity"],
        "subject": decision["subject"],
        "project": decision["project"],
        "status": decision["status"],
        "intent_confidence": decision["intent_confidence"],
        "evidence_confidence": decision["evidence_confidence"],
        "project_confidence": decision["project_confidence"],
        "alignment": decision["alignment"],
        "evidence": decision["evidence"],
        "recommendation": decision["recommendation"],
        "summary": decision["summary"],

        "created_at": user_signal.created_at,
    })