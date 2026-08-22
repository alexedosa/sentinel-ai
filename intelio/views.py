import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Conversation, Message, UserSignal
from .services.context import build_context
from .services.evidence import build_evidence
from .services.intelligence import analyze_evidence
from .services.sync import sync_github
from .services.mentor import generate_mentor_response

# Maximum allowed length for a user message to prevent abuse.
_MAX_MESSAGE_LENGTH = 4000


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

    # Store exactly what the user explicitly said, scoped to the authenticated user.
    user_signal = UserSignal.objects.create(
        user=request.user,
        request=user_request
    )

    # Sync factual development activity from GitHub.
    sync_result = sync_github()

    # Build Sentinel's current context scoped to this user.
    context = build_context(user=request.user)

    # Compare the user's statement against available evidence.
    evidence = build_evidence(
        user_request,
        context
    )

    # Let the intelligence layer interpret the evidence.
    decision = analyze_evidence(evidence)

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
    # Ownership is always derived from the authenticated user; never from request data.
    conversation = Conversation.objects.create(
        user=request.user
    )

    return Response(
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        },
        status=201
    )


@api_view(["GET"])
def get_conversation(request, conversation_id):
    try:
        # Scoped to request.user — returns 404 if ID belongs to another user,
        # which avoids leaking whether a resource exists at all.
        conversation = (
            Conversation.objects
            .prefetch_related("messages")
            .get(id=conversation_id, user=request.user)
        )
    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversation not found."},
            status=404
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
    content = request.data.get("message")

    if not content or not str(content).strip():
        return Response(
            {"error": "A non-empty 'message' field is required."},
            status=400
        )

    if len(str(content)) > _MAX_MESSAGE_LENGTH:
        return Response(
            {"error": f"Message exceeds maximum length of {_MAX_MESSAGE_LENGTH} characters."},
            status=400
        )

    try:
        # Scoped to request.user — a user cannot append messages to another user's conversation.
        conversation = Conversation.objects.get(
            id=conversation_id,
            user=request.user
        )
    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversation not found."},
            status=404
        )

    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_USER,
        content=str(content).strip()
    )

    assistant_content = generate_mentor_response(
        conversation,
        str(content).strip(),
        user=request.user
    )

    assistant_message = Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_ASSISTANT,
        content=assistant_content
    )

    conversation.save(update_fields=["updated_at"])

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
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    email = request.data.get("email", "")

    # Validate username.
    if not username or not str(username).strip():
        return Response(
            {"error": "A non-empty 'username' field is required."},
            status=400
        )

    username = str(username).strip()

    if len(username) > 150:
        return Response(
            {"error": "Username must be 150 characters or fewer."},
            status=400
        )

    # Validate password.
    if not password or not str(password).strip():
        return Response(
            {"error": "A non-empty 'password' field is required."},
            status=400
        )

    # Apply Django's built-in password validators.
    try:
        validate_password(password)
    except ValidationError as exc:
        return Response(
            {"error": list(exc.messages)},
            status=400
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "A user with that username already exists."},
            status=400
        )

    user = User.objects.create_user(
        username=username,
        email=str(email).strip() if email else "",
        password=password
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "token": token.key,
        },
        status=201
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"error": "Both 'username' and 'password' are required."},
            status=400
        )

    user = authenticate(username=username, password=password)

    if user is None:
        # Return the same message regardless of whether the username exists
        # to avoid leaking account existence.
        return Response(
            {"error": "Invalid credentials."},
            status=401
        )

    token, _ = Token.objects.get_or_create(user=user)

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
    # Safely delete the token if it exists; avoid raising RelatedObjectDoesNotExist
    # if the token was already revoked by a parallel request.
    try:
        request.user.auth_token.delete()
    except Token.DoesNotExist:
        pass

    return Response({"detail": "Successfully logged out."})