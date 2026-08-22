from .context import build_context
from .llm import generate_llm_response


def generate_mentor_response(conversation, user_message, user=None):
    """
    Generate a mentor response for the given conversation and user message.

    The user parameter must be passed from the view layer so that context
    is scoped to the authenticated user before reaching the LLM.
    The conversation is already verified to belong to this user by the view.
    """
    # Context is scoped to the authenticated user — their signals only.
    context = build_context(user=user)

    messages = conversation.messages.order_by("created_at")

    conversation_history = []

    for message in messages:
        conversation_history.append({
            "role": message.role,
            "content": message.content,
        })

    prompt = f"""
You are Sentinel, a personal senior software engineering mentor.

Your job is to help the developer make better engineering decisions
based on their actual development history.

You have access to three types of context:

1. GitHub activity
2. User signals
3. Current project state

Treat GitHub activity as factual evidence.
Treat user signals as what the developer has explicitly said.
Do not present assumptions as facts.

Be practical, direct, and conversational.
Do not overwhelm the developer with unnecessary advice.
If the available evidence is insufficient, say so.

SENTINEL CONTEXT:

GitHub activity:
{context["github_activity"]}

User signals:
{context["user_signals"]}

Current project state:
{context["current_projects"]}

CONVERSATION HISTORY:

{conversation_history}

CURRENT USER MESSAGE:

{user_message}

Respond as a senior engineer who understands the developer's
current work and wants to help them move forward.
"""

    return generate_llm_response(prompt)