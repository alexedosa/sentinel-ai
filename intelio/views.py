import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Conversation, Message
from .services.context import build_context
from .services.evidence import build_evidence
from .services.intelligence import analyze_evidence
from .services.project import resolve_project
from .services.decision import finalize_decision
from .services.mentor import generate_mentor_response
from .services.signals import save_user_signal
from .services.sync import sync_github


MAX_MESSAGE_LENGTH = 4000


def _extract_request(data):
    """
    Extract the user's intelligence request from supported payload formats.
    """

    if isinstance(data, dict):
        return data.get("request")

    if isinstance(data, str):
        try:
            parsed = json.loads(data)

            if isinstance(parsed, dict):
                return parsed.get("request")

        except (TypeError, ValueError):
            pass

        return data

    return None


def _validate_message(content):
    """
    Validate and normalize conversation message content.
    """

    if not content or not str(content).strip():
        return None, "A non-empty 'message' field is required."

    content = str(content).strip()

    if len(content) > MAX_MESSAGE_LENGTH:
        return (
            None,
            f"Message exceeds maximum length of "
            f"{MAX_MESSAGE_LENGTH} characters."
        )

    return content, None


def _get_user_conversation(request, conversation_id):
    """
    Retrieve a conversation belonging to the authenticated user.
    """

    try:
        return (
            Conversation.objects
            .prefetch_related("messages")
            .get(
                id=conversation_id,
                user=request.user,
            )
        )

    except Conversation.DoesNotExist:
        return None


@api_view(["POST"])
def intelligence(request):
    """
    Run Sentinel's intelligence pipeline for the authenticated user.
    """

    user_request = _extract_request(request.data)

    if not user_request:
        return Response(
            {"error": "A 'request' field is required."},
            status=400,
        )

    user_signal = save_user_signal(
        user=request.user,
        signal_text=user_request,
    )

    sync_result = sync_github()

    context = build_context(
        user=request.user,
    )

    evidence = build_evidence(
        user_request,
        context,
    )

    project_resolution = resolve_project(
        user_request,
        context,
    )

    evidence["project_resolution"] = project_resolution

    decision = analyze_evidence(
        evidence
    )

    decision = finalize_decision(
        decision,
        evidence,
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


@api_view(["POST"])
def create_conversation(request):
    """
    Create an empty conversation owned by the authenticated user.
    """

    conversation = Conversation.objects.create(
        user=request.user,
    )

    return Response(
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        },
        status=201,
    )


@api_view(["GET"])
def get_conversation(request, conversation_id):
    """
    Return a conversation only if it belongs to the authenticated user.
    """

    conversation = _get_user_conversation(
        request,
        conversation_id,
    )

    if conversation is None:
        return Response(
            {"error": "Conversation not found."},
            status=404,
        )

    messages = [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in conversation.messages.all()
    ]

    return Response({
        "id": conversation.id,
        "title": conversation.title,
        "messages": messages,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    })


@api_view(["POST"])
def create_message(request, conversation_id):
    """
    Add a user message and generate Sentinel's response.
    """

    content, error = _validate_message(
        request.data.get("message")
    )

    if error:
        return Response(
            {"error": error},
            status=400,
        )

    conversation = _get_user_conversation(
        request,
        conversation_id,
    )

    if conversation is None:
        return Response(
            {"error": "Conversation not found."},
            status=404,
        )

    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_USER,
        content=content,
    )

    assistant_content = generate_mentor_response(
        conversation,
        content,
        user=request.user,
    )

    assistant_message = Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_ASSISTANT,
        content=assistant_content,
    )

    conversation.save(
        update_fields=["updated_at"]
    )

    return Response({
        "user_message": {
            "id": user_message.id,
            "role": user_message.role,
            "content": user_message.content,
            "created_at": user_message.created_at,
        },
        "assistant_message": {
            "id": assistant_message.id,
            "role": assistant_message.role,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at,
        },
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and issue an authentication token.
    """

    username = str(
        request.data.get("username", "")
    ).strip()

    password = request.data.get(
        "password",
        "",
    )

    email = str(
        request.data.get("email", "")
    ).strip()

    if not username:
        return Response(
            {"error": "A non-empty 'username' field is required."},
            status=400,
        )

    if len(username) > 150:
        return Response(
            {"error": "Username must be 150 characters or fewer."},
            status=400,
        )

    if not password or not str(password).strip():
        return Response(
            {"error": "A non-empty 'password' field is required."},
            status=400,
        )

    try:
        validate_password(
            password,
        )

    except ValidationError as exc:
        return Response(
            {"error": list(exc.messages)},
            status=400,
        )

    if User.objects.filter(
        username=username
    ).exists():
        return Response(
            {"error": "A user with that username already exists."},
            status=400,
        )

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    token, _ = Token.objects.get_or_create(
        user=user,
    )

    return Response(
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "token": token.key,
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate a user and issue an authentication token.
    """

    username = str(
        request.data.get("username", "")
    ).strip()

    password = request.data.get(
        "password",
        "",
    )

    if not username or not password:
        return Response(
            {
                "error": (
                    "Both 'username' and 'password' "
                    "are required."
                )
            },
            status=400,
        )

    user = authenticate(
        username=username,
        password=password,
    )

    if user is None:
        return Response(
            {"error": "Invalid credentials."},
            status=401,
        )

    token, _ = Token.objects.get_or_create(
        user=user,
    )

    return Response({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
        "token": token.key,
    })


@api_view(["POST"])
def logout(request):
    """
    Revoke the authenticated user's token.
    """

    try:
        request.user.auth_token.delete()

    except Token.DoesNotExist:
        pass

    return Response({
        "detail": "Successfully logged out."
    })
