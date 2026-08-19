import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from rest_framework.decorators import api_view
from rest_framework.response import Response


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


CONTENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "ideas": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "content_angle": {"type": "STRING"},
                    "platform": {"type": "STRING"},
                    "format": {"type": "STRING"},
                    "visual": {
                        "type": "OBJECT",
                        "properties": {
                            "type": {"type": "STRING"},
                            "reason": {"type": "STRING"},
                        },
                        "required": ["type", "reason"],
                    },
                },
                "required": [
                    "title",
                    "content_angle",
                    "platform",
                    "format",
                    "visual",
                ],
            },
        }
    },
    "required": ["ideas"],
}


@api_view(["POST"])
def intelligence(request):

    user_request = request.data.get("request")

    if not user_request:
        return Response(
            {"error": "A 'request' field is required."},
            status=400,
        )

    context = {
        "name": "Alex",
        "role": "Developer building in public",
        "current_project": "Sentinel",
        "project_goal": "Build a personal AI-powered content management system",
        "content_goal": "Build a developer community around working with AI",
        "preferred_platforms": ["LinkedIn", "Instagram"],
    }

    prompt = f"""
You are Sentinel, an intelligent personal content strategist.

USER CONTEXT:
{context}

USER REQUEST:
{user_request}

Using the context above, fulfill the user's request.

Generate exactly 3 strong content opportunities.

The opportunities should be:
- specific to the user's actual journey
- authentic
- non-generic
- suitable for the selected platform
- based only on information actually provided

Do not invent projects, features, achievements, or experiences.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CONTENT_SCHEMA,
        ),
    )

    return Response(response.parsed)