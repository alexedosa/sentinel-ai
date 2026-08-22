from django.urls import path
from .views import (
    create_conversation,
    create_message,
    get_conversation,
    intelligence,
    login,
    logout,
    register,
)

urlpatterns = [
    path("intelligence/", intelligence),

    path(
        "mentor/conversations/",
        create_conversation
    ),

    path(
        "mentor/conversations/<int:conversation_id>/messages/",
        create_message
    ),

    path(
        "mentor/conversations/<int:conversation_id>/",
        get_conversation
    ),

    path("auth/register/", register),
    path("auth/login/", login),
    path("auth/logout/", logout),
]