import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Activity, ProjectState
from .services.context import build_context

load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


ACTIVITY_SCHEMA = {
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
        "summary": {
            "type": "STRING"
        }
    },
    "required": [
        "activity",
        "subject",
        "project",
        "status",
        "summary"
    ]
}



@api_view(["POST"])
def intelligence(request):
    
    user_request = request.data.get("request")

    if not user_request:
        return Response(
            {"error": "A 'request' field is required."},
            status=400
        )

    context = build_context()

    prompt = f"""
You are Sentinel, an intelligent personal development intelligence system.


USER:
Muzan


CURRENT PROJECT:
Sentinel


CONTEXT:
{context}


CURRENT USER REQUEST:
{user_request}


Understand the user's current activity using the available context.


Rules:
- Do not invent information.
- Use memory only when relevant.
- Detect contradictions or changes in direction.
- Determine the user's current activity.
- Return structured information.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ACTIVITY_SCHEMA,
        ),
    )

    activity = response.parsed

    saved_activity = Activity.objects.create(
        project=activity["project"],
        activity_type=activity["activity"],
        subject=activity["subject"],
        status=activity["status"],
        summary=activity["summary"],
    )

    ProjectState.objects.update_or_create(
        project=activity["project"],
        defaults={
            "current_focus": activity["subject"],
            "status": activity["status"],
            "summary": activity["summary"],
        },
    )

    return Response({
        "id": saved_activity.id,
        "activity": saved_activity.activity_type,
        "subject": saved_activity.subject,
        "project": saved_activity.project,
        "status": saved_activity.status,
        "summary": saved_activity.summary,
        "created_at": saved_activity.created_at,
    })